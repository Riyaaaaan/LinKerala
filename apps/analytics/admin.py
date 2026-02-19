"""
Analytics app admin configuration.
"""
from django.contrib import admin

from .models import ProfileView, SearchQuery


@admin.register(ProfileView)
class ProfileViewAdmin(admin.ModelAdmin):
    list_display = ['id', 'freelancer', 'viewer', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['freelancer__display_name', 'viewer__email', 'ip_address']
    raw_id_fields = ['freelancer', 'viewer']


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'query', 'results_count', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['query', 'user__email']
    raw_id_fields = ['user']
