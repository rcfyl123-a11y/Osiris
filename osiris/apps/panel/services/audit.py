from __future__ import annotations

from django.utils import timezone

from osiris.apps.core.models import SecurityEvent


def record_panel_view(request, *, action: str, status_code: int) -> None:
    """Записать просмотр страницы панели в SecurityEvent."""
    user = request.user if request.user.is_authenticated else None
    ip_address = request.META.get("REMOTE_ADDR") or "0.0.0.0"
    user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:255]

    SecurityEvent.objects.create(
        event_type=SecurityEvent.EventType.PANEL_VIEW,
        user=user,
        ip_address=ip_address,
        path=request.path,
        method=request.method,
        status_code=status_code,
        user_agent=user_agent,
        reason=action,
        created_at=timezone.now(),
    )
