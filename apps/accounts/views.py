"""
Accounts app views for LocalFreelance AI.
"""
import logging

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.generic import RedirectView
from django.contrib.auth import get_user_model
from django.shortcuts import render

from .models import FreelancerProfile, ClientProfile, Work, Quote

logger = logging.getLogger(__name__)
from .serializers import (
    UserSerializer, FreelancerProfileSerializer, ClientProfileSerializer,
    RegisterFreelancerSerializer, RegisterClientSerializer, LoginSerializer,
    FreelancerPublicSerializer, WorkSerializer, WorkCreateSerializer,
    QuoteCreateSerializer, QuoteSerializer
)
from .permissions import IsFreelancer, IsClient, CanAccessFreelancerDashboard, CanAccessClientDashboard


class HomeView(RedirectView):
    """Home view that redirects authenticated users to their appropriate dashboard."""

    permanent = False

    def get_redirect_url(self, **kwargs):
        # Check for JWT token in cookies or headers
        access_token = self.request.COOKIES.get('access_token')

        if not access_token:
            # Try to get from Authorization header
            auth_header = self.request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                access_token = auth_header[7:]

        if access_token:
            try:
                from rest_framework_simplejwt.authentication import JWTAuthentication
                from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(access_token)
                user = jwt_auth.get_user(validated_token)

                if user.role == 'freelancer':
                    return '/dashboard/freelancer/'
                else:
                    return '/dashboard/client/'
            except (InvalidToken, TokenError, Exception):
                pass

        # Not authenticated, redirect to login
        return '/login/'


class RegisterFreelancerView(generics.CreateAPIView):
    """Register a new freelancer."""

    serializer_class = RegisterFreelancerSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class RegisterClientView(generics.CreateAPIView):
    """Register a new client."""

    serializer_class = RegisterClientSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Login view returning JWT tokens."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.contrib.auth import authenticate
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )

        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutView(APIView):
    """Logout view to invalidate refresh token."""

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    """Get current user info."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data

        if user.role == 'freelancer':
            try:
                profile = user.freelancer_profile
                data['profile'] = FreelancerProfileSerializer(profile).data
            except FreelancerProfile.DoesNotExist:
                pass
        elif user.role == 'client':
            try:
                profile = user.client_profile
                data['profile'] = ClientProfileSerializer(profile).data
            except ClientProfile.DoesNotExist:
                pass

        return Response(data)

    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class FreelancerDashboardView(APIView):
    """Freelancer dashboard view."""

    permission_classes = [CanAccessFreelancerDashboard]

    def get(self, request):
        try:
            profile = request.user.freelancer_profile
            serializer = FreelancerProfileSerializer(profile)
            return Response(serializer.data)
        except FreelancerProfile.DoesNotExist:
            return Response(
                {'error': 'Freelancer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class FreelancerProfileUpdateView(generics.UpdateAPIView):
    """Update freelancer profile."""

    serializer_class = FreelancerProfileSerializer
    permission_classes = [IsFreelancer]

    def get_object(self):
        return self.request.user.freelancer_profile


class ClientDashboardView(APIView):
    """Client dashboard view."""

    permission_classes = [CanAccessClientDashboard]

    def get(self, request):
        try:
            profile = request.user.client_profile
            serializer = ClientProfileSerializer(profile)
            return Response(serializer.data)
        except ClientProfile.DoesNotExist:
            return Response(
                {'error': 'Client profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class FreelancerPublicView(APIView):
    """Public freelancer profile view."""

    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            freelancer = FreelancerProfile.objects.select_related('user').get(user__username=username)
        except FreelancerProfile.DoesNotExist:
            from django.http import Http404
            raise Http404("Freelancer not found")

        # Get reviews for this freelancer
        from apps.reviews.models import Review
        from apps.reviews.serializers import ReviewListSerializer
        reviews = Review.objects.filter(freelancer=freelancer).order_by('-created_at')[:5]
        reviews_data = ReviewListSerializer(reviews, many=True).data

        context = {
            'freelancer': freelancer,
            'reviews': reviews_data,
            'profile': FreelancerPublicSerializer(freelancer).data,
        }
        return render(request, 'freelancer/public_profile.html', context)


class FreelancerPortfolioView(APIView):
    """Get freelancer's portfolio items."""

    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            freelancer = FreelancerProfile.objects.select_related('user').get(user__username=username)
            from apps.portfolio.models import Portfolio
            portfolio = Portfolio.objects.filter(freelancer=freelancer, is_published=True).first()

            data = FreelancerPublicSerializer(freelancer).data
            if portfolio:
                from apps.portfolio.serializers import PortfolioItemSerializer
                data['portfolio_items'] = PortfolioItemSerializer(
                    portfolio.items.all(), many=True
                ).data

            return Response(data)
        except FreelancerProfile.DoesNotExist:
            return Response(
                {'error': 'Freelancer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BookmarkFreelancerView(APIView):
    """Bookmark/unbookmark a freelancer."""

    permission_classes = [IsAuthenticated]

    def post(self, request, freelancer_id):
        try:
            # Check if user has a client profile
            if not hasattr(request.user, 'client_profile'):
                return Response(
                    {'error': 'Only clients can bookmark freelancers'},
                    status=status.HTTP_403_FORBIDDEN
                )

            client = request.user.client_profile
            freelancer = FreelancerProfile.objects.get(id=freelancer_id)

            if freelancer in client.bookmarks.all():
                client.bookmarks.remove(freelancer)
                return Response({'bookmarked': False})
            else:
                client.bookmarks.add(freelancer)
                return Response({'bookmarked': True})

        except FreelancerProfile.DoesNotExist:
            return Response(
                {'error': 'Freelancer not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AvailableRoutesView(APIView):
    """
    Return available routes based on user role.
    Clients see client routes + common routes.
    Freelancers see freelancer routes + common routes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Common routes (available to all authenticated users)
        common_routes = {
            'api': {
                'auth': {
                    'me': '/api/auth/me/',
                    'logout': '/api/auth/logout/',
                    'token_refresh': '/api/auth/token/refresh/',
                },
                'freelancers': {
                    'list': '/api/freelancers/',
                    'public': '/api/freelancers/<username>/',
                    'portfolio': '/api/freelancers/<username>/portfolio/',
                },
                'portfolio': {
                    'items': '/api/portfolio/items/',
                    'categories': '/api/portfolio/categories/',
                    'skills': '/api/portfolio/skills/',
                },
                'search': {
                    'search': '/api/search/',
                    'freelancers': '/api/search/freelancers/',
                    'categories': '/api/search/categories/',
                    'recommendations': '/api/search/recommendations/',
                    'trending': '/api/search/trending/',
                },
                'reviews': {
                    'freelancer_reviews': '/api/reviews/<freelancer_id>/',
                },
                'messaging': {
                    'inbox': '/api/messages/inbox/',
                    'conversation': '/api/messages/<request_id>/',
                },
            },
            'frontend': {
                'home': '/',
                'login': '/login/',
                'register': '/register/',
                'search': '/search/',
                'freelancer_profile': '/freelancer/<username>/',
            }
        }

        # Freelancer-specific routes
        freelancer_routes = {
            'api': {
                'auth': {
                    'dashboard': '/api/auth/freelancer/dashboard/',
                    'profile': '/api/auth/freelancer/profile/',
                },
                'portfolio': {
                    'my_portfolio': '/api/portfolio/mine/',
                    'create': '/api/portfolio/create/',
                    'update': '/api/portfolio/update/',
                    'publish': '/api/portfolio/publish/',
                },
                'reviews': {
                    'my_reviews': '/api/reviews/mine/',
                },
                'messaging': {
                    'contact': '/api/messages/contact/<freelancer_id>/',
                    'reply': '/api/messages/<request_id>/reply/',
                    'status': '/api/messages/<request_id>/status/',
                },
                'analytics': {
                    'dashboard': '/api/analytics/dashboard/',
                    'views': '/api/analytics/views/',
                },
            },
            'frontend': {
                'dashboard': '/dashboard/freelancer/',
            }
        }

        # Client-specific routes
        client_routes = {
            'api': {
                'auth': {
                    'dashboard': '/api/auth/client/dashboard/',
                },
                'works': {
                    'list': '/api/auth/works/',
                    'create': '/api/auth/works/',
                    'detail': '/api/auth/works/<id>/',
                    'public': '/api/auth/works/public/',
                },
                'freelancers': {
                    'bookmark': '/api/freelancers/<freelancer_id>/bookmark/',
                },
                'search': {
                    'bookmarks': '/api/search/bookmarks/',
                },
                'reviews': {
                    'create': '/api/reviews/create/<freelancer_id>/',
                },
                'analytics': {
                    'dashboard': '/api/analytics/dashboard/',
                },
            },
            'frontend': {
                'dashboard': '/dashboard/client/',
                'bookmarks': '/bookmarks/',
            }
        }

        # Build response based on user role
        if user.role == 'freelancer':
            routes = {
                'role': 'freelancer',
                'common': common_routes,
                'role_specific': freelancer_routes,
                'all': {**common_routes, **freelancer_routes}
            }
        elif user.role == 'client':
            routes = {
                'role': 'client',
                'common': common_routes,
                'role_specific': client_routes,
                'all': {**common_routes, **client_routes}
            }
        elif user.role == 'admin':
            # Admin gets everything
            routes = {
                'role': 'admin',
                'common': common_routes,
                'freelancer_routes': freelancer_routes,
                'client_routes': client_routes,
                'all': {**common_routes, **freelancer_routes, **client_routes}
            }
        else:
            # Unauthenticated or unknown role - only public routes
            routes = {
                'role': user.role or 'unknown',
                'common': common_routes,
                'role_specific': {},
                'all': common_routes
            }

        return Response(routes)


class AllowAnyPermission:
    """Allow any access."""

    def has_permission(self, request, view):
        return True


class WorkListCreateView(APIView):
    """List all works for the client or create a new work."""

    permission_classes = [AllowAnyPermission]

    def get(self, request):
        """Get all works for the current client."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required', 'code': 'not_authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user_role = getattr(request.user, 'role', None)
        if user_role != 'client' and not request.user.is_staff:
            return Response(
                {'error': 'Only clients can view their work listings', 'user_role': user_role},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            client = request.user.client_profile
            works = Work.objects.filter(client=client)
            serializer = WorkSerializer(works, many=True)
            return Response(serializer.data)
        except ClientProfile.DoesNotExist:
            return Response(
                {'error': 'Client profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        """Create a new work posting."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required', 'code': 'not_authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user_role = getattr(request.user, 'role', None)
        if user_role != 'client' and not request.user.is_staff:
            return Response(
                {'error': 'Only clients can post work. Your role is: ' + str(user_role), 'user_role': user_role},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            client = request.user.client_profile
        except ClientProfile.DoesNotExist:
            return Response(
                {'error': 'Client profile not found. Please complete your profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = WorkCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            work = serializer.save()
            return Response(
                WorkSerializer(work).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkDetailView(APIView):
    """Get, update, or delete a specific work."""

    permission_classes = [IsAuthenticated, IsClient]

    def get_object(self, pk, client):
        try:
            return Work.objects.get(pk=pk, client=client)
        except Work.DoesNotExist:
            return None

    def get(self, request, pk):
        """Get a specific work."""
        try:
            client = request.user.client_profile
            work = self.get_object(pk, client)
            if work is None:
                return Response(
                    {'error': 'Work not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = WorkSerializer(work)
            return Response(serializer.data)
        except ClientProfile.DoesNotExist:
            return Response(
                {'error': 'Client profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, pk):
        """Update a work."""
        try:
            client = request.user.client_profile
            work = self.get_object(pk, client)
            if work is None:
                return Response(
                    {'error': 'Work not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = WorkSerializer(work, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ClientProfile.DoesNotExist:
            return Response(
                {'error': 'Client profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        """Delete a work."""
        try:
            client = request.user.client_profile
            work = self.get_object(pk, client)
            if work is None:
                return Response(
                    {'error': 'Work not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            work.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClientProfile.DoesNotExist:
            return Response(
                {'error': 'Client profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class WorkPublicListView(APIView):
    """Public endpoint to list open works."""

    permission_classes = [AllowAny]

    def get(self, request):
        """Get all open works."""
        works = Work.objects.filter(status='open')
        serializer = WorkSerializer(works, many=True)
        return Response(serializer.data)


class ClientProfileUpdateView(APIView):
    """Update client profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get client profile."""
        try:
            client = request.user.client_profile
            serializer = ClientProfileSerializer(client)
            return Response(serializer.data)
        except ClientProfile.DoesNotExist:
            return Response({'error': 'Client profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        """Update client profile."""
        try:
            client = request.user.client_profile
            serializer = ClientProfileSerializer(client, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ClientProfile.DoesNotExist:
            # Create client profile if it doesn't exist
            client = ClientProfile.objects.create(
                user=request.user,
                full_name=request.data.get('full_name', ''),
                phone=request.data.get('phone', ''),
                city=request.data.get('city', ''),
            )
            return Response(ClientProfileSerializer(client).data, status=status.HTTP_201_CREATED)


class QuoteCreateView(APIView):
    """Create a new quote for a work opportunity."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new quote."""
        # Check if user is a freelancer
        try:
            freelancer = request.user.freelancer_profile
        except FreelancerProfile.DoesNotExist:
            return Response(
                {'error': 'Only freelancers can submit quotes'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if quote already exists for this work-freelancer combination
        work_id = request.data.get('work')
        logger.error(f"Quote create - work_id: {work_id}, user: {request.user.email}, data: {request.data}")
        if work_id:
            existing_quote = Quote.objects.filter(work_id=work_id, freelancer=freelancer).first()
            logger.error(f"Existing quote check: work_id={work_id}, freelancer={freelancer.id}, existing={existing_quote}")
            if existing_quote:
                return Response(
                    {'error': 'You have already submitted a quote for this work'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = QuoteCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            quote = serializer.save()
            return Response(
                QuoteSerializer(quote).data,
                status=status.HTTP_201_CREATED
            )
        logger.error(f"QuoteCreateSerializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuoteListView(APIView):
    """List quotes for the authenticated freelancer or client."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get quotes for the user based on their role."""
        user = request.user

        # Check if user is a freelancer
        try:
            freelancer = user.freelancer_profile
            quotes = Quote.objects.filter(freelancer=freelancer)
            serializer = QuoteSerializer(quotes, many=True)
            return Response(serializer.data)
        except FreelancerProfile.DoesNotExist:
            pass

        # Check if user is a client
        try:
            client = user.client_profile
            works = Work.objects.filter(client=client)
            quotes = Quote.objects.filter(work__in=works)
            serializer = QuoteSerializer(quotes, many=True)
            return Response(serializer.data)
        except ClientProfile.DoesNotExist:
            pass

        return Response(
            {'error': 'User must be a freelancer or client'},
            status=status.HTTP_403_FORBIDDEN
        )


class WorkQuotesView(APIView):
    """List all quotes for a specific work (for work owner)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, work_id):
        """Get all quotes for a specific work."""
        try:
            work = Work.objects.get(id=work_id)
            # Only the work owner can see all quotes
            if work.client.user != request.user:
                return Response(
                    {'error': 'You can only view quotes for your own work'},
                    status=status.HTTP_403_FORBIDDEN
                )
            quotes = Quote.objects.filter(work=work)
            serializer = QuoteSerializer(quotes, many=True)
            return Response(serializer.data)
        except Work.DoesNotExist:
            return Response(
                {'error': 'Work not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class QuoteDetailView(APIView):
    """Get, update, or delete a specific quote."""

    permission_classes = [IsAuthenticated]

    def get(self, request, quote_id):
        """Get a specific quote."""
        try:
            quote = Quote.objects.get(id=quote_id)
            # Only the quote owner or work owner can view
            if quote.freelancer.user != request.user and quote.work.client.user != request.user:
                return Response(
                    {'error': 'You can only view your own quotes'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = QuoteSerializer(quote)
            return Response(serializer.data)
        except Quote.DoesNotExist:
            return Response(
                {'error': 'Quote not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, quote_id):
        """Update a quote (status for client)."""
        try:
            quote = Quote.objects.get(id=quote_id)
            
            # Freelancer can update their quote details
            if quote.freelancer.user == request.user:
                serializer = QuoteSerializer(quote, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Client can update status
            if quote.work.client.user == request.user:
                status = request.data.get('status')
                if status in ['accepted', 'declined']:
                    quote.status = status
                    quote.save(update_fields=['status'])
                    return Response(QuoteSerializer(quote).data)
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {'error': 'You can only update your own quotes'},
                status=status.HTTP_403_FORBIDDEN
            )
        except Quote.DoesNotExist:
            return Response(
                {'error': 'Quote not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, quote_id):
        """Delete a quote (only by quote owner)."""
        try:
            quote = Quote.objects.get(id=quote_id)
            if quote.freelancer.user != request.user:
                return Response(
                    {'error': 'You can only delete your own quotes'},
                    status=status.HTTP_403_FORBIDDEN
                )
            quote.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Quote.DoesNotExist:
            return Response(
                {'error': 'Quote not found'},
                status=status.HTTP_404_NOT_FOUND
            )
