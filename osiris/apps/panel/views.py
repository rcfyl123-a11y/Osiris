from __future__ import annotations

from datetime import datetime, time, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.generic import ListView, TemplateView

from osiris.apps.core.models import DeniedIPAttempt, UserIPRecord

from .services.audit import record_panel_view
from .services.dashboard import build_dashboard_context


class PanelStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ограничение доступа только для staff-пользователей."""

    def test_func(self) -> bool:
        return bool(self.request.user.is_staff)

    def handle_no_permission(self) -> HttpResponse:
        if self.request.user.is_authenticated:
            return render(self.request, "panel/403.html", status=403)
        return super().handle_no_permission()


class PanelCorePermissionMixin(PermissionRequiredMixin, PanelStaffRequiredMixin):
    """Ограничение доступа к security-разделам панели."""

    permission_required = "panel.core_security_view"

    def handle_no_permission(self) -> HttpResponse:
        if self.request.user.is_authenticated:
            return render(self.request, "panel/403.html", status=403)
        return super().handle_no_permission()


class PanelUsersPermissionMixin(PermissionRequiredMixin, PanelStaffRequiredMixin):
    """Ограничение доступа к управлению пользователями."""

    permission_required = "panel.core_users_manage"

    def handle_no_permission(self) -> HttpResponse:
        if self.request.user.is_authenticated:
            return render(self.request, "panel/403.html", status=403)
        return super().handle_no_permission()


class PanelAuditMixin:
    """Логирование просмотров страниц панели."""

    audit_action = "view"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated and request.user.is_staff and response.status_code < 400:
            record_panel_view(request, action=self.audit_action, status_code=response.status_code)
        return response


class PanelDashboardView(PanelAuditMixin, PanelStaffRequiredMixin, TemplateView):
    template_name = "panel/dashboard.html"
    audit_action = "dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period_key = self.request.GET.get("period")
        context.update(build_dashboard_context(period_key))
        return context


class PanelIPRecordListView(PanelAuditMixin, PanelCorePermissionMixin, ListView):
    template_name = "panel/core/ip_records.html"
    context_object_name = "records"
    paginate_by = 25
    audit_action = "core_ip_records"

    def get_queryset(self):
        queryset = UserIPRecord.objects.select_related("user").order_by("-last_seen_at")
        user_query = self.request.GET.get("user")
        ip_query = self.request.GET.get("ip")
        active_hours = self.request.GET.get("active_hours")

        if user_query:
            queryset = queryset.filter(user__username__icontains=user_query)
        if ip_query:
            queryset = queryset.filter(ip_address__icontains=ip_query)
        if active_hours:
            try:
                hours = int(active_hours)
            except ValueError:
                hours = None
            if hours:
                since = timezone.now() - timedelta(hours=hours)
                queryset = queryset.filter(last_seen_at__gte=since)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filters"] = {
            "user": self.request.GET.get("user", ""),
            "ip": self.request.GET.get("ip", ""),
            "active_hours": self.request.GET.get("active_hours", ""),
        }
        context["query_string"] = _build_query_string(self.request.GET)
        return context


class PanelDeniedListView(PanelAuditMixin, PanelCorePermissionMixin, ListView):
    template_name = "panel/core/denied.html"
    context_object_name = "attempts"
    paginate_by = 25
    audit_action = "core_denied"

    def get_queryset(self):
        queryset = DeniedIPAttempt.objects.order_by("-created_at")
        ip_query = self.request.GET.get("ip")
        path_query = self.request.GET.get("path")
        from_date = self.request.GET.get("from")
        to_date = self.request.GET.get("to")
        recent_hours = self.request.GET.get("hours")

        if ip_query:
            queryset = queryset.filter(ip_address__icontains=ip_query)
        if path_query:
            queryset = queryset.filter(attempted_path__icontains=path_query)

        since = _parse_since_value(recent_hours)
        if since:
            queryset = queryset.filter(created_at__gte=since)

        start, end = _parse_date_range(from_date, to_date)
        if start:
            queryset = queryset.filter(created_at__gte=start)
        if end:
            queryset = queryset.filter(created_at__lte=end)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filters"] = {
            "ip": self.request.GET.get("ip", ""),
            "path": self.request.GET.get("path", ""),
            "from": self.request.GET.get("from", ""),
            "to": self.request.GET.get("to", ""),
            "hours": self.request.GET.get("hours", ""),
        }
        context["query_string"] = _build_query_string(self.request.GET)
        return context


class PanelStatusView(PanelAuditMixin, PanelCorePermissionMixin, TemplateView):
    template_name = "panel/core/status.html"
    audit_action = "core_status"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allowlist = list(getattr(settings, "IP_ALLOWLIST", []))
        trusted_proxies = list(getattr(settings, "IP_TRUSTED_PROXIES", []))
        ip_mode = getattr(settings, "IP_MODE", "audit")
        trust_xff = bool(getattr(settings, "IP_TRUST_X_FORWARDED_FOR", False))
        fail_closed = bool(getattr(settings, "IP_FAIL_CLOSED_EMPTY_ALLOWLIST", False))

        warnings: list[str] = []
        if ip_mode in {"perimeter", "bind"} and not allowlist:
            warnings.append("Allowlist пуста: режим perimeter/bind работает без периметра.")
        if trust_xff and not trusted_proxies:
            warnings.append("Trust X-Forwarded-For включён, но trusted_proxies не настроены.")
        if ip_mode == "bind" and not getattr(settings, "IP_BIND_ENFORCE", True):
            warnings.append("IP_BIND_ENFORCE отключён при режиме bind.")

        context.update(
            {
                "status_items": [
                    {
                        "label": "IP_MODE",
                        "value": ip_mode,
                        "description": "Режим работы фильтрации IP (audit/perimeter/bind).",
                    },
                    {
                        "label": "IP_ALLOWLIST",
                        "value": ", ".join(allowlist) or "—",
                        "description": "Список разрешённых IP/подсетей для доступа.",
                    },
                    {
                        "label": "IP_TRUST_X_FORWARDED_FOR",
                        "value": "Да" if trust_xff else "Нет",
                        "description": "Доверять заголовку X-Forwarded-For от прокси.",
                    },
                    {
                        "label": "IP_TRUSTED_PROXIES",
                        "value": ", ".join(trusted_proxies) or "—",
                        "description": "Список доверенных прокси, через которые приходит трафик.",
                    },
                    {
                        "label": "IP_FAIL_CLOSED_EMPTY_ALLOWLIST",
                        "value": "Да" if fail_closed else "Нет",
                        "description": "Блокировать всех при пустом allowlist.",
                    },
                    {
                        "label": "IP_EXEMPT_PATHS",
                        "value": ", ".join(getattr(settings, "IP_EXEMPT_PATHS", []))
                        or "—",
                        "description": "Маршруты, исключённые из проверки IP.",
                    },
                    {
                        "label": "IP_APPLY_TO_STATIC_MEDIA",
                        "value": "Да" if getattr(settings, "IP_APPLY_TO_STATIC_MEDIA", True) else "Нет",
                        "description": "Применять фильтрацию к статике и медиа.",
                    },
                    {
                        "label": "IP_RECORD_THROTTLE_SECONDS",
                        "value": getattr(settings, "IP_RECORD_THROTTLE_SECONDS", 60),
                        "description": "Пауза между фиксацией повторных IP-событий.",
                    },
                    {
                        "label": "IP_BIND_ENFORCE",
                        "value": "Да" if getattr(settings, "IP_BIND_ENFORCE", True) else "Нет",
                        "description": "Жёстко привязывать пользователя к IP.",
                    },
                ],
                "warnings": warnings,
            }
        )
        return context


class PanelUsersView(PanelAuditMixin, PanelUsersPermissionMixin, TemplateView):
    template_name = "panel/core/users.html"
    audit_action = "core_users"

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        action = request.POST.get("action")
        User = get_user_model()

        if action == "create":
            username = (request.POST.get("username") or "").strip()
            email = (request.POST.get("email") or "").strip()
            password = (request.POST.get("password") or "").strip()
            role = request.POST.get("role", "user")
            group_ids = request.POST.getlist("groups")

            if not username or not password:
                messages.error(request, "Укажите имя пользователя и пароль.")
                return redirect("panel:users")
            if User.objects.filter(username=username).exists():
                messages.error(request, "Пользователь с таким именем уже существует.")
                return redirect("panel:users")

            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_staff = role in {"staff", "superuser"}
            user.is_superuser = role == "superuser"
            user.save(update_fields=["is_staff", "is_superuser"])
            if group_ids:
                groups = Group.objects.filter(id__in=group_ids)
                user.groups.set(groups)
            messages.success(request, "Пользователь создан.")
            return redirect("panel:users")

        user_id = request.POST.get("user_id")
        if not user_id:
            messages.error(request, "Не указан пользователь для действия.")
            return redirect("panel:users")

        target_user = get_object_or_404(User, pk=user_id)

        if action == "delete":
            if target_user == request.user:
                messages.error(request, "Нельзя удалить собственный аккаунт.")
            else:
                target_user.delete()
                messages.success(request, "Пользователь удалён.")
            return redirect("panel:users")

        if action == "toggle_active":
            if target_user == request.user:
                messages.error(request, "Нельзя деактивировать собственный аккаунт.")
            else:
                target_user.is_active = not target_user.is_active
                target_user.save(update_fields=["is_active"])
                messages.success(request, "Статус активности обновлён.")
            return redirect("panel:users")

        if action == "set_staff":
            target_user.is_staff = True
            target_user.save(update_fields=["is_staff"])
            messages.success(request, "Роль staff назначена.")
            return redirect("panel:users")

        if action == "unset_staff":
            if target_user == request.user and target_user.is_superuser:
                messages.error(request, "Нельзя убрать staff у собственного суперпользователя.")
            else:
                target_user.is_staff = False
                target_user.save(update_fields=["is_staff"])
                messages.success(request, "Роль staff снята.")
            return redirect("panel:users")

        if action == "set_superuser":
            target_user.is_superuser = True
            target_user.is_staff = True
            target_user.save(update_fields=["is_superuser", "is_staff"])
            messages.success(request, "Назначен суперпользователь.")
            return redirect("panel:users")

        if action == "unset_superuser":
            if target_user == request.user:
                messages.error(request, "Нельзя снять суперпользователя у себя.")
            else:
                target_user.is_superuser = False
                target_user.save(update_fields=["is_superuser"])
                messages.success(request, "Суперпользователь снят.")
            return redirect("panel:users")

        if action == "update_groups":
            group_ids = request.POST.getlist("groups")
            groups = Group.objects.filter(id__in=group_ids)
            target_user.groups.set(groups)
            messages.success(request, "Роли (группы) обновлены.")
            return redirect("panel:users")

        messages.error(request, "Неизвестное действие.")
        return redirect("panel:users")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context.update(
            {
                "users": User.objects.prefetch_related("groups").order_by("username"),
                "groups": Group.objects.order_by("name"),
            }
        )
        return context


def panel_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Показать аккуратную 404 страницу для панели."""
    if request.path.startswith("/panel/"):
        return render(request, "panel/404.html", status=404)
    return render(request, "404.html", status=404)


def _build_query_string(params) -> str:
    query_params = {
        key: value
        for key, value in params.items()
        if key != "page" and value not in (None, "")
    }
    return urlencode(query_params)


def _parse_since_value(raw_hours: str | None) -> datetime | None:
    if not raw_hours:
        return None
    try:
        hours = int(raw_hours)
    except ValueError:
        return None
    if hours <= 0:
        return None
    return timezone.now() - timedelta(hours=hours)


def _parse_date_range(raw_start: str | None, raw_end: str | None):
    start_dt = _parse_date_value(raw_start, is_start=True)
    end_dt = _parse_date_value(raw_end, is_start=False)
    return start_dt, end_dt


def _parse_date_value(raw_value: str | None, *, is_start: bool) -> datetime | None:
    if not raw_value:
        return None
    parsed_dt = parse_datetime(raw_value)
    if parsed_dt:
        if timezone.is_naive(parsed_dt):
            return timezone.make_aware(parsed_dt)
        return parsed_dt
    parsed_date = parse_date(raw_value)
    if not parsed_date:
        return None
    bound_time = time.min if is_start else time.max
    return timezone.make_aware(datetime.combine(parsed_date, bound_time))
