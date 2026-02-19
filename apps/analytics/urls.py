"""
Analytics app URL configuration.
"""
from django.urls import path

from .views import DashboardAnalyticsView, ProfileViewsView, LogProfileView

urlpatterns = [
    path('dashboard/', DashboardAnalyticsView.as_view(), name='analytics-dashboard'),
    path('views/', ProfileViewsView.as_view(), name='profile-views'),
    path('log/<int:freelancer_id>/', LogProfileView.as_view(), name='log-profile-view'),
]
