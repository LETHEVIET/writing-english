from pathlib import Path
import json

APP_NAME = "Writing English"
APP_VERSION = "0.1.1"
ORG_NAME = "WritingEnglish"

# XDG-style paths config lives outside the app data dir so it survives relocation.
_PATHS_CONFIG = Path.home() / ".config" / "writing_english" / "paths.json"


def _resolve_app_data_dir() -> Path:
    if _PATHS_CONFIG.exists():
        try:
            with open(_PATHS_CONFIG, encoding="utf-8") as f:
                data = json.load(f)
            override = data.get("app_data_dir")
            if override:
                return Path(override)
        except Exception:
            pass
    return Path.home() / ".local" / "share" / "writing_english"


APP_DATA_DIR = _resolve_app_data_dir()
SETTINGS_PATH = APP_DATA_DIR / "settings.ini"
LOGS_DIR = APP_DATA_DIR / "logs"
DB_PATH = APP_DATA_DIR / "app.db"

DOCUMENTS_DIR = Path.home() / "Documents" / "Writing English"
AUTOSAVE_DIR = DOCUMENTS_DIR / ".autosave"

AUTOSAVE_INTERVAL_MS = 30_000
MAX_RECENT_FILES = 10

GECTOR_ONNX_DIR = APP_DATA_DIR / "models" / "gector-onnx"

DEFAULT_FONT_FAMILY = "JetBrains Mono, Fira Code, Consolas, monospace"
DEFAULT_FONT_SIZE = 14
DEFAULT_LINE_HEIGHT = 1.6
DEFAULT_WORD_WRAP = True
DEFAULT_SHOW_LINE_NUMBERS = False
DEFAULT_THEME = "light"
