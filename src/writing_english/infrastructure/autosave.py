from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import QTimer, QObject, Signal

from writing_english.app.constants import AUTOSAVE_DIR
from writing_english.core.document import Document


class AutosaveManager(QObject):
    autosaved = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)
        self._document: Document | None = None
        self._interval_ms = 30_000

    def start(self, interval_ms: int = 30_000) -> None:
        self._interval_ms = interval_ms
        self._timer.start(interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def set_document(self, document: Document | None) -> None:
        self._document = document

    def set_interval(self, interval_ms: int) -> None:
        self._interval_ms = interval_ms
        if self._timer.isActive():
            self._timer.setInterval(interval_ms)

    def _on_timer(self) -> None:
        if self._document is None:
            return
        if not self._document.is_modified:
            return
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        name = f"{self._document.display_name}_{timestamp}.md"
        path = AUTOSAVE_DIR / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._document.serialize(), encoding="utf-8")
        self.autosaved.emit(str(path))
