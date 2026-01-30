"""Debug Toolbar configuration for Osiris.

Path: osiris/config/settings/debug_toolbar.py
"""

from .environment import DEBUG


def _show_toolbar(request) -> bool:
    """Return True when the debug toolbar should be visible."""
    return DEBUG

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": _show_toolbar,  # Показывать только в DEBUG режиме
    "SHOW_COLLAPSED": True,  # Свернутая панель
}
