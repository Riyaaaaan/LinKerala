"""
Messaging app admin configuration.
"""
from django.contrib import admin

from .models import ContactRequest, Message


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'freelancer', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__email', 'freelancer__display_name']
    raw_id_fields = ['sender', 'freelancer']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'request', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__email', 'content']
    raw_id_fields = ['request', 'sender']
