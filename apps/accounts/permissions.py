"""
Accounts app permissions for LocalFreelance AI.
"""
from rest_framework import permissions


class IsFreelancer(permissions.BasePermission):
    """Permission check for freelancer role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'freelancer'


class IsClient(permissions.BasePermission):
    """Permission check for client role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'client'


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to only allow owners of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff


class IsFreelancerOwner(permissions.BasePermission):
    """Permission to check if user owns the freelancer profile."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CanAccessFreelancerDashboard(permissions.BasePermission):
    """Permission to access freelancer dashboard."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'freelancer' or request.user.is_staff


class CanAccessClientDashboard(permissions.BasePermission):
    """Permission to access client dashboard."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'client' or request.user.is_staff
