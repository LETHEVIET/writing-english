from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSettings

from writing_english.app.constants import SETTINGS_PATH
from writing_english.config.defaults import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    DEFAULT_LINE_HEIGHT,
    DEFAULT_WORD_WRAP,
    DEFAULT_SHOW_LINE_NUMBERS,
    DEFAULT_SPELL_CHECK,
    DEFAULT_THEME,
    DEFAULT_AUTOSAVE_INTERVAL_MS,
)


class Settings:
    def __init__(self) -> None:
        self._qsettings = QSettings(str(SETTINGS_PATH), QSettings.Format.IniFormat)

    @property
    def font_family(self) -> str:
        return str(self._get("editor/font_family", DEFAULT_FONT_FAMILY))

    @font_family.setter
    def font_family(self, value: str) -> None:
        self._set("editor/font_family", value)

    @property
    def font_size(self) -> int:
        return int(self._get("editor/font_size", DEFAULT_FONT_SIZE))

    @font_size.setter
    def font_size(self, value: int) -> None:
        self._set("editor/font_size", value)

    @property
    def line_height(self) -> float:
        return float(self._get("editor/line_height", DEFAULT_LINE_HEIGHT))

    @line_height.setter
    def line_height(self, value: float) -> None:
        self._set("editor/line_height", value)

    @property
    def word_wrap(self) -> bool:
        val = self._get("editor/word_wrap", DEFAULT_WORD_WRAP)
        return str(val).lower() in ("true", "1")

    @word_wrap.setter
    def word_wrap(self, value: bool) -> None:
        self._set("editor/word_wrap", value)

    @property
    def show_line_numbers(self) -> bool:
        val = self._get("editor/show_line_numbers", DEFAULT_SHOW_LINE_NUMBERS)
        return str(val).lower() in ("true", "1")

    @show_line_numbers.setter
    def show_line_numbers(self, value: bool) -> None:
        self._set("editor/show_line_numbers", value)

    @property
    def spell_check(self) -> bool:
        val = self._get("editor/spell_check", DEFAULT_SPELL_CHECK)
        return str(val).lower() in ("true", "1")

    @spell_check.setter
    def spell_check(self, value: bool) -> None:
        self._set("editor/spell_check", value)

    @property
    def theme(self) -> str:
        return str(self._get("appearance/theme", DEFAULT_THEME))

    @theme.setter
    def theme(self, value: str) -> None:
        self._set("appearance/theme", value)

    @property
    def autosave_interval_ms(self) -> int:
        return int(
            self._get("general/autosave_interval_ms", DEFAULT_AUTOSAVE_INTERVAL_MS)
        )

    @autosave_interval_ms.setter
    def autosave_interval_ms(self, value: int) -> None:
        self._set("general/autosave_interval_ms", value)

    def _get(self, key: str, default: Any) -> Any:
        return self._qsettings.value(key, default)

    def _set(self, key: str, value: Any) -> None:
        self._qsettings.setValue(key, value)

    def sync(self) -> None:
        self._qsettings.sync()
