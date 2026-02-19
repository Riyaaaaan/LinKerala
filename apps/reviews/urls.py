"""
Reviews app URL configuration.
"""
from django.urls import path

from .views import (
    CreateReviewView, FreelancerReviewsView, MyReviewsView, DeleteReviewView
)

urlpatterns = [
    path('<int:freelancer_id>/', FreelancerReviewsView.as_view(), name='freelancer-reviews'),
    path('create/<int:freelancer_id>/', CreateReviewView.as_view(), name='create-review'),
    path('mine/', MyReviewsView.as_view(), name='my-reviews'),
    path('<int:review_id>/', DeleteReviewView.as_view(), name='delete-review'),
]
