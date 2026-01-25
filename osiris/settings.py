"""
Settings for Osiris project
"""

from .config import *
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Add apps directory to Python path so Django can discover them
import sys
sys.path.insert(0, str(APPS_DIR))

# Discover and add apps automatically
def discover_apps():
    """Discover apps in the apps directory and return their names."""
    discovered_apps = []
    
    if APPS_DIR.exists():
        for app_dir in APPS_DIR.iterdir():
            if app_dir.is_dir():
                # Check if it's a Django app by looking for apps.py
                apps_py = app_dir / "apps.py"
                init_py = app_dir / "__init__.py"
                
                if apps_py.exists() or init_py.exists():
                    # Add the app to INSTALLED_APPS
                    app_name = f"apps.{app_dir.name}"
                    discovered_apps.append(app_name)
                    
    return discovered_apps

# Update INSTALLED_APPS with discovered apps
DISCOVERED_APPS = discover_apps()
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
] + DISCOVERED_APPS

# Database configuration - each app can override this if needed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files configuration
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}