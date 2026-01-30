"""Main URL configuration for Osiris project."""

import logging
from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from osiris.apps.core import views as core_views
from osiris.config import views as config_views

urlpatterns = [
    path("", core_views.home, name="home"),
    path("admin/", admin.site.urls),
    path("health/", config_views.health_check, name="health"),
]

APPS_DIR = Path(__file__).resolve().parent.parent / "apps"
logger = logging.getLogger(__name__)

for app_path in sorted(APPS_DIR.iterdir(), key=lambda path: path.name):
    if app_path.is_dir():
        app_urls = app_path / "urls.py"
        if app_urls.exists():
            try:
                app_name = app_path.name
                # Подключаем URL-ы только для приложений с urls.py; в DEBUG падём на ошибке импорта.
                urlpatterns.append(
                    path(f"{app_name}/", include(f"osiris.apps.{app_name}.urls"))
                )
            except ImportError as exc:
                logger.warning(
                    "Не удалось импортировать URL-модуль приложения %s: %s",
                    app_name,
                    exc,
                )
                if settings.DEBUG:
                    raise

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
