from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from writing_english.adapters.base import GECError
from writing_english.adapters.gec.gector_adapter import GectorAdapter
from writing_english.adapters.gec.worker import GecWorker
from writing_english.editor.editor_highlighter import EditorHighlighter
from writing_english.editor.editor_widget import EditorWidget


class GrammarCheckController(QObject):
    status_changed = Signal(str)
    check_started = Signal()
    check_finished = Signal()
    results_ready = Signal(list)  # list[GECError]

    def __init__(
        self,
        editor: EditorWidget,
        highlighter: EditorHighlighter,
        adapter: GectorAdapter,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._editor = editor
        self._highlighter = highlighter
        self._adapter = adapter
        self._worker: GecWorker | None = None
        self._pending_check_text: str = ""
        self._editor.document().contentsChange.connect(self._on_contents_change)

    def set_adapter(self, adapter: GectorAdapter) -> None:
        self._adapter = adapter

    def shutdown(self) -> None:
        if self._worker is not None:
            self._worker.wait(2000)

    def _on_contents_change(
        self, _pos: int, chars_removed: int, chars_added: int
    ) -> None:
        if chars_removed > 0 or chars_added > 0:
            self._highlighter.clear_gec_errors()

    def check_now(self) -> None:
        doc = self._editor.document()
        text = doc.toPlainText()
        if not text.strip():
            self._highlighter.clear_gec_errors()
            self._pending_check_text = ""
            return

        self._pending_check_text = text
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(5000)

        self.check_started.emit()
        self._highlighter.set_gec_enabled(True)
        self._worker = GecWorker(self._adapter, text)
        self._worker.results_ready.connect(self._on_results)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_results(self, text: str, errors: list[GECError]) -> None:
        self._highlighter.set_gec_errors(errors)
        self.results_ready.emit(errors)

    def _on_error(self, msg: str) -> None:
        self.status_changed.emit(f"Grammar check error: {msg}")

    def _on_worker_finished(self) -> None:
        self._worker = None
        self.check_finished.emit()
