"""osiris.apps.blog.apps — конфигурация приложения блога."""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Конфигурация Django-приложения blog."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "osiris.apps.blog"
