"""
URL configuration for LocalFreelance AI project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # API endpoints
    path('api/auth/', include('apps.accounts.urls')),
    path('api/portfolio/', include('apps.portfolio.urls')),
    path('api/search/', include('apps.search.urls')),
    path('api/freelancers/', include('apps.accounts.freelancer_urls')),
    path('api/messages/', include('apps.messaging.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    # Frontend views
    path('', include('apps.accounts.frontend_urls')),
    path('freelancer/', include('apps.accounts.freelancer_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
