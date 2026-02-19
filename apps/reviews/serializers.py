"""
Reviews app serializers for LocalFreelance AI.
"""
from rest_framework import serializers

from .models import Review
from apps.accounts.serializers import UserSerializer


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""

    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'freelancer', 'reviewer', 'rating', 'comment', 'is_verified', 'created_at']
        read_only_fields = ['id', 'reviewer', 'is_verified', 'created_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a review."""

    class Meta:
        model = Review
        fields = ['freelancer', 'rating', 'comment']

    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)


class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for listing reviews."""

    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'reviewer', 'rating', 'comment', 'is_verified', 'created_at']
        read_only_fields = fields
