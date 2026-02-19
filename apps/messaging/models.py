"""
Messaging app models for LocalFreelance AI.
"""
from django.db import models
from django.conf import settings


class ContactRequest(models.Model):
    """Initial contact request from client to freelancer."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_requests'
    )
    freelancer = models.ForeignKey(
        'accounts.FreelancerProfile',
        on_delete=models.CASCADE,
        related_name='contact_requests'
    )
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.email} -> {self.freelancer.display_name}"


class Message(models.Model):
    """Individual messages in a conversation."""

    request = models.ForeignKey(
        ContactRequest,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages_sent'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"
