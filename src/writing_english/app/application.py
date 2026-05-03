from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from writing_english.app.constants import (
    APP_NAME,
    APP_DATA_DIR,
    LOGS_DIR,
    DOCUMENTS_DIR,
    AUTOSAVE_DIR,
)
from writing_english.app.context import AppContext
from writing_english.config.settings import Settings
from writing_english.infrastructure.database import Database
from writing_english.infrastructure.filesystem import FileSystem
from writing_english.infrastructure.recent_files import RecentFiles


def bootstrap_app() -> QApplication:
    _ensure_dirs()
    _ensure_logs_dir()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)

    return app


def bootstrap_context() -> AppContext:
    settings = Settings()
    database = Database(APP_DATA_DIR / "app.db")
    database.initialize()
    filesystem = FileSystem()
    recent_files = RecentFiles(database)
    return AppContext(
        settings=settings,
        database=database,
        filesystem=filesystem,
        recent_files=recent_files,
        documents_dir=DOCUMENTS_DIR,
    )


def _ensure_dirs() -> None:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    AUTOSAVE_DIR.mkdir(parents=True, exist_ok=True)
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_logs_dir() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
