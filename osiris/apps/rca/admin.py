from django.contrib import admin

from osiris.apps.rca import models


@admin.register(models.Org)
class OrgAdmin(admin.ModelAdmin):
    list_display = ("code", "created_at")
    search_fields = ("code",)


@admin.register(models.OrgVersion)
class OrgVersionAdmin(admin.ModelAdmin):
    list_display = ("org", "name", "valid_from", "valid_to", "is_current")
    list_filter = ("is_current",)
    search_fields = ("org__code", "name")


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("code", "created_at")
    search_fields = ("code",)


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
