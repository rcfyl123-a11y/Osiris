from django.contrib import admin
from django.db.models import Prefetch

from osiris.apps.rca import models


@admin.register(models.Org)
class OrgAdmin(admin.ModelAdmin):
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
        current = self._get_current_version(obj)
        return current.name if current else "-"

    @admin.display(description="Полное наименование")
    def current_full_name(self, obj):
        current = self._get_current_version(obj)
        return current.full_name if current else "-"

    @admin.display(description="Код родительской орг.единицы")
    def current_parent_code(self, obj):
        current = self._get_current_version(obj)
        return current.parent_code if current else "-"

    @admin.display(description="Вершина")
    def current_is_top(self, obj):
        current = self._get_current_version(obj)
        return current.is_top if current else "-"

    def _get_current_version(self, obj):
        if hasattr(obj, "current_versions") and obj.current_versions:
            return obj.current_versions[0]
        return obj.versions.filter(is_current=True).first()


@admin.register(models.OrgVersion)
class OrgVersionAdmin(admin.ModelAdmin):
    list_display = ("org", "name", "valid_from", "valid_to", "is_current")
    list_filter = ("is_current",)
    search_fields = ("org__code", "name")


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
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
        current = self._get_current_version(obj)
        return current.name if current else "-"

    def _get_current_version(self, obj):
        if hasattr(obj, "current_versions") and obj.current_versions:
            return obj.current_versions[0]
        return obj.versions.filter(is_current=True).first()


@admin.register(models.PostVersion)
class PostVersionAdmin(admin.ModelAdmin):
    list_display = ("post", "name", "valid_from", "valid_to", "is_current")
    list_filter = ("is_current",)
    search_fields = ("post__code", "name")


@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
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
    list_display = ("employee", "start", "end")
    search_fields = ("employee__snils_norm", "employee__tab_norm_current")


@admin.register(models.ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ("set_date", "set_hash", "imported_at")
    search_fields = ("set_date", "set_hash")
