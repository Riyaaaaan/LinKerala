"""
Development settings for LocalFreelance AI.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Use SQLite for development (easier setup)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Allow all hosts in development
ALLOWED_HOSTS = ['*']
