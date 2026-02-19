"""
Portfolio app models for LocalFreelance AI.
"""
from django.db import models
from django.conf import settings


class Category(models.Model):
    """Service categories: Photography, Tutoring, etc."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Skills that freelancers can have."""

    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='skills'
    )

    def __str__(self):
        return self.name


class Portfolio(models.Model):
    """A freelancer's main portfolio container."""

    freelancer = models.OneToOneField(
        'accounts.FreelancerProfile',
        on_delete=models.CASCADE,
        related_name='portfolio'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    completeness = models.IntegerField(default=0)
    categories = models.ManyToManyField(Category, blank=True, related_name='portfolios')
    skills = models.ManyToManyField(Skill, blank=True, related_name='portfolios')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.freelancer.display_name}'s Portfolio"

    def calculate_completeness(self):
        """Calculate profile completeness score (0-100)."""
        score = 0

        if self.title:
            score += 10
        if self.description and len(self.description) > 50:
            score += 15
        if self.categories.exists():
            score += 15
        if self.skills.exists():
            score += 15
        if self.items.exists():
            score += 25
            featured = self.items.filter(is_featured=True).exists()
            if featured:
                score += 20

        self.completeness = min(score, 100)
        self.save(update_fields=['completeness'])


class PortfolioItem(models.Model):
    """Individual work samples in a portfolio."""

    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
    ]

    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='items'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    media_url = models.URLField()
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default='image')
    ai_tags = models.JSONField(default=list)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
