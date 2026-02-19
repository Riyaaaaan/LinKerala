"""
Portfolio app admin configuration.
"""
from django.contrib import admin

from .models import Category, Skill, Portfolio, PortfolioItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['title', 'freelancer', 'is_published', 'completeness', 'created_at']
    list_filter = ['is_published', 'categories']
    search_fields = ['title', 'freelancer__display_name']
    raw_id_fields = ['freelancer']
    filter_horizontal = ['categories', 'skills']


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'portfolio', 'media_type', 'is_featured', 'created_at']
    list_filter = ['media_type', 'is_featured']
    search_fields = ['title', 'portfolio__title']
    raw_id_fields = ['portfolio']
