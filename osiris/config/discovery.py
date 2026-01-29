"""Application and URL discovery helpers for Osiris."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Iterable

from django.apps import AppConfig


EXCLUDED_APP_DIRS = {
    "__pycache__",
    "migrations",
    "tests",
    "management",
    "static",
    "templates",
    "locale",
}


@dataclass(frozen=True)
class DiscoveredApp:
    label: str
    package: str
    config: str | None
    urls_module: str | None


def discover_apps(
    apps_dir: Path | None = None,
    base_package: str = "osiris.apps",
) -> list[DiscoveredApp]:
    """Discover Django apps in the given directory.

    An app is detected when the directory is a Python package or contains
    an ``apps.py`` module. The results are returned in a stable, sorted order.
    """

    base_dir = apps_dir or (Path(__file__).resolve().parent.parent / "apps")
    app_paths = _iter_app_paths(base_dir)

    discovered: list[DiscoveredApp] = []
    for app_path in app_paths:
        label = app_path.name
        package = f"{base_package}.{label}"
        config = _resolve_app_config(package, app_path)
        urls_module = f"{package}.urls" if (app_path / "urls.py").is_file() else None
        discovered.append(
            DiscoveredApp(
                label=label,
                package=package,
                config=config,
                urls_module=urls_module,
            )
        )

    return discovered


def discover_installed_apps(
    apps_dir: Path | None = None,
    base_package: str = "osiris.apps",
) -> list[str]:
    """Return INSTALLED_APPS entries for discovered apps."""

    apps = discover_apps(apps_dir=apps_dir, base_package=base_package)
    return [app.config or app.package for app in apps]


def _iter_app_paths(apps_dir: Path) -> list[Path]:
    if not apps_dir.exists():
        return []

    candidates: Iterable[Path] = (
        path
        for path in apps_dir.iterdir()
        if path.is_dir()
        and path.name not in EXCLUDED_APP_DIRS
        and not path.name.startswith(".")
    )

    app_paths: list[Path] = []
    for path in candidates:
        if _is_app_dir(path):
            app_paths.append(path)

    return sorted(app_paths, key=lambda item: item.name)


def _is_app_dir(path: Path) -> bool:
    return (path / "apps.py").is_file() or (path / "__init__.py").is_file()


def _resolve_app_config(package: str, app_path: Path) -> str | None:
    apps_module = app_path / "apps.py"
    if not apps_module.is_file():
        return None

    module_name = f"{package}.apps"
    try:
        module = import_module(module_name)
    except ImportError:
        return None

    config_classes = []
    for value in module.__dict__.values():
        if isinstance(value, type) and issubclass(value, AppConfig) and value is not AppConfig:
            config_classes.append(value)

    if not config_classes:
        return None

    config_classes.sort(key=lambda cls: cls.__name__)
    return f"{module_name}.{config_classes[0].__name__}"
