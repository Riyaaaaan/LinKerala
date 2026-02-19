"""
Frontend URL configuration.
"""
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from .views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login-page'),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register-page'),
    path('register/freelancer/', TemplateView.as_view(template_name='auth/register_freelancer.html'), name='register-freelancer-page'),
    path('dashboard/freelancer/', TemplateView.as_view(template_name='freelancer/dashboard.html'), name='freelancer-dashboard'),
    path('dashboard/client/', TemplateView.as_view(template_name='user/dashboard.html'), name='client-dashboard'),
    path('profile/', TemplateView.as_view(template_name='user/profile.html'), name='client-profile'),
    path('search/', TemplateView.as_view(template_name='user/search_results.html'), name='search-results'),
    path('bookmarks/', TemplateView.as_view(template_name='user/bookmarks.html'), name='bookmarks'),
    path('inbox/', TemplateView.as_view(template_name='user/inbox.html'), name='inbox'),
]
