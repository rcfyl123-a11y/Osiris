"""
Main URL configuration for Osiris project
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os
from pathlib import Path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Dynamically discover and include app URLs
APPS_DIR = Path(__file__).resolve().parent.parent / "apps"

for app_path in APPS_DIR.iterdir():
    if app_path.is_dir():
        # Look for urls.py in each app
        app_urls = app_path / "urls.py"
        if app_urls.exists():
            # Import the app's urls module and add to urlpatterns
            try:
                app_name = app_path.name
                urlpatterns.append(
                    path(f"{app_name}/", include(f"{app_name}.urls"))
                )
            except ImportError:
                pass  # Skip apps that don't have a proper urls.py

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static('/media/', document_root='media')