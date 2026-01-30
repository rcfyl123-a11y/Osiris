from django.apps import AppConfig


class PanelConfig(AppConfig):
    """Конфигурация Django-приложения panel."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "osiris.apps.panel"
    verbose_name = "Panel"
