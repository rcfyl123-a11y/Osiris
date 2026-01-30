"""Утилиты для голосований."""

from osiris.apps.core.middleware import _resolve_settings, resolve_client_ip


def get_client_ip(request) -> str | None:
    settings = _resolve_settings()
    return resolve_client_ip(request, settings.trusted_proxies, settings.trust_xff)
