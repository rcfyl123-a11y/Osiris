from pathlib import Path

from osiris.config.discovery import discover_apps


def test_discover_apps_returns_known_apps():
    apps_dir = Path(__file__).resolve().parents[1] / "apps"
    labels = [app.label for app in discover_apps(apps_dir=apps_dir)]

    assert "accounts" in labels
    assert "blog" in labels
    assert "rca" in labels
