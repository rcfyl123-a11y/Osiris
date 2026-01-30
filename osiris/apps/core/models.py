from django.conf import settings
from django.db import models


class SecurityEvent(models.Model):
    class EventType(models.TextChoices):
        DENIED_PERIMETER = "DENIED_PERIMETER", "Denied (perimeter)"
        DENIED_BIND = "DENIED_BIND", "Denied (bind)"
        BIND_MISMATCH = "BIND_MISMATCH", "Bind mismatch"
        LOGIN_NEW_IP = "LOGIN_NEW_IP", "Login from new IP"
        FILE_DOWNLOAD = "FILE_DOWNLOAD", "File download"
        SENSITIVE_ACTION = "SENSITIVE_ACTION", "Sensitive action"
        PANEL_VIEW = "PANEL_VIEW", "Panel view"

    event_type = models.CharField(max_length=32, choices=EventType.choices, verbose_name="Тип события")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events",
        verbose_name="Пользователь",
    )
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    path = models.CharField(max_length=512, blank=True, verbose_name="Путь")
    method = models.CharField(max_length=12, blank=True, verbose_name="Метод")
    status_code = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="HTTP статус")
    user_agent = models.CharField(max_length=255, blank=True, verbose_name="User-Agent")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Причина")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    class Meta:
        verbose_name = "Security событие"
        verbose_name_plural = "Security события"
        indexes = [
            models.Index(fields=["created_at"], name="core_sec_event_created_idx"),
            models.Index(fields=["ip_address"], name="core_sec_event_ip_idx"),
            models.Index(fields=["user"], name="core_sec_event_user_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} {self.ip_address}"


class Workstation(models.Model):
    ip_address = models.GenericIPAddressField(unique=True, verbose_name="IP-адрес")
    hostname = models.CharField(max_length=255, blank=True, verbose_name="Имя хоста")
    label = models.CharField(max_length=255, blank=True, verbose_name="Метка")
    description = models.TextField(blank=True, verbose_name="Описание")
    department = models.CharField(max_length=255, blank=True, verbose_name="Подразделение")
    location = models.CharField(max_length=255, blank=True, verbose_name="Локация")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="allowed_workstations",
        verbose_name="Разрешенные пользователи",
    )

    class Meta:
        verbose_name = "Рабочее место"
        verbose_name_plural = "Рабочие места"
        indexes = [
            models.Index(fields=["ip_address"], name="core_workstation_ip_idx"),
            models.Index(fields=["is_active"], name="core_workstation_active_idx"),
        ]

    def __str__(self) -> str:
        return self.label or self.hostname or self.ip_address


class UserIPRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ip_records",
        verbose_name="Пользователь",
    )
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    first_seen_at = models.DateTimeField(auto_now_add=True, verbose_name="Первое посещение")
    last_seen_at = models.DateTimeField(auto_now=True, verbose_name="Последнее посещение")
    last_path = models.CharField(
        max_length=512,
        blank=True,
        verbose_name="Последний путь",
    )
    last_method = models.CharField(
        max_length=12,
        blank=True,
        verbose_name="Последний метод",
    )
    last_user_agent = models.TextField(blank=True, verbose_name="User-Agent")
    last_download_path = models.CharField(
        max_length=512,
        blank=True,
        verbose_name="Последняя загрузка",
    )
    last_download_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последняя загрузка (время)",
    )

    class Meta:
        verbose_name = "IP пользователя"
        verbose_name_plural = "IP пользователей"
        constraints = [
            models.UniqueConstraint(fields=["user", "ip_address"], name="core_user_ip_unique"),
        ]
        indexes = [
            models.Index(fields=["user"], name="core_user_ip_user_idx"),
            models.Index(fields=["ip_address"], name="core_user_ip_ip_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.ip_address}"


class DeniedIPAttempt(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    attempted_path = models.CharField(
        max_length=512,
        blank=True,
        verbose_name="Запрошенный путь",
    )
    attempted_method = models.CharField(
        max_length=12,
        blank=True,
        verbose_name="HTTP метод",
    )
    user_agent = models.TextField(blank=True, verbose_name="User-Agent")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Причина")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    class Meta:
        verbose_name = "Заблокированный IP"
        verbose_name_plural = "Заблокированные IP"
        indexes = [
            models.Index(fields=["ip_address"], name="core_denied_ip_idx"),
            models.Index(fields=["created_at"], name="core_denied_ip_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.ip_address} ({self.created_at:%Y-%m-%d %H:%M:%S})"


class AppInventory(models.Model):
    app_name = models.CharField(max_length=255, unique=True, verbose_name="Полное имя приложения")
    app_label = models.CharField(max_length=100, verbose_name="Ярлык приложения")
    app_path = models.CharField(max_length=512, verbose_name="Путь приложения")
    file_hashes = models.JSONField(default=dict, verbose_name="Хеши файлов")
    aggregate_hash = models.CharField(max_length=64, verbose_name="Сводный хеш")
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="Первичное обнаружение")
    last_seen_at = models.DateTimeField(auto_now=True, verbose_name="Последнее обнаружение")
    last_changed_at = models.DateTimeField(null=True, blank=True, verbose_name="Последнее изменение")
    missing_since = models.DateTimeField(null=True, blank=True, verbose_name="Отсутствует с")

    class Meta:
        verbose_name = "Инвентаризация приложения"
        verbose_name_plural = "Инвентаризация приложений"
        indexes = [
            models.Index(fields=["app_name"], name="core_app_inv_name_idx"),
            models.Index(fields=["missing_since"], name="core_app_inv_missing_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.app_label} ({self.app_name})"
