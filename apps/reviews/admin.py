"""
Reviews app admin configuration.
"""
from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'freelancer', 'reviewer', 'rating', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'rating', 'created_at']
    search_fields = ['freelancer__display_name', 'reviewer__email', 'comment']
    raw_id_fields = ['freelancer', 'reviewer']
