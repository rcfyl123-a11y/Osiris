import ipaddress
import logging
import time
from dataclasses import dataclass
from typing import Iterable

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils import timezone


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IPSettings:
    mode: str
    allowlist: list[ipaddress._BaseNetwork]
    trusted_proxies: list[ipaddress._BaseNetwork]
    trust_xff: bool
    fail_closed_empty_allowlist: bool
    exempt_paths: tuple[str, ...]
    apply_to_static_media: bool
    record_throttle_seconds: int
    bind_enforce: bool
    download_require_auth: bool
    download_require_bind: bool
    download_paths: tuple[str, ...]


def _parse_networks(values: Iterable[str]) -> list[ipaddress._BaseNetwork]:
    networks: list[ipaddress._BaseNetwork] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        try:
            networks.append(ipaddress.ip_network(cleaned, strict=False))
        except ValueError:
            logger.warning("Invalid network entry '%s'", cleaned)
    return networks


def _normalize_paths(values: Iterable[str]) -> tuple[str, ...]:
    paths = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        if not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        paths.append(cleaned)
    return tuple(paths)


def _get_setting_list(value: str | Iterable[str]) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [item.strip() for item in value if item.strip()]


def _resolve_settings() -> IPSettings:
    mode = getattr(settings, "IP_MODE", "audit").lower()
    if mode not in {"audit", "perimeter", "bind"}:
        logger.warning("Unknown IP mode '%s', fallback to audit", mode)
        mode = "audit"

    allowlist = _parse_networks(_get_setting_list(getattr(settings, "IP_ALLOWLIST", [])))
    trusted_proxies = _parse_networks(_get_setting_list(getattr(settings, "IP_TRUSTED_PROXIES", [])))

    return IPSettings(
        mode=mode,
        allowlist=allowlist,
        trusted_proxies=trusted_proxies,
        trust_xff=bool(getattr(settings, "IP_TRUST_X_FORWARDED_FOR", False)),
        fail_closed_empty_allowlist=bool(getattr(settings, "IP_FAIL_CLOSED_EMPTY_ALLOWLIST", False)),
        exempt_paths=_normalize_paths(getattr(settings, "IP_EXEMPT_PATHS", [])),
        apply_to_static_media=bool(getattr(settings, "IP_APPLY_TO_STATIC_MEDIA", True)),
        record_throttle_seconds=int(getattr(settings, "IP_RECORD_THROTTLE_SECONDS", 60)),
        bind_enforce=bool(getattr(settings, "IP_BIND_ENFORCE", True)),
        download_require_auth=bool(getattr(settings, "DOWNLOAD_REQUIRE_AUTH", False)),
        download_require_bind=bool(getattr(settings, "DOWNLOAD_REQUIRE_BIND", False)),
        download_paths=_normalize_paths(getattr(settings, "DOWNLOAD_PATHS", [])),
    )


def _ip_in_networks(ip_address: str | None, networks: list[ipaddress._BaseNetwork]) -> bool:
    if not ip_address:
        return False
    try:
        ip_obj = ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    return any(ip_obj in network for network in networks)


def _extract_forwarded_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        return first or None
    real_ip = request.META.get("HTTP_X_REAL_IP")
    return real_ip.strip() if real_ip else None


def resolve_client_ip(request, trusted_proxies: list[ipaddress._BaseNetwork], trust_xff: bool) -> str | None:
    """
    IP resolution priority:
    1) REMOTE_ADDR if no trusted proxy match or proxy trust disabled.
    2) If REMOTE_ADDR belongs to trusted proxies AND trust_xff enabled,
       use first IP from X-Forwarded-For, otherwise X-Real-IP.
    """
    remote_addr = request.META.get("REMOTE_ADDR")
    if not remote_addr:
        return None
    if trust_xff and trusted_proxies and _ip_in_networks(remote_addr, trusted_proxies):
        forwarded = _extract_forwarded_ip(request)
        if forwarded:
            try:
                ipaddress.ip_address(forwarded)
            except ValueError:
                return remote_addr
            return forwarded
    return remote_addr


def _is_path_exempt(path: str, exempt_paths: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in exempt_paths)


def _truncate(value: str | None, max_len: int) -> str:
    if not value:
        return ""
    return value[:max_len]


def _download_filename(disposition: str) -> str:
    if "filename=" not in disposition:
        return ""
    _, _, remainder = disposition.partition("filename=")
    return _truncate(remainder.strip('"\' '), 120)


class IPAllowlistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.settings = _resolve_settings()
        if self.settings.mode in {"perimeter", "bind"} and not self.settings.allowlist:
            logger.warning("IP allowlist is empty; mode=%s", self.settings.mode)
        if self.settings.trust_xff and not self.settings.trusted_proxies:
            logger.warning("X-Forwarded-For trust enabled but trusted proxies are empty")

    def __call__(self, request):
        path = request.path
        if _is_path_exempt(path, self._exempt_paths(request)):
            return self.get_response(request)

        client_ip = resolve_client_ip(request, self.settings.trusted_proxies, self.settings.trust_xff)
        if self.settings.allowlist and not _ip_in_networks(client_ip, self.settings.allowlist):
            self._record_event(
                event_type="DENIED_PERIMETER",
                request=request,
                ip_address=client_ip,
                reason="IP not in allowlist",
                status_code=403 if self.settings.mode != "audit" else None,
                throttle_key="perimeter",
            )
            if self.settings.mode != "audit":
                return HttpResponseForbidden("Доступ запрещен: IP-адрес не разрешен")
        elif not self.settings.allowlist and self.settings.mode in {"perimeter", "bind"}:
            if self.settings.fail_closed_empty_allowlist:
                self._record_event(
                    event_type="DENIED_PERIMETER",
                    request=request,
                    ip_address=client_ip,
                    reason="Empty allowlist (fail-closed)",
                    status_code=403,
                    throttle_key="empty_allowlist",
                )
                return HttpResponseForbidden("Доступ запрещен: IP-адрес не разрешен")

        user = getattr(request, "user", None)
        is_authenticated = bool(user and user.is_authenticated)
        if self.settings.mode == "bind" and is_authenticated:
            if not self._is_user_bound(user, client_ip):
                if self.settings.bind_enforce:
                    self._record_event(
                        event_type="DENIED_BIND",
                        request=request,
                        ip_address=client_ip,
                        user=user,
                        reason="User not bound to workstation",
                        status_code=403,
                        throttle_key="bind",
                    )
                    return HttpResponseForbidden("Доступ запрещен: рабочее место не разрешено")
                self._record_event(
                    event_type="BIND_MISMATCH",
                    request=request,
                    ip_address=client_ip,
                    user=user,
                    reason="User not bound to workstation",
                )

        if self._is_download_path(path) and not self._check_download_access(request, is_authenticated, user, client_ip):
            return HttpResponseForbidden("Доступ к скачиванию запрещен")

        response = self.get_response(request)

        response = self._handle_download_response(request, response, is_authenticated, user, client_ip)
        self._record_user_ip(request, response, client_ip, user, is_authenticated)

        return response

    def _exempt_paths(self, request) -> tuple[str, ...]:
        paths = list(self.settings.exempt_paths)
        if not self.settings.apply_to_static_media:
            static_url = getattr(settings, "STATIC_URL", "/static/") or "/static/"
            media_url = getattr(settings, "MEDIA_URL", "/media/") or "/media/"
            paths.extend([static_url, media_url])
        return tuple(paths)

    def _is_user_bound(self, user, client_ip: str | None) -> bool:
        if not client_ip:
            return False
        model = apps.get_model("core", "Workstation")
        if not model:
            return False
        return model.objects.filter(
            ip_address=client_ip,
            is_active=True,
            allowed_users=user,
        ).exists()

    def _is_download_path(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.settings.download_paths)

    def _check_download_access(self, request, is_authenticated: bool, user, client_ip: str | None) -> bool:
        if self.settings.download_require_auth and not is_authenticated:
            self._record_event(
                event_type="DENIED_PERIMETER",
                request=request,
                ip_address=client_ip,
                user=user,
                reason="Download requires authentication",
                status_code=403,
                throttle_key="download_auth",
            )
            return False
        if self.settings.download_require_bind and self.settings.mode == "bind" and is_authenticated:
            if not self._is_user_bound(user, client_ip):
                self._record_event(
                    event_type="DENIED_BIND",
                    request=request,
                    ip_address=client_ip,
                    user=user,
                    reason="Download requires bind",
                    status_code=403,
                    throttle_key="download_bind",
                )
                return False
        return True

    def _handle_download_response(self, request, response, is_authenticated: bool, user, client_ip: str | None):
        disposition = response.get("Content-Disposition", "")
        is_attachment = "attachment" in disposition.lower()
        if is_attachment and not self._check_download_access(request, is_authenticated, user, client_ip):
            return HttpResponseForbidden("Доступ к скачиванию запрещен")

        is_download = response.status_code < 400 and (is_attachment or self._is_download_path(request.path))
        if is_download:
            self._record_event(
                event_type="FILE_DOWNLOAD",
                request=request,
                ip_address=client_ip,
                user=user if is_authenticated else None,
                reason=_download_filename(disposition),
                status_code=response.status_code,
            )
            self._update_download_record(request.path, client_ip, user, is_authenticated)
        return response

    def _record_user_ip(self, request, response, client_ip: str | None, user, is_authenticated: bool) -> None:
        if not client_ip or not is_authenticated:
            return

        model = apps.get_model("core", "UserIPRecord")
        if not model:
            return

        cache_key = f"core_ip_record:{user.pk}:{client_ip}"
        throttle = max(self.settings.record_throttle_seconds, 0)
        should_update = throttle == 0 or cache.add(cache_key, True, timeout=throttle)

        user_agent = request.META.get("HTTP_USER_AGENT", "")
        defaults = {
            "last_path": _truncate(request.path, 512),
            "last_method": _truncate(request.method, 12),
            "last_user_agent": _truncate(user_agent, 255),
        }
        record, created = model.objects.get_or_create(
            user=user,
            ip_address=client_ip,
            defaults=defaults,
        )

        if created:
            self._record_event(
                event_type="LOGIN_NEW_IP",
                request=request,
                ip_address=client_ip,
                user=user,
                status_code=response.status_code,
            )

        if not should_update and not created:
            return

        record.last_path = defaults["last_path"]
        record.last_method = defaults["last_method"]
        record.last_user_agent = defaults["last_user_agent"]
        record.save()

    def _update_download_record(self, path: str, client_ip: str | None, user, is_authenticated: bool) -> None:
        if not client_ip or not is_authenticated:
            return

        model = apps.get_model("core", "UserIPRecord")
        if not model:
            return

        try:
            record = model.objects.get(user=user, ip_address=client_ip)
        except model.DoesNotExist:
            return

        record.last_download_path = _truncate(path, 512)
        record.last_download_at = timezone.now()
        record.save(update_fields=["last_download_path", "last_download_at"])

    def _record_event(
        self,
        *,
        event_type: str,
        request,
        ip_address: str | None,
        reason: str = "",
        status_code: int | None = None,
        user=None,
        throttle_key: str | None = None,
    ) -> None:
        if not ip_address:
            ip_address = "0.0.0.0"

        if throttle_key and not self._allow_event(ip_address, request, reason, throttle_key):
            return

        model = apps.get_model("core", "SecurityEvent")
        if not model:
            return

        path = request.path if request is not None else ""
        method = request.method if request is not None else ""
        user_agent = request.META.get("HTTP_USER_AGENT") if request is not None else ""

        model.objects.create(
            event_type=event_type,
            user=user if user and getattr(user, "is_authenticated", False) else None,
            ip_address=ip_address,
            path=_truncate(path, 512),
            method=_truncate(method, 12),
            status_code=status_code,
            user_agent=_truncate(user_agent, 255),
            reason=_truncate(reason, 255),
        )

    @staticmethod
    def _allow_event(ip_address: str, request, reason: str, throttle_key: str) -> bool:
        path = request.path if request is not None else ""
        bucket = int(time.time() // 60)
        key = f"core_sec_event:{throttle_key}:{ip_address}:{path}:{reason}:{bucket}"
        return cache.add(key, True, timeout=60)
