from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_securityevent_workstation"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppInventory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("app_name", models.CharField(max_length=255, unique=True, verbose_name="Полное имя приложения")),
                ("app_label", models.CharField(max_length=100, verbose_name="Ярлык приложения")),
                ("app_path", models.CharField(max_length=512, verbose_name="Путь приложения")),
                ("file_hashes", models.JSONField(default=dict, verbose_name="Хеши файлов")),
                ("aggregate_hash", models.CharField(max_length=64, verbose_name="Сводный хеш")),
                ("recorded_at", models.DateTimeField(auto_now_add=True, verbose_name="Первичное обнаружение")),
                ("last_seen_at", models.DateTimeField(auto_now=True, verbose_name="Последнее обнаружение")),
                ("last_changed_at", models.DateTimeField(blank=True, null=True, verbose_name="Последнее изменение")),
                ("missing_since", models.DateTimeField(blank=True, null=True, verbose_name="Отсутствует с")),
            ],
            options={
                "verbose_name": "Инвентаризация приложения",
                "verbose_name_plural": "Инвентаризация приложений",
                "indexes": [
                    models.Index(fields=["app_name"], name="core_app_inv_name_idx"),
                    models.Index(fields=["missing_since"], name="core_app_inv_missing_idx"),
                ],
            },
        ),
    ]
