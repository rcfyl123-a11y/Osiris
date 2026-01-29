"""Main URL configuration for Osiris project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from osiris.apps.blog import views as blog_views
from osiris.config.discovery import discover_apps

urlpatterns = [
    path("", blog_views.home, name="home"),
    path("admin/", admin.site.urls),
]

for app in discover_apps():
    if app.urls_module:
        urlpatterns.append(
            path(
                f"{app.label}/",
                include((app.urls_module, app.label), namespace=app.label),
            )
        )

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
