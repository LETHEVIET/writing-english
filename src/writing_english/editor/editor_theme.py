from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorColors:
    background: str
    text: str
    prompt_bg: str
    status_bg: str
    accent: str
    line_number: str
    cursor: str


LIGHT_THEME = EditorColors(
    background="#FAFAFA",
    text="#1A1A1A",
    prompt_bg="#F0F0F0",
    status_bg="#EAEAEA",
    accent="#B4D7FF",
    line_number="#C0C0C0",
    cursor="#1A1A1A",
)

DARK_THEME = EditorColors(
    background="#1E1E1E",
    text="#D4D4D4",
    prompt_bg="#252526",
    status_bg="#2D2D30",
    accent="#264F78",
    line_number="#6E6E6E",
    cursor="#D4D4D4",
)


def get_colors(theme_name: str) -> EditorColors:
    if theme_name == "dark":
        return DARK_THEME
    return LIGHT_THEME
