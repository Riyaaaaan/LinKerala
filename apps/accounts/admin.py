"""
Accounts app admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomUser, FreelancerProfile, ClientProfile


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'is_active', 'is_verified', 'date_joined']
    list_filter = ['role', 'is_active', 'is_verified']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'is_verified')}),
    )


@admin.register(FreelancerProfile)
class FreelancerProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user', 'city', 'state', 'availability', 'activity_score', 'profile_views']
    list_filter = ['availability', 'city', 'state']
    search_fields = ['display_name', 'user__email', 'user__username']
    raw_id_fields = ['user']


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'city']
    list_filter = ['city']
    search_fields = ['full_name', 'user__email', 'user__username']
    raw_id_fields = ['user', 'bookmarks']
    filter_horizontal = ['bookmarks']
