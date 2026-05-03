from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from writing_english.adapters.gec.gector_adapter import GectorAdapter


class GecWorker(QThread):
    results_ready = Signal(str, list)
    error_occurred = Signal(str)

    def __init__(self, adapter: GectorAdapter, text: str) -> None:
        super().__init__()
        self._adapter = adapter
        self._text = text

    def run(self) -> None:
        try:
            errors = self._adapter.check(self._text)
            self.results_ready.emit(self._text, errors)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
