"""Installed apps discovery for Osiris.

Path: osiris/config/settings/installed_apps.py
"""

import importlib
import logging
import pkgutil
from typing import Iterable

from django.apps import AppConfig

from .environment import ENABLE_DEBUG_TOOLBAR


logger = logging.getLogger(__name__)


DJANGO_CORE_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]


def _iter_osiris_app_names() -> Iterable[str]:
    """Yield osiris app package names from the apps namespace."""
    import osiris.apps

    return sorted(module.name for module in pkgutil.iter_modules(osiris.apps.__path__))


def _resolve_app_config(app_name: str) -> str | None:
    """Return the dotted path to an AppConfig subclass for a given app."""
    module_path = f"osiris.apps.{app_name}.apps"
    try:
        apps_module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        if exc.name == module_path:
            logger.warning("Missing apps.py for osiris app '%s'; skipping.", app_name)
            return None
        logger.warning(
            "Failed to import osiris app '%s' due to missing dependency: %s",
            app_name,
            exc,
        )
        return None
    except Exception as exc:  # noqa: BLE001 - log and skip faulty apps
        logger.warning("Failed to import osiris app '%s': %s", app_name, exc)
        return None

    candidates = []
    direct_config = getattr(apps_module, "AppConfig", None)
    if (
        isinstance(direct_config, type)
        and issubclass(direct_config, AppConfig)
        and direct_config is not AppConfig
    ):
        candidates.append(direct_config)

    for value in apps_module.__dict__.values():
        if (
            isinstance(value, type)
            and issubclass(value, AppConfig)
            and value is not AppConfig
        ):
            candidates.append(value)

    if not candidates:
        logger.warning(
            "No AppConfig subclass found in %s for osiris app '%s'; skipping.",
            module_path,
            app_name,
        )
        return None

    config_class = sorted(candidates, key=lambda cls: cls.__name__)[0]
    return f"{module_path}.{config_class.__name__}"


def _collect_osiris_apps() -> list[str]:
    """Collect AppConfig paths for osiris apps that can be imported."""
    configs = []
    for app_name in _iter_osiris_app_names():
        config_path = _resolve_app_config(app_name)
        if config_path:
            configs.append(config_path)
    return configs


INSTALLED_APPS = [
    *DJANGO_CORE_APPS,
    *_collect_osiris_apps(),
]

if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
