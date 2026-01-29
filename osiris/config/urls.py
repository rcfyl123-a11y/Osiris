"""Main URL configuration for Osiris project."""

from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from osiris.apps.blog import views as blog_views

urlpatterns = [
    path("", blog_views.home, name="home"),
    path("admin/", admin.site.urls),
]

APPS_DIR = Path(__file__).resolve().parent.parent / "apps"

for app_path in APPS_DIR.iterdir():
    if app_path.is_dir():
        app_urls = app_path / "urls.py"
        if app_urls.exists():
            try:
                app_name = app_path.name
                urlpatterns.append(
                    path(f"{app_name}/", include(f"osiris.apps.{app_name}.urls"))
                )
            except ImportError:
                pass

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

