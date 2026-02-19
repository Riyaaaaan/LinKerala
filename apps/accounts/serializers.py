"""
Accounts app serializers for LocalFreelance AI.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import FreelancerProfile, ClientProfile, Work, Quote

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model."""

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'is_verified', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class FreelancerProfileSerializer(serializers.ModelSerializer):
    """Serializer for FreelancerProfile model."""

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = FreelancerProfile
        fields = [
            # User info
            'id', 'username', 'email',
            # Basic info
            'display_name', 'tagline', 'bio', 'profile_photo', 'cover_photo',
            # Location
            'city', 'state', 'country', 'latitude', 'longitude', 'address',
            # Pricing
            'hourly_rate', 'price_min', 'price_max',
            # Availability & Response
            'availability', 'response_time_hours',
            # Experience
            'years_experience', 'languages',
            # Social Links
            'linkedin_url', 'website_url', 'github_url', 'twitter_url', 'instagram_url',
            # Professional Info
            'education', 'work_experience', 'certifications',
            # System fields
            'ai_tags', 'activity_score', 'profile_views', 'is_profile_complete',
            'avg_rating', 'review_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ai_tags', 'activity_score', 'profile_views', 'is_profile_complete', 'created_at', 'updated_at']


class ClientProfileSerializer(serializers.ModelSerializer):
    """Serializer for ClientProfile model."""

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ClientProfile
        fields = ['id', 'username', 'email', 'full_name', 'profile_photo', 'city', 'phone', 'is_profile_complete', 'bookmarks']
        read_only_fields = ['id', 'bookmarks']


class RegisterFreelancerSerializer(serializers.ModelSerializer):
    """Serializer for freelancer registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    display_name = serializers.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'display_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            role='freelancer'
        )
        FreelancerProfile.objects.create(
            user=user,
            display_name=validated_data['display_name']
        )
        return user


class RegisterClientSerializer(serializers.ModelSerializer):
    """Serializer for client registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'full_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            role='client'
        )
        ClientProfile.objects.create(
            user=user,
            full_name=validated_data['full_name']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class FreelancerPublicSerializer(serializers.ModelSerializer):
    """Public serializer for freelancer profile (no sensitive data)."""

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = FreelancerProfile
        fields = [
            # Basic info
            'id', 'username', 'display_name', 'tagline', 'bio',
            'profile_photo', 'cover_photo',
            # Contact
            'email',
            # Location
            'city', 'state', 'country',
            # Pricing & Availability
            'hourly_rate', 'price_min', 'price_max', 'availability', 'response_time_hours',
            # Experience & Skills
            'years_experience', 'languages',
            # Social Links (public)
            'linkedin_url', 'website_url', 'github_url',
            # Professional Info
            'education', 'work_experience', 'certifications',
            # Stats
            'activity_score', 'avg_rating', 'review_count', 'profile_views'
        ]


class WorkSerializer(serializers.ModelSerializer):
    """Serializer for Work model."""

    client_name = serializers.CharField(source='client.full_name', read_only=True)
    client_username = serializers.CharField(source='client.user.username', read_only=True)
    client_phone = serializers.SerializerMethodField()
    client_city = serializers.CharField(source='client.city', read_only=True)

    class Meta:
        model = Work
        fields = [
            'id', 'client', 'client_name', 'client_username', 'client_phone', 'client_city', 'title', 'description', 'category',
            'pay_per_hour', 'duration_value', 'duration_unit', 'location',
            'status', 'skills', 'show_contact_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'client', 'created_at', 'updated_at']

    def get_client_phone(self, obj):
        """Return phone only if show_contact_info is True."""
        if obj.show_contact_info:
            return obj.client.phone
        return None


class WorkCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Work."""

    class Meta:
        model = Work
        fields = [
            'title', 'description', 'category',
            'pay_per_hour', 'duration_value', 'duration_unit', 'location', 'skills', 'show_contact_info'
        ]

    def create(self, validated_data):
        # Get the client profile from the request user
        client = self.context['request'].user.client_profile
        validated_data['client'] = client
        return super().create(validated_data)


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for Quote model."""

    freelancer_name = serializers.CharField(source='freelancer.full_name', read_only=True)
    work_title = serializers.CharField(source='work.title', read_only=True)
    work_client_email = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = [
            'id', 'work', 'work_title', 'freelancer', 'freelancer_name',
            'proposed_rate', 'estimated_duration', 'cover_letter',
            'status', 'email_sent', 'email_sent_at', 'created_at', 'updated_at',
            'work_client_email'
        ]
        read_only_fields = ['id', 'freelancer', 'status', 'email_sent', 'email_sent_at', 'created_at', 'updated_at']

    def get_work_client_email(self, obj):
        """Return client email for sending quote."""
        return obj.work.client.user.email


class QuoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Quote."""

    send_email = serializers.BooleanField(default=True, write_only=True, help_text="Send quote via email to client")

    class Meta:
        model = Quote
        fields = [
            'work', 'proposed_rate', 'estimated_duration', 'cover_letter', 'send_email'
        ]

    def create(self, validated_data):
        send_email = validated_data.pop('send_email', True)
        freelancer = self.context['request'].user.freelancer_profile
        validated_data['freelancer'] = freelancer
        
        quote = super().create(validated_data)
        
        if send_email:
            try:
                quote.send_quote_email()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error sending quote email: {e}")
        
        return quote
