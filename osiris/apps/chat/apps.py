"""osiris.apps.chat.apps — конфигурация приложения чатов."""

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Конфигурация Django-приложения chat."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "osiris.apps.chat"
    verbose_name = "Чаты"
