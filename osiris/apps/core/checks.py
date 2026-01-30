from django.core.checks import Info, Warning, register
from django.db.utils import OperationalError, ProgrammingError

from .app_inventory import audit_app_inventory


@register()
def app_inventory_check(app_configs, **kwargs):
    try:
        changes = audit_app_inventory()
    except (OperationalError, ProgrammingError) as exc:
        return [
            Warning(
                "Невозможно проверить инвентаризацию приложений.",
                hint="Убедитесь, что миграции core применены и база данных доступна.",
                obj=str(exc),
                id="core.W001",
            )
        ]

    messages = []
    for change in changes:
        if change.status == "new":
            messages.append(
                Info(
                    f"Приложение {change.app_label} ({change.app_name}) добавлено в инвентарь.",
                    hint="Хеши файлов сохранены для последующих проверок.",
                    id="core.I001",
                )
            )
        elif change.status == "changed":
            messages.append(
                Warning(
                    f"Приложение {change.app_label} ({change.app_name}) изменено.",
                    hint="Проверьте изменения файлов и корректность зависимостей.",
                    id="core.W002",
                )
            )
        elif change.status == "missing":
            messages.append(
                Warning(
                    f"Приложение {change.app_label} ({change.app_name}) отсутствует.",
                    hint="Проверьте, что отсутствие приложения не ломает зависимости.",
                    id="core.W003",
                )
            )
    return messages
