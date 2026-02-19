"""
Portfolio app URL configuration.
"""
from django.urls import path

from .views import (
    MyPortfolioView, PortfolioCreateView, PortfolioUpdateView,
    PortfolioPublishView, PortfolioItemListView, PortfolioItemDetailView,
    CategoryListView, SkillListView, CategoryDetailView
)

urlpatterns = [
    # Portfolio CRUD
    path('mine/', MyPortfolioView.as_view(), name='my-portfolio'),
    path('create/', PortfolioCreateView.as_view(), name='portfolio-create'),
    path('update/', PortfolioUpdateView.as_view(), name='portfolio-update'),
    path('publish/', PortfolioPublishView.as_view(), name='portfolio-publish'),

    # Portfolio Items
    path('items/', PortfolioItemListView.as_view(), name='portfolio-items'),
    path('items/<int:pk>/', PortfolioItemDetailView.as_view(), name='portfolio-item-detail'),

    # Categories & Skills
    path('categories/', CategoryListView.as_view(), name='categories'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('skills/', SkillListView.as_view(), name='skills'),
]
