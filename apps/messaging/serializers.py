"""
Messaging app serializers for LocalFreelance AI.
"""
from rest_framework import serializers

from .models import ContactRequest, Message
from apps.accounts.serializers import FreelancerPublicSerializer, UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""

    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'is_read', 'created_at']


class ContactRequestSerializer(serializers.ModelSerializer):
    """Serializer for ContactRequest model."""

    sender = UserSerializer(read_only=True)
    freelancer = FreelancerPublicSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ContactRequest
        fields = [
            'id', 'sender', 'freelancer', 'message', 'status',
            'last_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'status', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None


class ContactRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a contact request."""

    class Meta:
        model = ContactRequest
        fields = ['freelancer', 'message']

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for a conversation (contact request with messages)."""

    messages = MessageSerializer(many=True, read_only=True)
    freelancer = FreelancerPublicSerializer(read_only=True)
    sender = UserSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ContactRequest
        fields = [
            'id', 'sender', 'freelancer', 'message', 'status',
            'messages', 'unread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_unread_count(self, obj):
        return obj.messages.filter(is_read=False).exclude(
            sender=self.context['request'].user
        ).count()


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a message."""

    class Meta:
        model = Message
        fields = ['content']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['request'] = self.context['contact_request']
        validated_data['sender'] = request.user
        return super().create(validated_data)
