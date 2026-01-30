from django.db import models


class PanelPermission(models.Model):
    """Модель для регистрации прав доступа к панели."""

    class Meta:
        permissions = [
            ("core_security_view", "Can view core security panel"),
        ]
        verbose_name = "Panel permission"
        verbose_name_plural = "Panel permissions"

    def __str__(self) -> str:  # pragma: no cover - модель используется для permissions
        return "Panel permission"
