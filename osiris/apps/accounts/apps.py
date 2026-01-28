"""osiris.apps.accounts.apps — конфигурация приложения Accounts."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Конфигурация Django-приложения accounts."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "osiris.apps.accounts"
    verbose_name = "Accounts"
