"""
Messaging app URL configuration.
"""
from django.urls import path

from .views import (
    SendContactRequestView, InboxView, ConversationView,
    SendMessageView, UpdateRequestStatusView, MarkAsReadView
)

urlpatterns = [
    # Contact Requests
    path('contact/<int:freelancer_id>/', SendContactRequestView.as_view(), name='send-contact-request'),

    # Conversations
    path('inbox/', InboxView.as_view(), name='inbox'),
    path('<int:request_id>/', ConversationView.as_view(), name='conversation'),
    path('<int:request_id>/reply/', SendMessageView.as_view(), name='send-message'),
    path('<int:request_id>/status/', UpdateRequestStatusView.as_view(), name='update-status'),
    path('<int:request_id>/read/', MarkAsReadView.as_view(), name='mark-read'),
]
