"""
Search app URL configuration.
"""
from django.urls import path

from .views import (
    SearchView, FreelancerListView, CategoryListView,
    RecommendationsView, TrendingView, BookmarksView, WorkSuggestionsView
)

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('freelancers/', FreelancerListView.as_view(), name='freelancer-list'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('recommendations/', RecommendationsView.as_view(), name='recommendations'),
    path('trending/', TrendingView.as_view(), name='trending'),
    path('bookmarks/', BookmarksView.as_view(), name='bookmarks'),
    path('work-suggestions/', WorkSuggestionsView.as_view(), name='work-suggestions'),
]
