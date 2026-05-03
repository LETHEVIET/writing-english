from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication


def _parse_rgb(rgb_str: str) -> str | None:
    parts = rgb_str.split(",")
    if len(parts) != 3:
        return None
    try:
        r, g, b = (int(p.strip()) for p in parts)
    except ValueError:
        return None
    return f"#{r:02X}{g:02X}{b:02X}"


def _read_kde_wm_colors() -> tuple[str | None, str | None]:
    """Returns (active_bg, active_fg) from KDE's kdeglobals [WM] section."""
    config_path = Path.home() / ".config" / "kdeglobals"
    if not config_path.exists():
        return (None, None)

    active_bg: str | None = None
    active_fg: str | None = None

    in_wm_section = False
    try:
        with open(config_path) as f:
            for raw in f:
                line = raw.strip()
                if line == "[WM]":
                    in_wm_section = True
                    continue
                if in_wm_section:
                    if line.startswith("[") and line.endswith("]"):
                        break
                    if line.startswith("activeBackground="):
                        active_bg = _parse_rgb(line.split("=", 1)[1])
                    elif line.startswith("activeForeground="):
                        active_fg = _parse_rgb(line.split("=", 1)[1])
    except OSError:
        pass

    return (active_bg, active_fg)


def get_system_theme() -> str:
    app = QGuiApplication.instance()
    if app is not None:
        if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            return "dark"
    return "light"


def get_chrome_colors(theme: str) -> tuple[str, str]:
    if theme == "dark":
        return ("#2A2E32", "#EFF0F1")
    bg, fg = _read_kde_wm_colors()
    if bg and fg:
        return (bg, fg)
    return ("palette(window)", "palette(windowText)")
