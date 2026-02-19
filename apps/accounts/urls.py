"""
Accounts app URL configuration for API endpoints.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterFreelancerView, RegisterClientView, LoginView, LogoutView,
    CurrentUserView, FreelancerDashboardView, FreelancerProfileUpdateView,
    ClientDashboardView, AvailableRoutesView,
    WorkListCreateView, WorkDetailView, WorkPublicListView,
    ClientProfileUpdateView,
    QuoteCreateView, QuoteListView, QuoteDetailView, WorkQuotesView
)

urlpatterns = [
    # Authentication
    path('register/freelancer/', RegisterFreelancerView.as_view(), name='register-freelancer'),
    path('register/client/', RegisterClientView.as_view(), name='register-client'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', CurrentUserView.as_view(), name='current-user'),

    # Freelancer
    path('freelancer/dashboard/', FreelancerDashboardView.as_view(), name='freelancer-dashboard'),
    path('freelancer/profile/', FreelancerProfileUpdateView.as_view(), name='freelancer-profile-update'),

    # Client
    path('client/dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('client/profile/', ClientProfileUpdateView.as_view(), name='client-profile-update'),

    # Work/Jobs
    path('works/', WorkListCreateView.as_view(), name='work-list-create'),
    path('works/<int:pk>/', WorkDetailView.as_view(), name='work-detail'),
    path('works/public/', WorkPublicListView.as_view(), name='work-public-list'),

    # Quotes
    path('quotes/', QuoteListView.as_view(), name='quote-list'),
    path('quotes/create/', QuoteCreateView.as_view(), name='quote-create'),
    path('quotes/<int:quote_id>/', QuoteDetailView.as_view(), name='quote-detail'),
    path('works/<int:work_id>/quotes/', WorkQuotesView.as_view(), name='work-quotes'),

    # Role-based routes
    path('routes/', AvailableRoutesView.as_view(), name='available-routes'),
]
