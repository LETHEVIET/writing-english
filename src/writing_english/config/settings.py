from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import QSettings

from writing_english.app.constants import APP_DATA_DIR, SETTINGS_PATH, _PATHS_CONFIG
from datetime import datetime, timezone

from writing_english.config.defaults import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    DEFAULT_LINE_HEIGHT,
    DEFAULT_WORD_WRAP,
    DEFAULT_SHOW_LINE_NUMBERS,
    DEFAULT_GECTOR_MODEL,
    DEFAULT_GECTOR_MODEL_DIR,
    DEFAULT_TYPING_SOUNDS,
    DEFAULT_TYPING_SOUND_PACK,
    DEFAULT_THEME,
    DEFAULT_AUTOSAVE_INTERVAL_MS,
    DEFAULT_STICKER_REWARDS,
    DEFAULT_STICKER_FOLDER,
    DEFAULT_CHECK_FOR_UPDATES,
)


class Settings:
    def __init__(self) -> None:
        self._qsettings = QSettings(str(SETTINGS_PATH), QSettings.Format.IniFormat)

    @property
    def app_data_dir(self) -> str:
        if _PATHS_CONFIG.exists():
            try:
                with open(_PATHS_CONFIG, encoding="utf-8") as f:
                    data = json.load(f)
                val = data.get("app_data_dir")
                if val:
                    return str(val)
            except Exception:
                pass
        return str(APP_DATA_DIR)

    @app_data_dir.setter
    def app_data_dir(self, value: str) -> None:
        _PATHS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, object] = {}
        if _PATHS_CONFIG.exists():
            try:
                with open(_PATHS_CONFIG, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        data["app_data_dir"] = value
        with open(_PATHS_CONFIG, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

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
    def typing_sounds(self) -> bool:
        val = self._get("editor/typing_sounds", DEFAULT_TYPING_SOUNDS)
        return str(val).lower() in ("true", "1")

    @typing_sounds.setter
    def typing_sounds(self, value: bool) -> None:
        self._set("editor/typing_sounds", value)

    @property
    def typing_sound_pack(self) -> str:
        return str(self._get("editor/typing_sound_pack", DEFAULT_TYPING_SOUND_PACK))

    @typing_sound_pack.setter
    def typing_sound_pack(self, value: str) -> None:
        self._set("editor/typing_sound_pack", value)

    @property
    def gector_model(self) -> str:
        return str(self._get("gector/model", DEFAULT_GECTOR_MODEL))

    @gector_model.setter
    def gector_model(self, value: str) -> None:
        self._set("gector/model", value)

    @property
    def gector_model_dir(self) -> str:
        return str(self._get("gector/model_dir", DEFAULT_GECTOR_MODEL_DIR))

    @gector_model_dir.setter
    def gector_model_dir(self, value: str) -> None:
        self._set("gector/model_dir", value)

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

    @property
    def sticker_rewards(self) -> bool:
        val = self._get("rewards/sticker_rewards", DEFAULT_STICKER_REWARDS)
        return str(val).lower() in ("true", "1")

    @sticker_rewards.setter
    def sticker_rewards(self, value: bool) -> None:
        self._set("rewards/sticker_rewards", value)

    @property
    def sticker_folder(self) -> str:
        return str(self._get("rewards/sticker_folder", DEFAULT_STICKER_FOLDER))

    @sticker_folder.setter
    def sticker_folder(self, value: str) -> None:
        self._set("rewards/sticker_folder", value)

    def _get(self, key: str, default: Any) -> Any:
        return self._qsettings.value(key, default)

    def _set(self, key: str, value: Any) -> None:
        self._qsettings.setValue(key, value)

    @property
    def check_for_updates(self) -> bool:
        val = self._get("general/check_for_updates", DEFAULT_CHECK_FOR_UPDATES)
        return str(val).lower() in ("true", "1")

    @check_for_updates.setter
    def check_for_updates(self, value: bool) -> None:
        self._set("general/check_for_updates", value)

    def get_last_update_check(self) -> datetime | None:
        ts = self._get("updater/last_check", None)
        if ts is None:
            return None
        try:
            return datetime.fromisoformat(str(ts))
        except ValueError, TypeError:
            return None

    def set_last_update_check(self, dt: datetime | None = None) -> None:
        if dt is None:
            dt = datetime.now(timezone.utc)
        self._set("updater/last_check", dt.isoformat())

    def sync(self) -> None:
        self._qsettings.sync()
