"""
WSGI config for Osiris project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from pathlib import Path

# Add the apps directory to the Python path so Django can find the apps
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "apps"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osiris.settings')

application = get_wsgi_application()