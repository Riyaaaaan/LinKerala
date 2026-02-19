"""
Freelancer public URL configuration.
"""
from django.urls import path

from .views import (
    FreelancerPublicView, FreelancerPortfolioView, BookmarkFreelancerView
)

urlpatterns = [
    path('<str:username>/', FreelancerPublicView.as_view(), name='freelancer-public'),
    path('<str:username>/portfolio/', FreelancerPortfolioView.as_view(), name='freelancer-portfolio'),
    path('<int:freelancer_id>/bookmark/', BookmarkFreelancerView.as_view(), name='bookmark-freelancer'),
]
