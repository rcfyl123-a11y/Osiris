from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Конфигурация Django-приложения core."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "osiris.apps.core"
    verbose_name = "Core"

    def ready(self) -> None:
        from . import checks  # noqa: F401
