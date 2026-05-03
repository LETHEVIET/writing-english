"""KDE Breeze-inspired color palettes."""

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
    spell_underline: str
    gec_underline: str


LIGHT_THEME = EditorColors(
    background="#FFFFFF",
    text="#232629",
    prompt_bg="#F8F8F8",
    status_bg="#EAEAEA",
    accent="#3DAEE9",
    line_number="#A4A4A4",
    cursor="#232629",
    spell_underline="#DA4453",
    gec_underline="#F67400",
)

DARK_THEME = EditorColors(
    background="#232629",
    text="#EFF0F1",
    prompt_bg="#2A2E32",
    status_bg="#2A2E32",
    accent="#3DAEE9",
    line_number="#7A7C7F",
    cursor="#EFF0F1",
    spell_underline="#DA4453",
    gec_underline="#F67400",
)


def get_colors(theme_name: str) -> EditorColors:
    if theme_name == "dark":
        return DARK_THEME
    return LIGHT_THEME
