import hashlib
import os
from dataclasses import dataclass

from django.apps import apps as django_apps
from django.db import transaction
from django.utils import timezone

from .models import AppInventory, AppInventoryHistory


@dataclass(frozen=True)
class AppInventoryChange:
    app_name: str
    app_label: str
    status: str
    details: str


def _iter_app_files(app_path: str) -> list[str]:
    file_paths: list[str] = []
    for root, dirs, files in os.walk(app_path):
        dirs[:] = [
            directory
            for directory in dirs
            if directory not in {"__pycache__", ".git", ".pytest_cache"}
            and not directory.startswith(".")
        ]
        for filename in files:
            if filename.endswith((".pyc", ".pyo")) or filename == ".DS_Store":
                continue
            file_paths.append(os.path.join(root, filename))
    return file_paths


def _hash_file(file_path: str) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _build_file_hashes(app_path: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for file_path in _iter_app_files(app_path):
        relative_path = os.path.relpath(file_path, app_path)
        hashes[relative_path] = _hash_file(file_path)
    return hashes


def _aggregate_hash(file_hashes: dict[str, str]) -> str:
    hasher = hashlib.sha256()
    for file_path in sorted(file_hashes):
        hasher.update(file_path.encode("utf-8"))
        hasher.update(b":")
        hasher.update(file_hashes[file_path].encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def _diff_file_hashes(old_hashes: dict[str, str], new_hashes: dict[str, str]) -> list[dict[str, str | None]]:
    changes: list[dict[str, str | None]] = []
    all_paths = set(old_hashes) | set(new_hashes)
    for path in sorted(all_paths):
        old_hash = old_hashes.get(path)
        new_hash = new_hashes.get(path)
        if old_hash is None and new_hash is not None:
            changes.append(
                {
                    "path": path,
                    "change": "added",
                    "old_hash": None,
                    "new_hash": new_hash,
                }
            )
        elif old_hash is not None and new_hash is None:
            changes.append(
                {
                    "path": path,
                    "change": "removed",
                    "old_hash": old_hash,
                    "new_hash": None,
                }
            )
        elif old_hash != new_hash:
            changes.append(
                {
                    "path": path,
                    "change": "modified",
                    "old_hash": old_hash,
                    "new_hash": new_hash,
                }
            )
    return changes


def _summarize_changes(changes: list[dict[str, str | None]]) -> str:
    added = sum(1 for change in changes if change["change"] == "added")
    removed = sum(1 for change in changes if change["change"] == "removed")
    modified = sum(1 for change in changes if change["change"] == "modified")
    return f"Изменения файлов: +{added} / ~{modified} / -{removed}."


def audit_app_inventory() -> list[AppInventoryChange]:
    changes: list[AppInventoryChange] = []
    now = timezone.now()
    osiris_apps = {
        app_config.name: app_config
        for app_config in django_apps.get_app_configs()
        if app_config.name.startswith("osiris.apps.")
    }
    existing = {entry.app_name: entry for entry in AppInventory.objects.all()}

    with transaction.atomic():
        for app_name, app_config in osiris_apps.items():
            file_hashes = _build_file_hashes(app_config.path)
            aggregate_hash = _aggregate_hash(file_hashes)
            entry = existing.get(app_name)
            if entry is None:
                entry = AppInventory(
                    app_name=app_name,
                    app_label=app_config.label,
                    app_path=app_config.path,
                    file_hashes=file_hashes,
                    aggregate_hash=aggregate_hash,
                    last_changed_at=now,
                )
                entry.save()
                AppInventoryHistory.objects.create(
                    app_inventory=entry,
                    status=AppInventoryHistory.Status.NEW,
                    summary="Обнаружено новое приложение.",
                    changed_files=_diff_file_hashes({}, file_hashes),
                    changed_at=now,
                )
                changes.append(
                    AppInventoryChange(
                        app_name=app_name,
                        app_label=app_config.label,
                        status="new",
                        details="Обнаружено новое приложение.",
                    )
                )
                continue

            status = "unchanged"
            was_missing = entry.missing_since is not None
            if entry.aggregate_hash != aggregate_hash:
                file_changes = _diff_file_hashes(entry.file_hashes, file_hashes)
                summary = _summarize_changes(file_changes) if file_changes else "Изменены файлы приложения."
                AppInventoryHistory.objects.create(
                    app_inventory=entry,
                    status=AppInventoryHistory.Status.CHANGED,
                    summary=summary,
                    changed_files=file_changes,
                    changed_at=now,
                )
                status = "changed"
                entry.last_changed_at = now
                changes.append(
                    AppInventoryChange(
                        app_name=app_name,
                        app_label=app_config.label,
                        status="changed",
                        details="Изменились файлы приложения.",
                    )
                )

            entry.app_label = app_config.label
            entry.app_path = app_config.path
            entry.file_hashes = file_hashes
            entry.aggregate_hash = aggregate_hash
            entry.missing_since = None
            entry.save()

            if was_missing:
                AppInventoryHistory.objects.create(
                    app_inventory=entry,
                    status=AppInventoryHistory.Status.RESTORED,
                    summary="Приложение снова обнаружено в конфигурации.",
                    changed_files=[],
                    changed_at=now,
                )

            if status == "unchanged":
                changes.append(
                    AppInventoryChange(
                        app_name=app_name,
                        app_label=app_config.label,
                        status="unchanged",
                        details="Изменений не обнаружено.",
                    )
                )

        for app_name, entry in existing.items():
            if app_name in osiris_apps:
                continue
            if entry.missing_since is None:
                entry.missing_since = now
                entry.save(update_fields=["missing_since"])
                AppInventoryHistory.objects.create(
                    app_inventory=entry,
                    status=AppInventoryHistory.Status.MISSING,
                    summary="Приложение отсутствует в текущей конфигурации.",
                    changed_files=[],
                    changed_at=now,
                )
            changes.append(
                AppInventoryChange(
                    app_name=entry.app_name,
                    app_label=entry.app_label,
                    status="missing",
                    details="Приложение отсутствует в текущей конфигурации.",
                )
            )

    return changes
