"""
Messaging app views for LocalFreelance AI.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ContactRequest, Message
from .serializers import (
    ContactRequestSerializer, ContactRequestCreateSerializer,
    ConversationSerializer, MessageSerializer, MessageCreateSerializer
)
from apps.accounts.permissions import IsFreelancer, IsClient
from apps.accounts.models import FreelancerProfile


class SendContactRequestView(APIView):
    """Send a contact request to a freelancer."""

    permission_classes = [IsAuthenticated, IsClient]

    def post(self, request, freelancer_id):
        try:
            freelancer = FreelancerProfile.objects.get(id=freelancer_id)
        except FreelancerProfile.DoesNotExist:
            return Response(
                {'error': 'Freelancer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if request already exists
        existing = ContactRequest.objects.filter(
            sender=request.user,
            freelancer=freelancer
        ).first()

        if existing:
            serializer = ContactRequestSerializer(existing)
            return Response(serializer.data)

        data = request.data.copy()
        data['freelancer'] = freelancer_id

        serializer = ContactRequestCreateSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            ContactRequestSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )


class InboxView(APIView):
    """Get all conversations for the current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == 'freelancer':
            # Get requests sent to this freelancer
            requests = ContactRequest.objects.filter(
                freelancer=user.freelancer_profile
            ).select_related('sender', 'freelancer__user')
        else:
            # Get requests sent by this client
            requests = ContactRequest.objects.filter(
                sender=user
            ).select_related('sender', 'freelancer__user')

        serializer = ConversationSerializer(requests, many=True, context={'request': request})
        return Response(serializer.data)


class ConversationView(APIView):
    """Get a specific conversation with all messages."""

    permission_classes = [IsAuthenticated]

    def get(self, request, request_id):
        try:
            conversation = ContactRequest.objects.get(id=request_id)
        except ContactRequest.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is part of this conversation
        user = request.user
        is_freelancer = user.role == 'freelancer' and conversation.freelancer.user == user
        is_sender = conversation.sender == user

        if not (is_freelancer or is_sender):
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data)


class SendMessageView(APIView):
    """Send a message in an existing conversation."""

    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            conversation = ContactRequest.objects.get(id=request_id)
        except ContactRequest.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is part of this conversation
        user = request.user
        is_freelancer = user.role == 'freelancer' and conversation.freelancer.user == user
        is_sender = conversation.sender == user

        if not (is_freelancer or is_sender):
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MessageCreateSerializer(
            data=request.data,
            context={'request': request, 'contact_request': conversation}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            MessageSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )


class UpdateRequestStatusView(APIView):
    """Accept or decline a contact request (freelancer only)."""

    permission_classes = [IsAuthenticated, IsFreelancer]

    def patch(self, request, request_id):
        try:
            conversation = ContactRequest.objects.get(id=request_id)
        except ContactRequest.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify freelancer owns this request
        if conversation.freelancer.user != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        if new_status not in ['accepted', 'declined']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversation.status = new_status
        conversation.save(update_fields=['status'])

        return Response(ContactRequestSerializer(conversation).data)


class MarkAsReadView(APIView):
    """Mark messages in a conversation as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            conversation = ContactRequest.objects.get(id=request_id)
        except ContactRequest.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mark unread messages from the other user as read
        updated = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)

        return Response({'updated_count': updated})
