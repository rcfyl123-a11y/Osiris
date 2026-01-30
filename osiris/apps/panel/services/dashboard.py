from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from osiris.apps.core.models import DeniedIPAttempt, UserIPRecord


@dataclass(frozen=True)
class DashboardPeriod:
    key: str
    label: str
    delta: timedelta


PERIODS: dict[str, DashboardPeriod] = {
    "24h": DashboardPeriod(key="24h", label="Последние 24 часа", delta=timedelta(hours=24)),
    "7d": DashboardPeriod(key="7d", label="Последние 7 дней", delta=timedelta(days=7)),
}


def resolve_period(key: str | None) -> DashboardPeriod:
    """Выбрать период для метрик панели."""
    if not key:
        return PERIODS["24h"]
    return PERIODS.get(key, PERIODS["24h"])


def build_dashboard_context(period_key: str | None) -> dict[str, object]:
    """Собрать агрегаты для главной страницы панели."""
    period = resolve_period(period_key)
    since = timezone.now() - period.delta

    unique_ips = (
        UserIPRecord.objects.filter(last_seen_at__gte=since)
        .values("ip_address")
        .distinct()
        .count()
    )
    denied_count = DeniedIPAttempt.objects.filter(created_at__gte=since).count()
    top_denied = (
        DeniedIPAttempt.objects.filter(created_at__gte=since)
        .values("ip_address")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    recent_downloads = list(
        UserIPRecord.objects.filter(last_download_at__isnull=False)
        .select_related("user")
        .order_by("-last_download_at")
        .values(
            "user__username",
            "ip_address",
            "last_download_at",
            "last_download_path",
        )[:10]
    )

    recent_denied = list(
        DeniedIPAttempt.objects.order_by("-created_at").values(
            "ip_address",
            "attempted_path",
            "created_at",
        )[:10]
    )

    recent_events = [
        {
            "type": "download",
            "timestamp": item["last_download_at"],
            "ip_address": item["ip_address"],
            "path": item["last_download_path"],
            "username": item["user__username"],
        }
        for item in recent_downloads
    ] + [
        {
            "type": "denied",
            "timestamp": item["created_at"],
            "ip_address": item["ip_address"],
            "path": item["attempted_path"],
            "username": None,
        }
        for item in recent_denied
    ]
    recent_events = sorted(recent_events, key=lambda event: event["timestamp"], reverse=True)[:10]

    seven_days_ago = timezone.now() - timedelta(days=7)
    denied_by_day_raw = (
        DeniedIPAttempt.objects.filter(created_at__gte=seven_days_ago)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    denied_by_day = [
        {"day": row["day"], "total": row["total"]} for row in denied_by_day_raw
    ]

    return {
        "period": period,
        "unique_ips": unique_ips,
        "denied_count": denied_count,
        "top_denied": top_denied,
        "recent_events": recent_events,
        "denied_by_day": denied_by_day,
    }
