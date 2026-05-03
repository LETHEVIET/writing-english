from pathlib import Path

APP_NAME = "Writing English"
APP_VERSION = "0.1.0"
ORG_NAME = "WritingEnglish"

DOCUMENTS_DIR = Path.home() / "Documents" / "Writing English"
AUTOSAVE_DIR = DOCUMENTS_DIR / ".autosave"
APP_DATA_DIR = Path.home() / ".local" / "share" / "writing_english"
LOGS_DIR = APP_DATA_DIR / "logs"
DB_PATH = APP_DATA_DIR / "app.db"
SETTINGS_PATH = APP_DATA_DIR / "settings.ini"

AUTOSAVE_INTERVAL_MS = 30_000
MAX_RECENT_FILES = 10

DEFAULT_FONT_FAMILY = "JetBrains Mono, Fira Code, Consolas, monospace"
DEFAULT_FONT_SIZE = 14
DEFAULT_LINE_HEIGHT = 1.6
DEFAULT_WORD_WRAP = True
DEFAULT_SHOW_LINE_NUMBERS = False
DEFAULT_THEME = "light"
