"""
Ranking algorithm for freelancer search results.
Fair AI-based ranking — no paid promotions.
"""
from datetime import timedelta
from django.utils import timezone


def compute_activity_score(freelancer_profile) -> float:
    """
    Fair ranking score — no paid promotions ever.

    Components:
    - Portfolio completeness  30%
    - Average rating          25%
    - Activity recency        20%
    - Profile views trend     15%
    - Review count            10%
    """
    from apps.portfolio.models import Portfolio

    # Portfolio completeness (30%)
    completeness_score = 0
    try:
        portfolio = freelancer_profile.portfolio
        completeness_score = (portfolio.completeness / 100) * 30
    except Portfolio.DoesNotExist:
        pass

    # Average rating (25%)
    rating_score = (freelancer_profile.avg_rating / 5.0) * 25

    # Activity recency (20%)
    activity_score = compute_recency_score(freelancer_profile) * 20

    # Profile views trend (15%)
    views_score = compute_views_trend(freelancer_profile) * 15

    # Review count (10%)
    review_count = freelancer_profile.review_count
    review_score = min(review_count / 10, 1.0) * 10

    return round(
        completeness_score + rating_score + activity_score + views_score + review_score, 2
    )


def compute_recency_score(freelancer_profile) -> float:
    """Calculate score based on how recently the freelancer was active."""
    # Check portfolio update time
    try:
        portfolio = freelancer_profile.portfolio
        if portfolio.updated_at:
            days_since_update = (timezone.now() - portfolio.updated_at).days
            if days_since_update <= 7:
                return 1.0
            elif days_since_update <= 30:
                return 0.7
            elif days_since_update <= 90:
                return 0.4
            else:
                return 0.1
    except Exception:
        pass

    # Fallback to profile update time
    days_since_update = (timezone.now() - freelancer_profile.updated_at).days
    if days_since_update <= 7:
        return 1.0
    elif days_since_update <= 30:
        return 0.7
    elif days_since_update <= 90:
        return 0.4
    else:
        return 0.1


def compute_views_trend(freelancer_profile) -> float:
    """Calculate score based on profile views."""
    # For now, just use absolute views normalized to a 0-1 scale
    # In production, you'd track views over time
    views = freelancer_profile.profile_views
    if views >= 100:
        return 1.0
    elif views >= 50:
        return 0.8
    elif views >= 20:
        return 0.6
    elif views >= 10:
        return 0.4
    elif views >= 1:
        return 0.2
    else:
        return 0.0


def rank_freelancers(freelancers_queryset) -> list:
    """
    Rank a queryset of freelancers by activity score.
    Returns sorted list.
    """
    return sorted(
        freelancers_queryset,
        key=lambda f: f.activity_score,
        reverse=True
    )
