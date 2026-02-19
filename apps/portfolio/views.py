"""
Portfolio app views for LocalFreelance AI.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from .models import Category, Skill, Portfolio, PortfolioItem
from .serializers import (
    CategorySerializer, SkillSerializer, PortfolioSerializer,
    PortfolioCreateSerializer, PortfolioItemSerializer, PortfolioItemCreateSerializer
)
from .utils import ai_tag_portfolio_item
from apps.accounts.permissions import IsFreelancer


class MyPortfolioView(APIView):
    """Get freelancer's own portfolio."""

    permission_classes = [IsAuthenticated, IsFreelancer]

    def get(self, request):
        try:
            portfolio = request.user.freelancer_profile.portfolio
            serializer = PortfolioSerializer(portfolio)
            return Response(serializer.data)
        except Portfolio.DoesNotExist:
            return Response(
                {'error': 'Portfolio not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PortfolioCreateView(generics.CreateAPIView):
    """Create a new portfolio."""

    serializer_class = PortfolioCreateSerializer
    permission_classes = [IsAuthenticated, IsFreelancer]

    def perform_create(self, serializer):
        serializer.save()


class PortfolioUpdateView(generics.UpdateAPIView):
    """Update portfolio details."""

    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated, IsFreelancer]

    def get_object(self):
        try:
            return self.request.user.freelancer_profile.portfolio
        except Portfolio.DoesNotExist:
            return None

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response(
                {'error': 'Portfolio not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PortfolioPublishView(APIView):
    """Toggle portfolio publish status."""

    permission_classes = [IsAuthenticated, IsFreelancer]

    def post(self, request):
        try:
            portfolio = request.user.freelancer_profile.portfolio
            portfolio.is_published = not portfolio.is_published
            portfolio.save(update_fields=['is_published'])
            return Response({'is_published': portfolio.is_published})
        except Portfolio.DoesNotExist:
            return Response(
                {'error': 'Portfolio not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PortfolioItemListView(generics.ListCreateAPIView):
    """List and create portfolio items."""

    serializer_class = PortfolioItemSerializer
    permission_classes = [IsAuthenticated, IsFreelancer]

    def get_queryset(self):
        try:
            portfolio = self.request.user.freelancer_profile.portfolio
            return portfolio.items.all()
        except Portfolio.DoesNotExist:
            return PortfolioItem.objects.none()

    def perform_create(self, serializer):
        portfolio = self.request.user.freelancer_profile.portfolio
        item = serializer.save()

        # AI tag the image if it's an image
        if item.media_type == 'image':
            tags = ai_tag_portfolio_item(item.media_url)
            if tags:
                item.ai_tags = tags
                item.save(update_fields=['ai_tags'])

        # Recalculate completeness
        portfolio.calculate_completeness()


class PortfolioItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a portfolio item."""

    serializer_class = PortfolioItemSerializer
    permission_classes = [IsAuthenticated, IsFreelancer]

    def get_queryset(self):
        try:
            portfolio = self.request.user.freelancer_profile.portfolio
            return portfolio.items.all()
        except Portfolio.DoesNotExist:
            return PortfolioItem.objects.none()


class CategoryListView(generics.ListAPIView):
    """List all categories."""

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    queryset = Category.objects.all()


class SkillListView(generics.ListAPIView):
    """List all skills."""

    serializer_class = SkillSerializer
    permission_classes = [AllowAny]
    queryset = Skill.objects.all()


class CategoryDetailView(generics.RetrieveAPIView):
    """Get a single category."""

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    queryset = Category.objects.all()
