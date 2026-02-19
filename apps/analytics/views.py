"""
Analytics app views for LocalFreelance AI.
"""
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ProfileView, SearchQuery
from apps.accounts.permissions import IsFreelancer


class DashboardAnalyticsView(APIView):
    """Get freelancer analytics summary."""

    permission_classes = [IsAuthenticated, IsFreelancer]

    def get(self, request):
        freelancer = request.user.freelancer_profile

        # Profile views (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_views = ProfileView.objects.filter(
            freelancer=freelancer,
            viewed_at__gte=thirty_days_ago
        )

        # Total views
        total_views = freelancer.profile_views

        # Views by day (last 30 days)
        views_by_day = {}
        for i in range(30):
            day = (timezone.now() - timedelta(days=i)).date()
            count = recent_views.filter(viewed_at__date=day).count()
            views_by_day[str(day)] = count

        # Get message inquiries
        from apps.messaging.models import ContactRequest
        inquiries = ContactRequest.objects.filter(
            freelancer=freelancer
        )

        # Get reviews
        from apps.reviews.models import Review
        reviews = Review.objects.filter(freelancer=freelancer)

        return Response({
            'profile_views': {
                'total': total_views,
                'last_30_days': recent_views.count(),
                'by_day': views_by_day
            },
            'inquiries': {
                'total': inquiries.count(),
                'pending': inquiries.filter(status='pending').count(),
                'accepted': inquiries.filter(status='accepted').count(),
                'declined': inquiries.filter(status='declined').count(),
            },
            'reviews': {
                'total': reviews.count(),
                'avg_rating': freelancer.avg_rating
            },
            'activity_score': freelancer.activity_score
        })


class ProfileViewsView(APIView):
    """Get profile view history."""

    permission_classes = [IsAuthenticated, IsFreelancer]

    def get(self, request):
        freelancer = request.user.freelancer_profile

        # Get days parameter (default 30)
        days = request.query_params.get('days', 30, type=int)
        since = timezone.now() - timedelta(days=days)

        views = ProfileView.objects.filter(
            freelancer=freelancer,
            viewed_at__gte=since
        ).order_by('-viewed_at')[:100]

        data = []
        for view in views:
            data.append({
                'id': view.id,
                'viewer_email': view.viewer.email if view.viewer else None,
                'ip_address': view.ip_address,
                'referrer': view.referrer,
                'viewed_at': view.viewed_at.isoformat()
            })

        return Response({'views': data})


class LogProfileView(APIView):
    """Log a profile view (called when someone views a freelancer profile)."""

    permission_classes = []  # Public access

    def post(self, request, freelancer_id):
        from apps.accounts.models import FreelancerProfile
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            freelancer = FreelancerProfile.objects.get(id=freelancer_id)
        except FreelancerProfile.DoesNotExist:
            return Response({'error': 'Freelancer not found'}, status=404)

        # Get viewer (if authenticated)
        viewer = None
        if request.user.is_authenticated:
            viewer = request.user

        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Create view record
        ProfileView.objects.create(
            freelancer=freelancer,
            viewer=viewer,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referrer=request.META.get('HTTP_REFERER', '')
        )

        # Increment view count
        freelancer.profile_views += 1
        freelancer.save(update_fields=['profile_views'])

        return Response({'success': True})
