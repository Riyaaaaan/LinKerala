"""
AI Engine for search functionality using Google Gemini.
"""
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class _GenaiModelWrapper:
    """Thin wrapper so callers can use model.generate_content(contents) and response.text."""

    def __init__(self, client, model_name: str):
        self._client = client
        self._model_name = model_name

    def generate_content(self, contents):
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


def parse_search_query(raw_query: str) -> dict:
    """
    Extracts structured intent from free-text user queries.

    Example input:  "I need a wedding photographer in Austin under $300"
    Example output: {
        "service_type": "photography",
        "keywords": ["wedding", "photographer"],
        "location": "Austin",
        "max_budget": 300,
        "urgency": null
    }
    """
    model = get_gemini_model()
    if not model:
        # Fallback: simple keyword extraction
        logger.info("Using fallback parser (no Gemini API)")
        return fallback_parse_query(raw_query)

    try:
        prompt = f"""
        You are a search intent extractor for a local freelancer platform.
        Extract structured data from this user query: "{raw_query}"

        Return ONLY valid JSON with these fields:
        - service_type: string (e.g. photography, tutoring, videography, repair)
        - keywords: list of strings
        - location: string or null
        - min_budget: integer or null
        - max_budget: integer or null
        - urgency: string or null (e.g. "today", "this week")

        Return nothing else — no explanation, no markdown.
        """

        logger.info(f"Sending query to Gemini AI: {raw_query}")
        response = model.generate_content(prompt)
        logger.info(f"Gemini AI raw response: {response.text}")

        result = json.loads(response.text.strip())
        logger.info(f"Gemini AI parsed result: {result}")

        # Ensure all keys exist
        return {
            'service_type': result.get('service_type'),
            'keywords': result.get('keywords', []),
            'location': result.get('location'),
            'min_budget': result.get('min_budget'),
            'max_budget': result.get('max_budget'),
            'urgency': result.get('urgency'),
        }

    except Exception as e:
        logger.error(f"Error parsing search query: {e}")
        return fallback_parse_query(raw_query)


def fallback_parse_query(raw_query: str) -> dict:
    """Fallback simple query parser when Gemini is not available."""
    import re

    query_lower = raw_query.lower()

    # Extract budget
    budget_match = re.search(r'under\s*\$?(\d+)', query_lower)
    max_budget = int(budget_match.group(1)) if budget_match else None

    budget_match_min = re.search(r'from\s*\$?(\d+)', query_lower)
    min_budget = int(budget_match_min.group(1)) if budget_match_min else None

    # Common service types
    service_types = {
        'photography': ['photo', 'photographer', 'photography'],
        'videography': ['video', 'videographer', 'videography'],
        'tutoring': ['tutor', 'tutoring', 'teach'],
        'design': ['design', 'designer'],
        'repair': ['repair', 'fix', 'technician'],
    }

    service_type = None
    for stype, keywords in service_types.items():
        if any(kw in query_lower for kw in keywords):
            service_type = stype
            break

    # Simple location extraction (common cities)
    cities = ['new york', 'los angeles', 'chicago', 'houston', 'phoenix',
              'austin', 'seattle', 'boston', 'denver', 'portland']

    location = None
    for city in cities:
        if city in query_lower:
            location = city.title()
            break

    # Extract keywords (words longer than 3 chars that aren't common)
    stop_words = {'the', 'and', 'for', 'with', 'need', 'looking', 'want',
                  'find', 'have', 'near', 'in', 'a', 'an', 'under', 'from'}

    words = re.findall(r'\b\w+\b', query_lower)
    keywords = [w for w in words if len(w) > 3 and w not in stop_words]

    return {
        'service_type': service_type,
        'keywords': keywords,
        'location': location,
        'min_budget': min_budget,
        'max_budget': max_budget,
        'urgency': None,
    }


def get_recommendations(freelancer_profile, limit: int = 5) -> list:
    """
    Get personalized AI recommendations for a client.
    Returns list of recommended freelancer IDs.
    Uses Gemini to analyze client's preferences and match with freelancers.
    """
    from apps.accounts.models import FreelancerProfile, ClientProfile

    # Get all available freelancers as candidates
    candidates = list(FreelancerProfile.objects.filter(
        availability='available'
    ).select_related('user'))

    if not candidates:
        return []

    model = get_gemini_model()

    # If no Gemini available, fall back to activity-based sorting
    if not model:
        sorted_freelancers = sorted(
            candidates,
            key=lambda f: f.activity_score,
            reverse=True
        )
        return [f.id for f in sorted_freelancers[:limit]]

    try:
        # Build context about the client
        client_context = ""
        if isinstance(freelancer_profile, ClientProfile):
            if freelancer_profile.industry:
                client_context += f"Industry: {freelancer_profile.industry}. "
            if freelancer_profile.bio:
                client_context += f"Interests: {freelancer_profile.bio}. "

        # Build freelancer profiles for AI matching
        freelancer_profiles = []
        for f in candidates:
            profile_text = (
                f"Freelancer {f.user.username}: {f.title or 'No title'}. "
                f"Skills: {f.skills or 'Not specified'}. "
                f"Experience: {f.years_experience or 0} years. "
                f"Rating: {f.avg_rating:.1f}/5. "
                f"Price range: ${f.price_min or 0}-${f.price_max or 0}. "
                f"Location: {f.city or 'Remote'}. "
                f"Availability: {f.availability}."
            )
            freelancer_profiles.append(f"ID:{f.id} - {profile_text}")

        prompt = f"""
You are a recommendation engine for a freelancer platform.
Given a client's background: "{client_context}"
And the following available freelancers:
{chr(10).join(freelancer_profiles)}

Select the top {limit} freelancer IDs that best match the client's needs.
Consider skills match, price range fit, location, availability, and ratings.
Return ONLY a JSON list of freelancer IDs, nothing else.
Example: [1, 5, 8, 12, 3]
"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Parse the response to extract IDs
        import re
        id_matches = re.findall(r'\[([\d,\s]+)\]', result_text)
        if id_matches:
            ids = [int(x.strip()) for x in id_matches[0].split(',') if x.strip().isdigit()]
            # Verify IDs exist
            valid_ids = [i for i in ids if i in [f.id for f in candidates]]
            if valid_ids:
                return valid_ids[:limit]

        # Fallback if parsing fails
        sorted_freelancers = sorted(
            candidates,
            key=lambda f: f.activity_score,
            reverse=True
        )
        return [f.id for f in sorted_freelancers[:limit]]

    except Exception as e:
        logger.error(f"Error getting AI recommendations: {e}")
        # Fallback to activity-based sorting
        sorted_freelancers = sorted(
            candidates,
            key=lambda f: f.activity_score,
            reverse=True
        )
        return [f.id for f in sorted_freelancers[:limit]]


def get_work_suggestions(freelancer_profile, limit: int = 5) -> list:
    """
    Get AI-powered work suggestions for a freelancer.
    Returns list of recommended work IDs based on freelancer's tagline, bio, and ai_tags.
    ONLY returns works that actually match the freelancer's profile - never returns all works.
    """
    from apps.accounts.models import Work

    # Get all open works as candidates
    candidates = list(Work.objects.filter(status='open'))

    if not candidates:
        return []

    model = get_gemini_model()

    # If no Gemini available, use keyword-based matching
    if not model:
        return keyword_based_matching(freelancer_profile, candidates, limit)

    try:
        # Build comprehensive profile context from available fields
        # FreelancerProfile has: tagline, bio, ai_tags, display_name, city, hourly_rate, etc.
        freelancer_tagline = getattr(freelancer_profile, 'tagline', '') or ''
        freelancer_bio = getattr(freelancer_profile, 'bio', '') or ''
        freelancer_ai_tags = getattr(freelancer_profile, 'ai_tags', []) or []
        freelancer_display_name = getattr(freelancer_profile, 'display_name', '') or ''
        freelancer_city = getattr(freelancer_profile, 'city', '') or ''
        freelancer_hourly_rate = getattr(freelancer_profile, 'hourly_rate', None)
        freelancer_price_min = getattr(freelancer_profile, 'price_min', None)
        freelancer_price_max = getattr(freelancer_profile, 'price_max', None)
        freelancer_years_exp = getattr(freelancer_profile, 'years_experience', 0) or 0

        # Create keyword set from tagline, bio, ai_tags, and display_name
        profile_keywords = set()
        if freelancer_tagline:
            profile_keywords.update(freelancer_tagline.lower().split())
        if freelancer_bio:
            # Extract meaningful words from bio (filter short words)
            bio_words = [w for w in freelancer_bio.lower().split() if len(w) > 3]
            profile_keywords.update(bio_words)
        if freelancer_ai_tags:
            if isinstance(freelancer_ai_tags, list):
                profile_keywords.update([str(t).lower() for t in freelancer_ai_tags])
            else:
                profile_keywords.update(str(freelancer_ai_tags).lower().split())
        if freelancer_display_name:
            profile_keywords.update(freelancer_display_name.lower().split())

        # If no profile keywords, return empty - don't show unrelated works
        if not profile_keywords:
            logger.info("Freelancer has no tagline/bio/ai_tags - returning empty suggestions")
            return []

        # Score candidates by keyword relevance
        scored_candidates = []
        for w in candidates:
            work_text = f"{w.title} {w.description}".lower()
            # Also include work skills
            if w.skills:
                if isinstance(w.skills, list):
                    work_text += ' ' + ' '.join(w.skills).lower()
            # Also include category
            if w.category:
                work_text += ' ' + w.category.lower()

            # Calculate match score - count unique matching keywords
            matching_keywords = [kw for kw in profile_keywords if kw in work_text and len(kw) > 2]
            match_count = len(matching_keywords)

            if match_count > 0:
                scored_candidates.append((w, match_count, matching_keywords))

        # Sort by relevance score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Get top matches
        top_matches = scored_candidates[:limit] if scored_candidates else []

        # If no matches found, return empty - don't fallback to all works
        if not top_matches:
            logger.info("No keyword matches found - returning empty suggestions")
            return []

        # Use only matched works for AI refinement
        matched_works = [w for w, score, kw in top_matches]

        # Build context about the freelancer using CORRECT field names
        price_range = f"${freelancer_price_min or 0}-${freelancer_price_max or 0}" if freelancer_price_min or freelancer_price_max else "Flexible"
        hourly = f"${freelancer_hourly_rate}/hr" if freelancer_hourly_rate else "Negotiable"

        freelancer_context = (
            f"Freelancer Name: {freelancer_display_name}. "
            f"Tagline: {freelancer_tagline or 'Not specified'}. "
            f"Bio/Description: {freelancer_bio or 'Not specified'}. "
            f"AI Tags/Skills: {', '.join(freelancer_ai_tags) if freelancer_ai_tags else 'Not specified'}. "
            f"Experience: {freelancer_years_exp} years. "
            f"Location: {freelancer_city or 'Remote'}. "
            f"Hourly Rate: {hourly}. "
            f"Price Range: {price_range}."
        )

        # Build work profiles for AI matching
        work_profiles = []
        for w in matched_works:
            skills_str = ', '.join(w.skills) if w.skills else 'Not specified'
            work_text = (
                f"Work ID {w.id}: {w.title}. "
                f"Description: {w.description[:300]} "
                f"Category: {w.category or 'Not specified'}. "
                f"Required skills: {skills_str}. "
                f"Pay: ${w.pay_per_hour}/hr."
            )
            work_profiles.append(work_text)

        # Get keyword list for the prompt
        keyword_list = list(profile_keywords)[:15]

        prompt = f"""
You are a STRICT job matching engine. Your job is to filter jobs to only those that HIGHLY MATCH the freelancer.

Freelancer Profile:
"{freelancer_context}"

Matching Keywords from Profile: {keyword_list}

Jobs to Filter (already pre-scored by keyword matching):
{chr(10).join(work_profiles)}

STRICT INSTRUCTIONS:
- ONLY include jobs where there is CLEAR relevance between the freelancer's profile and the job
- A developer should ONLY see development/programming jobs
- A videographer should ONLY see video/filmmaking jobs
- Compare: Tagline, Bio, AI Tags with Job Title, Description, Category, Skills
- If a job is not directly related, EXCLUDE it
- Return ONLY IDs of HIGHLY RELEVANT jobs
- If NONE are relevant, return empty list: []

Return ONLY a JSON list of work IDs, nothing else.
Example: [1, 5] or []
"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Parse the response to extract IDs
        import re
        id_matches = re.findall(r'\[([\d,\s]*)\]', result_text)
        if id_matches:
            ids = [int(x.strip()) for x in id_matches[0].split(',') if x.strip().isdigit()]
            # Verify IDs exist in matched works
            valid_ids = [i for i in ids if i in [w.id for w in matched_works]]
            if valid_ids:
                return valid_ids[:limit]

        # If AI filtering fails, return the pre-filtered keyword matches
        return [w.id for w in matched_works[:limit]]

    except Exception as e:
        logger.error(f"Error getting work suggestions: {e}")
        # Don't fallback to all works - use keyword matching or return empty
        return keyword_based_matching(freelancer_profile, candidates, limit)


def get_work_suggestions_ai_message(freelancer_profile, work_summaries: list) -> str:
    """
    Generate a short AI message explaining why these works are recommended for the freelancer.
    work_summaries: list of strings like "Title (Category)" or just titles.
    """
    if not work_summaries:
        return ""
    model = get_gemini_model()
    if not model:
        return "These jobs match your profile and skills."
    try:
        tagline = getattr(freelancer_profile, 'tagline', '') or ''
        bio = (getattr(freelancer_profile, 'bio', '') or '')[:200]
        ai_tags = getattr(freelancer_profile, 'ai_tags', []) or []
        tags_str = ", ".join(ai_tags[:8]) if isinstance(ai_tags, list) else str(ai_tags)[:100]
        works_list = "\n".join(f"- {s}" for s in work_summaries[:10])

        prompt = f"""You are a helpful assistant for a freelancer platform. In 1-2 short sentences, tell the freelancer why these jobs are recommended for them. Be warm and specific (mention their profile/skills). No bullet points, no markdown.

Freelancer profile: Tagline: "{tagline}". Bio: "{bio}". Skills/tags: {tags_str}.

Recommended jobs:
{works_list}

Write only the message, nothing else."""

        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        if text:
            return text
    except Exception as e:
        logger.warning(f"Could not generate work suggestions message: {e}")
    return "These jobs match your profile and skills."


def get_work_suggestion_match_reasons(freelancer_profile, work_list: list) -> list:
    """
    Return a short reason string for each work explaining why it was suggested.
    work_list: list of Work instances. Returns list of strings, one per work.
    """
    if not work_list:
        return []
    model = get_gemini_model()
    if not model:
        return ["Matches your profile."] * len(work_list)
    try:
        tagline = getattr(freelancer_profile, 'tagline', '') or ''
        bio = (getattr(freelancer_profile, 'bio', '') or '')[:200]
        ai_tags = getattr(freelancer_profile, 'ai_tags', []) or []
        tags_str = ", ".join(ai_tags[:8]) if isinstance(ai_tags, list) else str(ai_tags)[:100]
        works_list = "\n".join(
            f"{i + 1}. {w.title} ({w.category or 'General'}): {w.description[:150]}..."
            for i, w in enumerate(work_list)
        )

        prompt = f"""You are a freelancer platform assistant. For each job below, write ONE short phrase (under 15 words) explaining why it fits this freelancer. Return ONLY a JSON list of strings, one per job, in the same order.

Freelancer: Tagline: "{tagline}". Bio: "{bio}". Skills/tags: {tags_str}.

Jobs:
{works_list}

Example: ["Your photography experience fits this wedding gig", "Location and rate match", ...]
Return nothing else — only the JSON list."""

        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        # Strip markdown code fence if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        reasons = json.loads(text)
        if isinstance(reasons, list) and len(reasons) >= len(work_list):
            return [str(r) for r in reasons[:len(work_list)]]
        if isinstance(reasons, list):
            # Pad if AI returned fewer
            return [str(r) for r in reasons] + ["Matches your profile."] * (len(work_list) - len(reasons))
    except Exception as e:
        logger.warning(f"Could not generate match reasons: {e}")
    return ["Matches your profile."] * len(work_list)


def keyword_based_matching(freelancer_profile, candidates, limit: int = 5) -> list:
    """
    Fallback matching using keyword overlap between freelancer profile and work.
    Uses tagline, bio, and ai_tags to match with work title, description, and skills.
    NEVER returns unrelated works.
    """
    # Build keyword set from freelancer profile fields
    profile_keywords = set()

    tagline = getattr(freelancer_profile, 'tagline', '') or ''
    bio = getattr(freelancer_profile, 'bio', '') or ''
    ai_tags = getattr(freelancer_profile, 'ai_tags', []) or []
    display_name = getattr(freelancer_profile, 'display_name', '') or ''

    if tagline:
        profile_keywords.update(tagline.lower().split())
    if bio:
        bio_words = [w for w in bio.lower().split() if len(w) > 3]
        profile_keywords.update(bio_words)
    if ai_tags:
        if isinstance(ai_tags, list):
            profile_keywords.update([str(t).lower() for t in ai_tags])
        else:
            profile_keywords.update(str(ai_tags).lower().split())
    if display_name:
        profile_keywords.update(display_name.lower().split())

    # If no profile keywords, return empty - don't show unrelated works
    if not profile_keywords:
        return []

    # Score each work by keyword overlap with title, description, category, and skills
    work_scores = []
    for w in candidates:
        work_text = f"{w.title} {w.description}".lower()
        # Also include skills and category
        if w.skills:
            if isinstance(w.skills, list):
                work_text += ' ' + ' '.join(w.skills).lower()
            else:
                work_text += ' ' + str(w.skills).lower()
        if w.category:
            work_text += ' ' + w.category.lower()

        # Find matching keywords
        matching_keywords = [kw for kw in profile_keywords if kw in work_text and len(kw) > 2]
        match_count = len(matching_keywords)

        if match_count > 0:
            work_scores.append((w.id, match_count, matching_keywords))

    # Sort by score descending
    work_scores.sort(key=lambda x: x[1], reverse=True)

    # Return only matched work IDs - never return all works
    # Require at least 1 keyword match
    matched_ids = [work_id for work_id, score, kw in work_scores if score > 0]

    return matched_ids[:limit]
