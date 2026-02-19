"""
Reviews app views for LocalFreelance AI.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer, ReviewListSerializer
from apps.accounts.models import FreelancerProfile
from apps.accounts.permissions import IsClient


class CreateReviewView(APIView):
    """Create a review for a freelancer."""

    permission_classes = [IsAuthenticated, IsClient]

    def post(self, request, freelancer_id):
        try:
            freelancer = FreelancerProfile.objects.get(id=freelancer_id)
        except FreelancerProfile.DoesNotExist:
            return Response(
                {'error': 'Freelancer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user already reviewed this freelancer
        existing = Review.objects.filter(
            freelancer=freelancer,
            reviewer=request.user
        ).first()

        if existing:
            return Response(
                {'error': 'You have already reviewed this freelancer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data['freelancer'] = freelancer_id

        serializer = ReviewCreateSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            ReviewSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )


class FreelancerReviewsView(APIView):
    """Get all reviews for a freelancer."""

    permission_classes = [AllowAny]

    def get(self, request, freelancer_id):
        try:
            freelancer = FreelancerProfile.objects.get(id=freelancer_id)
        except FreelancerProfile.DoesNotExist:
            return Response(
                {'error': 'Freelancer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        reviews = Review.objects.filter(freelancer=freelancer)
        serializer = ReviewListSerializer(reviews, many=True)

        # Calculate average rating
        avg_rating = 0
        if reviews.exists():
            avg_rating = sum(r.rating for r in reviews) / reviews.count()

        return Response({
            'reviews': serializer.data,
            'count': reviews.count(),
            'avg_rating': round(avg_rating, 1)
        })


class MyReviewsView(APIView):
    """Get reviews given by the current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        reviews = Review.objects.filter(reviewer=request.user)
        serializer = ReviewListSerializer(reviews, many=True)
        return Response(serializer.data)


class DeleteReviewView(APIView):
    """Delete a review (only by the reviewer)."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if review.reviewer != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
