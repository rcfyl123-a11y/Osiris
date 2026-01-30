from django.contrib import admin

from .models import DeniedIPAttempt, SecurityEvent, UserIPRecord, Workstation


@admin.register(UserIPRecord)
class UserIPRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "last_seen_at", "last_path", "last_download_at")
    list_filter = ("ip_address", "last_seen_at")
    search_fields = ("user__username", "ip_address", "last_path")


@admin.register(DeniedIPAttempt)
class DeniedIPAttemptAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "attempted_path", "attempted_method", "created_at")
    list_filter = ("ip_address", "created_at")
    search_fields = ("ip_address", "attempted_path", "user_agent")


@admin.register(Workstation)
class WorkstationAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "hostname", "is_active", "allowed_users_count", "label")
    list_filter = ("is_active",)
    search_fields = ("ip_address", "hostname", "label")
    filter_horizontal = ("allowed_users",)

    @admin.display(description="Пользователи")
    def allowed_users_count(self, obj):
        return obj.allowed_users.count()

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("allowed_users")


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "ip_address", "user", "path", "created_at")
    list_filter = ("event_type", "created_at", "ip_address")
    search_fields = ("ip_address", "user__username", "path", "reason")
