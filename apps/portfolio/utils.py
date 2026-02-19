"""
Portfolio app utilities for AI features.
"""
import json
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class _GenaiModelWrapper:
    """Thin wrapper so callers can use model.generate_content(contents) and response.text."""

    def __init__(self, client, model_name: str):
        self._client = client
        self._model_name = model_name

    def generate_content(self, contents):
        # New SDK expects inline_data as {"inline_data": {"data": ..., "mimeType": ...}}
        if isinstance(contents, list):
            normalized = []
            for part in contents:
                if isinstance(part, dict) and "mime_type" in part and "data" in part:
                    normalized.append({
                        "inline_data": {
                            "data": part["data"],
                            "mimeType": part["mime_type"],
                        }
                    })
                else:
                    normalized.append(part)
            contents = normalized
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
        )
        return response


def get_gemini_model():
    """Get configured Gemini model (wrapper with generate_content returning .text)."""
    try:
        # New google.genai package: use Client(api_key=...), no configure
        try:
            from google.genai import Client
            if settings.GEMINI_API_KEY:
                client = Client(api_key=settings.GEMINI_API_KEY)
                return _GenaiModelWrapper(client, "gemini-1.5-flash")
        except ImportError:
            pass
        # Fall back to deprecated google.generativeai
        import google.generativeai as genai
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        logger.warning(f"Gemini not configured: {e}")
    return None


def ai_tag_portfolio_item(image_url: str) -> list:
    """
    Sends a portfolio image to Gemini Vision.
    Returns descriptive tags that improve search discoverability.

    Example tags: ["outdoor", "wedding", "candid", "golden hour", "portrait"]
    """
    cache_key = f"ai_tags_{hash(image_url)}"
    cached_tags = cache.get(cache_key)
    if cached_tags:
        return cached_tags

    model = get_gemini_model()
    if not model:
        return []

    try:
        prompt = """
        Analyze this portfolio image from a local freelancer.
        Return ONLY a JSON list of 5-10 descriptive tags for search purposes.
        Tags should describe: style, subject, setting, technique, mood.
        Return nothing else.
        """

        # Fetch image and create parts
        import urllib.request
        from PIL import Image
        import io

        with urllib.request.urlopen(image_url) as response:
            image_data = response.read()

        image_part = {
            "mime_type": "image/jpeg",
            "data": image_data
        }

        response = model.generate_content([prompt, image_part])
        tags = json.loads(response.text.strip())

        # Cache for 7 days
        cache.set(cache_key, tags, 60 * 60 * 24 * 7)
        return tags

    except Exception as e:
        logger.error(f"Error generating AI tags: {e}")
        return []


def get_ai_profile_suggestions(freelancer_profile) -> list:
    """Returns 3 actionable suggestions to improve a freelancer's profile."""
    model = get_gemini_model()
    if not model:
        return []

    try:
        portfolio = getattr(freelancer_profile, 'portfolio', None)

        profile_data = {
            "has_bio": bool(freelancer_profile.bio),
            "bio_length": len(freelancer_profile.bio) if freelancer_profile.bio else 0,
            "portfolio_items": portfolio.items.count() if portfolio else 0,
            "has_photo": bool(freelancer_profile.profile_photo),
            "skills_count": freelancer_profile.skills.count() if portfolio else 0,
            "avg_rating": freelancer_profile.avg_rating,
            "completeness": portfolio.completeness if portfolio else 0,
        }

        prompt = f"""
        A local freelancer has this profile status: {json.dumps(profile_data)}

        Give 3 short, specific, actionable suggestions to improve their discoverability.
        Return as a JSON list of strings. No explanation, no markdown.
        """

        response = model.generate_content(prompt)
        return json.loads(response.text.strip())

    except Exception as e:
        logger.error(f"Error generating profile suggestions: {e}")
        return []
