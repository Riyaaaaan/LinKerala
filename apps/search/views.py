"""
Search app views for LocalFreelance AI.
"""
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.accounts.models import FreelancerProfile
from apps.accounts.serializers import FreelancerPublicSerializer, WorkSerializer
from apps.portfolio.models import Category
from .ai_engine import (
    parse_search_query,
    get_recommendations,
    get_work_suggestions,
    get_work_suggestions_ai_message,
    get_work_suggestion_match_reasons,
)
from .ranking import rank_freelancers, compute_activity_score

logger = logging.getLogger(__name__)


class SearchView(APIView):
    """
    AI-powered natural language search.
    Example: "find a wedding photographer near downtown under $200"
    """

    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')

        if len(query) < 2:
            return Response({'results': [], 'query_parsed': {}})

        logger.info(f"Search query received: {query}")

        # Parse query with AI
        parsed = parse_search_query(query)

        # Log AI parsing results
        logger.info(f"AI parsed query: {parsed}")

        # Build queryset with filters
        freelancers = FreelancerProfile.objects.select_related('user').filter(
            user__is_active=True
        )

        # Filter by category/service type - check AI parsed type first
        service_type = parsed.get('service_type')
        query_lower = query.lower()

        # Also check if query directly contains any category names
        all_categories = Category.objects.all()
        if not service_type:
            for cat in all_categories:
                if cat.name.lower() in query_lower:
                    service_type = cat.name.lower()
                    logger.info(f"Category matched from query: {service_type}")
                    break

        if service_type:
            category = Category.objects.filter(
                name__icontains=service_type
            ).first()
            if category:
                logger.info(f"Filtering by category: {category.name}")
                # Filter freelancers who have this category in their portfolio
                freelancers = freelancers.filter(
                    portfolio__categories=category
                )
            else:
                # Also try filtering by display_name/skills if no category match
                logger.info(f"No category found, filtering by display_name/skills: {service_type}")
                from django.db.models import Q
                freelancers = freelancers.filter(
                    Q(display_name__icontains=service_type) |
                    Q(tagline__icontains=service_type) |
                    Q(bio__icontains=service_type)
                )

        # Filter by location
        if parsed.get('location'):
            location = parsed['location']
            logger.info(f"Filtering by location: {location}")
            freelancers = freelancers.filter(
                city__icontains=location
            )

        # Also filter by keywords in display_name, tagline, and bio
        keywords = parsed.get('keywords', [])
        if keywords:
            from django.db.models import Q
            keyword_queries = Q()
            for kw in keywords:
                keyword_queries |= Q(display_name__icontains=kw)
                keyword_queries |= Q(tagline__icontains=kw)
                keyword_queries |= Q(bio__icontains=kw)
            freelancers = freelancers.filter(keyword_queries)
            logger.info(f"Filtering by keywords: {keywords}")

        # Filter by budget
        if parsed.get('max_budget'):
            max_budget = parsed['max_budget']
            logger.info(f"Filtering by max budget: {max_budget}")
            freelancers = freelancers.filter(
                price_max__lte=max_budget
            )

        if parsed.get('min_budget'):
            min_budget = parsed['min_budget']
            logger.info(f"Filtering by min budget: {min_budget}")
            freelancers = freelancers.filter(
                price_min__gte=min_budget
            )

        # Filter by availability
        availability = request.query_params.get('availability')
        if availability:
            freelancers = freelancers.filter(availability=availability)

        # Filter by minimum rating
        min_rating_param = request.query_params.get('min_rating')
        if min_rating_param:
            try:
                min_rating = float(min_rating_param)
                # Filter in Python since avg_rating is a property
                freelancers = [f for f in freelancers if f.avg_rating >= min_rating]
            except (ValueError, TypeError):
                freelancers = list(freelancers)
        else:
            freelancers = list(freelancers)

        logger.info(f"Freelancers before ranking: {len(freelancers)}")

        # Rank results
        ranked_freelancers = rank_freelancers(freelancers)

        logger.info(f"Freelancers after ranking: {len(ranked_freelancers)}")

        # Serialize
        serializer = FreelancerPublicSerializer(ranked_freelancers, many=True)

        # Generate personalized message
        result_count = len(ranked_freelancers)
        message = generate_search_message(query, parsed, result_count)

        return Response({
            'results': serializer.data,
            'query_parsed': parsed,
            'count': result_count,
            'message': message
        })


def generate_search_message(query, parsed, count):
    """Generate a personalized message based on search results."""
    parts = []

    # Build message based on parsed query components
    if parsed.get('service_type'):
        parts.append(f"looking for {parsed['service_type']}")

    if parsed.get('keywords'):
        keywords_str = ", ".join(parsed['keywords'][:3])
        if len(parsed['keywords']) > 3:
            keywords_str += " and more"
        parts.append(f"with skills in {keywords_str}")

    if parsed.get('location'):
        parts.append(f"near {parsed['location']}")

    if parsed.get('max_budget'):
        parts.append(f"under ${parsed['max_budget']}")

    if parsed.get('min_budget'):
        parts.append(f"above ${parsed['min_budget']}")

    if parts:
        query_description = " ".join(parts)
    else:
        query_description = query

    if count == 0:
        return f"Sorry, we couldn't find any freelancers {query_description}. Try adjusting your search criteria."
    elif count == 1:
        return f"Found 1 freelancer {query_description}. Here's your perfect match!"
    else:
        return f"Found {count} freelancers {query_description}. Here are the best matches for you!"


class FreelancerListView(APIView):
    """Browse all freelancers with filters."""

    permission_classes = [AllowAny]

    def get(self, request):
        freelancers = FreelancerProfile.objects.select_related('user').filter(
            user__is_active=True
        )

        # Filters
        category = request.query_params.get('category')
        if category:
            cat = Category.objects.filter(slug=category).first()
            if cat:
                freelancers = freelancers.filter(portfolio__categories=cat)

        city = request.query_params.get('city')
        if city:
            freelancers = freelancers.filter(city__icontains=city)

        availability = request.query_params.get('availability')
        if availability:
            freelancers = freelancers.filter(availability=availability)

        min_price = request.query_params.get('min_price')
        if min_price:
            try:
                min_price = int(min_price)
                freelancers = freelancers.filter(price_min__gte=min_price)
            except ValueError:
                pass

        max_price = request.query_params.get('max_price')
        if max_price:
            try:
                max_price = int(max_price)
                freelancers = freelancers.filter(price_max__lte=max_price)
            except ValueError:
                pass

        # Sort by activity score
        freelancers = rank_freelancers(freelancers)

        # Pagination
        page = request.query_params.get('page', 1)
        page_size = 12
        start = (int(page) - 1) * page_size
        end = start + page_size

        paginated = freelancers[start:end]
        serializer = FreelancerPublicSerializer(paginated, many=True)

        return Response({
            'results': serializer.data,
            'count': len(freelancers),
            'page': int(page),
            'total_pages': (len(freelancers) + page_size - 1) // page_size
        })


class CategoryListView(APIView):
    """List all service categories."""

    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        data = [{'id': c.id, 'name': c.name, 'slug': c.slug, 'icon': c.icon} for c in categories]
        return Response(data)


class RecommendationsView(APIView):
    """Get personalized AI recommendations."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .ai_engine import get_recommendations

        # Get recommendations based on user profile
        try:
            client_profile = request.user.client_profile
            # In production, you'd use the client's search history, bookmarks, etc.
            recommended_ids = get_recommendations(client_profile, limit=10)
        except Exception:
            # Fallback to popular freelancers
            recommended_ids = []

        if not recommended_ids:
            # Fallback: get top freelancers by activity
            freelancers = FreelancerProfile.objects.select_related('user').filter(
                user__is_active=True,
                availability='available'
            )[:10]
        else:
            freelancers = FreelancerProfile.objects.filter(
                id__in=recommended_ids
            ).select_related('user')

        serializer = FreelancerPublicSerializer(freelancers, many=True)
        return Response({'results': serializer.data})


class TrendingView(APIView):
    """Get trending/most-active freelancers."""

    permission_classes = [AllowAny]

    def get(self, request):
        freelancers = FreelancerProfile.objects.select_related('user').filter(
            user__is_active=True,
            availability='available'
        ).order_by('-activity_score', '-profile_views')[:20]

        serializer = FreelancerPublicSerializer(freelancers, many=True)
        return Response({'results': serializer.data})


class BookmarksView(APIView):
    """Get client's bookmarked freelancers."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client_profile = request.user.client_profile
            bookmarks = client_profile.bookmarks.select_related('user').filter(
                user__is_active=True
            )
            serializer = FreelancerPublicSerializer(bookmarks, many=True)
            return Response({'results': serializer.data})
        except Exception as e:
            return Response({'results': [], 'error': str(e)})


class WorkSuggestionsView(APIView):
    """Get AI-powered work suggestions for freelancers."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.accounts.models import Work

        # Get the freelancer's profile
        try:
            freelancer_profile = request.user.freelancer_profile
        except Exception:
            return Response({'results': [], 'error': 'Freelancer profile not found'})

        # Get AI-powered work suggestions
        try:
            suggested_work_ids = get_work_suggestions(freelancer_profile, limit=10)
        except Exception as e:
            logger.error(f"Error in work suggestions: {e}")
            return Response({'results': [], 'error': str(e)})

        # Only return works that actually match - NO FALLBACK to all works
        if not suggested_work_ids:
            # Return empty results instead of showing unrelated works
            return Response({'results': [], 'message': 'No matching works found based on your profile'})

        works = Work.objects.filter(id__in=suggested_work_ids, status='open')
        order = {wid: i for i, wid in enumerate(suggested_work_ids)}
        work_list = sorted(works, key=lambda w: order.get(w.id, 999))

        work_summaries = [f"{w.title} ({w.category or 'General'})" for w in work_list]
        ai_message = get_work_suggestions_ai_message(request.user.freelancer_profile, work_summaries)
        match_reasons = get_work_suggestion_match_reasons(request.user.freelancer_profile, work_list)

        serializer = WorkSerializer(work_list, many=True)
        return Response({
            'results': serializer.data,
            'ai_message': ai_message,
            'match_reasons': match_reasons,
        })
