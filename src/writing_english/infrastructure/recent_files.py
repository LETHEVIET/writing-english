from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from writing_english.app.constants import MAX_RECENT_FILES
from writing_english.infrastructure.database import Database


@dataclass
class RecentFileEntry:
    path: str
    display_name: str
    last_opened: datetime
    id: Optional[int] = None


class RecentFiles:
    def __init__(self, database: Database) -> None:
        self._db = database

    def add(self, file_path: Path) -> None:
        conn = self._db.connection
        display = file_path.stem
        conn.execute(
            "INSERT OR REPLACE INTO recent_files (path, display_name, last_opened) "
            "VALUES (?, ?, CURRENT_TIMESTAMP)",
            (str(file_path), display),
        )
        self._trim()
        conn.commit()

    def _trim(self) -> None:
        conn = self._db.connection
        conn.execute(
            f"DELETE FROM recent_files WHERE id NOT IN ("
            f"SELECT id FROM recent_files ORDER BY last_opened DESC LIMIT {MAX_RECENT_FILES})"
        )

    def list(self) -> list[RecentFileEntry]:
        conn = self._db.connection
        rows = conn.execute(
            "SELECT id, path, display_name, last_opened FROM recent_files ORDER BY last_opened DESC"
        ).fetchall()
        return [
            RecentFileEntry(
                id=row[0],
                path=row[1],
                display_name=row[2],
                last_opened=datetime.fromisoformat(row[3])
                if isinstance(row[3], str)
                else datetime.min,
            )
            for row in rows
        ]

    def remove(self, file_path: Path) -> None:
        conn = self._db.connection
        conn.execute("DELETE FROM recent_files WHERE path = ?", (str(file_path),))
        conn.commit()
