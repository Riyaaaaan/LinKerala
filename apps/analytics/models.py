"""
Analytics app models for LocalFreelance AI.
"""
from django.db import models
from django.conf import settings


class ProfileView(models.Model):
    """Track profile views."""

    freelancer = models.ForeignKey(
        'accounts.FreelancerProfile',
        on_delete=models.CASCADE,
        related_name='view_records'
    )
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    referrer = models.CharField(max_length=500, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.freelancer.display_name} - {self.viewed_at}"


class SearchQuery(models.Model):
    """Log search queries for analytics."""

    query = models.CharField(max_length=500)
    results_count = models.IntegerField(default=0)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.query
