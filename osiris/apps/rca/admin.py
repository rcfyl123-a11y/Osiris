"""osiris.apps.rca.admin — конфигурация админки для RCA."""

from django.contrib import admin
from django.db.models import Prefetch

from osiris.apps.rca import models


def get_current_version(obj, related_name: str = "versions", cache_attr: str = "current_versions"):
    """Вернуть актуальную версию объекта, используя кеш префетча при наличии."""
    cached = getattr(obj, cache_attr, None)
    if cached:
        return cached[0]
    return getattr(obj, related_name).filter(is_current=True).first()


@admin.register(models.Org)
class OrgAdmin(admin.ModelAdmin):
    """Настройки админки для организационных единиц."""

    fields = (
        "code",
        "current_name",
        "current_full_name",
        "current_parent_code",
        "current_is_top",
        "created_at",
    )
    list_display = (
        "code",
        "current_name",
        "current_full_name",
        "current_parent_code",
        "current_is_top",
        "created_at",
    )
    readonly_fields = (
        "code",
        "current_name",
        "current_full_name",
        "current_parent_code",
        "current_is_top",
        "created_at",
    )
    search_fields = ("code", "versions__name", "versions__full_name", "versions__parent_code")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            Prefetch(
                "versions",
                queryset=models.OrgVersion.objects.filter(is_current=True),
                to_attr="current_versions",
            )
        )

    @admin.display(description="Название")
    def current_name(self, obj):
        current = get_current_version(obj)
        return current.name if current else "-"

    @admin.display(description="Полное наименование")
    def current_full_name(self, obj):
        current = get_current_version(obj)
        return current.full_name if current else "-"

    @admin.display(description="Код родительской орг.единицы")
    def current_parent_code(self, obj):
        current = get_current_version(obj)
        return current.parent_code if current else "-"

    @admin.display(description="Вершина")
    def current_is_top(self, obj):
        current = get_current_version(obj)
        return current.is_top if current else "-"


@admin.register(models.OrgVersion)
class OrgVersionAdmin(admin.ModelAdmin):
    """Настройки админки для версий орг. единиц."""

    list_display = ("org", "name", "valid_from", "valid_to", "is_current")
    list_filter = ("is_current",)
    search_fields = ("org__code", "name")


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    """Настройки админки для должностей."""

    list_display = ("code", "current_name", "created_at")
    search_fields = ("code", "versions__name")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            Prefetch(
                "versions",
                queryset=models.PostVersion.objects.filter(is_current=True),
                to_attr="current_versions",
            )
        )

    @admin.display(description="Наименование")
    def current_name(self, obj):
        current = get_current_version(obj)
        return current.name if current else "-"


@admin.register(models.PostVersion)
class PostVersionAdmin(admin.ModelAdmin):
    """Настройки админки для версий должностей."""

    list_display = ("post", "name", "valid_from", "valid_to", "is_current")
    list_filter = ("is_current",)
    search_fields = ("post__code", "name")


@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Настройки админки для сотрудников."""

    list_display = (
        "snils_norm",
        "tab_norm_current",
        "last_name",
        "first_name",
        "is_fired_current",
    )
    list_filter = ("is_fired_current",)
    search_fields = ("snils_norm", "tab_norm_current", "last_name", "first_name")


@admin.register(models.EmployeeSnapshot)
class EmployeeSnapshotAdmin(admin.ModelAdmin):
    """Настройки админки для снимков сотрудников."""

    list_display = (
        "employee",
        "org",
        "post",
        "state",
        "valid_from",
        "valid_to",
        "is_current",
    )
    list_filter = ("is_current", "state")
    search_fields = ("employee__snils_norm", "employee__tab_norm_current")


@admin.register(models.VacationPeriod)
class VacationPeriodAdmin(admin.ModelAdmin):
    """Настройки админки для периодов отпусков."""

    list_display = ("employee", "start", "end")
    search_fields = ("employee__snils_norm", "employee__tab_norm_current")


@admin.register(models.ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    """Настройки админки для пакетов импорта."""

    list_display = ("set_date", "set_hash", "imported_at")
    search_fields = ("set_date", "set_hash")
