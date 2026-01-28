from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional


FIRE_SENTINEL = date(9999, 12, 31)


def parse_ddmmyyyy(value: str | None) -> Optional[date]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    return datetime.strptime(value, "%d.%m.%Y").date()


def norm_tab_id(raw: str | None) -> tuple[Optional[str], Optional[str]]:
    if raw is None:
        return None, None
    raw_clean = raw.strip()
    if not raw_clean:
        return None, None
    norm = re.sub(r"\s+", "", raw_clean).upper()
    return raw_clean, (norm or None)


def norm_snils(raw: str | None) -> tuple[Optional[str], Optional[str]]:
    if raw is None:
        return None, None
    raw_clean = raw.strip()
    if not raw_clean:
        return None, None
    digits = re.sub(r"\D+", "", raw_clean)
    norm = digits if len(digits) == 11 else None
    return raw_clean, norm


def norm_text(value: str | None) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def is_fired(fire_date: Optional[date]) -> bool:
    if fire_date is None:
        return False
    return fire_date != FIRE_SENTINEL


def to_iso(value: Optional[date]) -> str:
    return value.isoformat() if value else ""
