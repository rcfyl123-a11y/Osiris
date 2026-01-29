"""osiris.apps.rca.apps — конфигурация приложения RCA."""

from django.apps import AppConfig


class RcaConfig(AppConfig):
    """Конфигурация Django-приложения rca."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "osiris.apps.rca"
    verbose_name = "RCA"

    def ready(self) -> None:
        from django.contrib.admin import helpers

        if not hasattr(helpers.AdminReadonlyField, "is_fieldset"):
            helpers.AdminReadonlyField.is_fieldset = False