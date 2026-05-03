from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from writing_english.config.settings import Settings
from writing_english.infrastructure.database import Database
from writing_english.infrastructure.filesystem import FileSystem
from writing_english.infrastructure.recent_files import RecentFiles


@dataclass
class AppContext:
    settings: Settings
    database: Database
    filesystem: FileSystem
    recent_files: RecentFiles
    documents_dir: Path = field(default=Path.home() / "Documents" / "Writing English")
