"""Конфигурация Debug Toolbar для Osiris.

Путь: osiris/config/settings/debug_toolbar.py
"""

from .environment import DEBUG


def _show_toolbar(request) -> bool:
    """Возвращает True, когда debug-панель должна отображаться."""
    return DEBUG

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": _show_toolbar,  # Показывать только в DEBUG режиме
    "SHOW_COLLAPSED": True,  # Свернутая панель
}
