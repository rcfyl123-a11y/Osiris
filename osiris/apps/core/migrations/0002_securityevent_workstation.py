from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SecurityEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("DENIED_PERIMETER", "Denied (perimeter)"),
                            ("DENIED_BIND", "Denied (bind)"),
                            ("BIND_MISMATCH", "Bind mismatch"),
                            ("LOGIN_NEW_IP", "Login from new IP"),
                            ("FILE_DOWNLOAD", "File download"),
                            ("SENSITIVE_ACTION", "Sensitive action"),
                        ],
                        max_length=32,
                        verbose_name="Тип события",
                    ),
                ),
                ("ip_address", models.GenericIPAddressField(verbose_name="IP-адрес")),
                ("path", models.CharField(blank=True, max_length=512, verbose_name="Путь")),
                ("method", models.CharField(blank=True, max_length=12, verbose_name="Метод")),
                (
                    "status_code",
                    models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="HTTP статус"),
                ),
                ("user_agent", models.CharField(blank=True, max_length=255, verbose_name="User-Agent")),
                ("reason", models.CharField(blank=True, max_length=255, verbose_name="Причина")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Время")),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="security_events",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Security событие",
                "verbose_name_plural": "Security события",
                "indexes": [
                    models.Index(fields=["created_at"], name="core_sec_event_created_idx"),
                    models.Index(fields=["ip_address"], name="core_sec_event_ip_idx"),
                    models.Index(fields=["user"], name="core_sec_event_user_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Workstation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ip_address", models.GenericIPAddressField(unique=True, verbose_name="IP-адрес")),
                ("hostname", models.CharField(blank=True, max_length=255, verbose_name="Имя хоста")),
                ("label", models.CharField(blank=True, max_length=255, verbose_name="Метка")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("department", models.CharField(blank=True, max_length=255, verbose_name="Подразделение")),
                ("location", models.CharField(blank=True, max_length=255, verbose_name="Локация")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
                (
                    "allowed_users",
                    models.ManyToManyField(
                        blank=True,
                        related_name="allowed_workstations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Разрешенные пользователи",
                    ),
                ),
            ],
            options={
                "verbose_name": "Рабочее место",
                "verbose_name_plural": "Рабочие места",
                "indexes": [
                    models.Index(fields=["ip_address"], name="core_workstation_ip_idx"),
                    models.Index(fields=["is_active"], name="core_workstation_active_idx"),
                ],
            },
        ),
    ]
