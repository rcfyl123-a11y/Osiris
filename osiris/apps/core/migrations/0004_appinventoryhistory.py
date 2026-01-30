from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_appinventory"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppInventoryHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("new", "Новое"), ("changed", "Изменено"), ("missing", "Отсутствует"), ("restored", "Восстановлено")], max_length=20, verbose_name="Статус")),
                ("summary", models.CharField(max_length=255, verbose_name="Описание")),
                ("changed_files", models.JSONField(default=list, verbose_name="Изменённые файлы")),
                ("changed_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Время изменения")),
                ("app_inventory", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="history", to="core.appinventory", verbose_name="Инвентаризация приложения")),
            ],
            options={
                "verbose_name": "История приложения",
                "verbose_name_plural": "История приложений",
                "indexes": [
                    models.Index(fields=["changed_at"], name="core_app_hist_changed_idx"),
                    models.Index(fields=["status"], name="core_app_hist_status_idx"),
                ],
            },
        ),
    ]
