"""
Portfolio app serializers for LocalFreelance AI.
"""
from rest_framework import serializers

from .models import Category, Skill, Portfolio, PortfolioItem


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']
        read_only_fields = ['id']


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model."""

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Skill
        fields = ['id', 'name', 'category', 'category_name']
        read_only_fields = ['id']


class PortfolioItemSerializer(serializers.ModelSerializer):
    """Serializer for PortfolioItem model."""

    class Meta:
        model = PortfolioItem
        fields = [
            'id', 'title', 'description', 'media_url', 'media_type',
            'ai_tags', 'is_featured', 'created_at'
        ]
        read_only_fields = ['id', 'ai_tags', 'created_at']


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio model."""

    items = PortfolioItemSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    skill_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Portfolio
        fields = [
            'id', 'title', 'description', 'is_published', 'completeness',
            'categories', 'skills', 'items', 'category_ids', 'skill_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'completeness', 'created_at', 'updated_at']

    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        skill_ids = validated_data.pop('skill_ids', [])

        portfolio = Portfolio.objects.create(**validated_data)

        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            portfolio.categories.set(categories)

        if skill_ids:
            skills = Skill.objects.filter(id__in=skill_ids)
            portfolio.skills.set(skills)

        portfolio.calculate_completeness()
        return portfolio

    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        skill_ids = validated_data.pop('skill_ids', None)

        instance = super().update(instance, validated_data)

        if category_ids is not None:
            categories = Category.objects.filter(id__in=category_ids)
            instance.categories.set(categories)

        if skill_ids is not None:
            skills = Skill.objects.filter(id__in=skill_ids)
            instance.skills.set(skills)

        instance.calculate_completeness()
        return instance


class PortfolioCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new portfolio."""

    class Meta:
        model = Portfolio
        fields = ['title', 'description']

    def create(self, validated_data):
        freelancer = self.context['request'].user.freelancer_profile
        portfolio = Portfolio.objects.create(
            freelancer=freelancer,
            **validated_data
        )
        return portfolio


class PortfolioItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a portfolio item."""

    class Meta:
        model = PortfolioItem
        fields = ['title', 'description', 'media_url', 'media_type', 'is_featured']

    def create(self, validated_data):
        portfolio = self.context['portfolio']
        return PortfolioItem.objects.create(portfolio=portfolio, **validated_data)
