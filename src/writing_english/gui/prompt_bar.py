from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPlainTextEdit

from writing_english.editor.editor_widget import EDITOR_SIDE_PADDING


MIN_PROMPT_HEIGHT = 40
MAX_PROMPT_LINES = 5


class PromptBar(QWidget):
    prompt_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("promptBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(10)

        self._input = QPlainTextEdit()
        self._input.setObjectName("promptBarInput")
        self._input.setPlaceholderText("Set a writing prompt…")
        self._input.setFrameStyle(0)
        self._input.setViewportMargins(EDITOR_SIDE_PADDING, 0, EDITOR_SIDE_PADDING, 0)
        self._input.document().setDocumentMargin(16)
        self._input.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self._input.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self._input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._input.setMinimumHeight(MIN_PROMPT_HEIGHT)
        self._input.textChanged.connect(self._schedule_update)
        self._input.textChanged.connect(self._on_text_changed)

        layout.addWidget(self._input, 1)

        # Defer first calculation until after layout is known
        QTimer.singleShot(0, self._update_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_update()

    def _schedule_update(self):
        # Defer to next event loop so we're outside any active layout pass
        QTimer.singleShot(0, self._update_height)

    def _update_height(self) -> None:
        doc = self._input.document()
        layout = doc.documentLayout()

        # Sum the exact bounding rect of every laid-out block
        total = 0.0
        block = doc.begin()
        while block.isValid():
            total += layout.blockBoundingRect(block).height()
            block = block.next()

        margin = doc.documentMargin()
        doc_h = total + margin * 2
        line_h = self._input.fontMetrics().lineSpacing()
        max_doc_h = MAX_PROMPT_LINES * line_h + margin * 2

        # +8 for QSS padding (4px top + 4px bottom)
        input_h = max(MIN_PROMPT_HEIGHT, min(int(doc_h) + 8, int(max_doc_h) + 8))
        bar_h = input_h + 12  # 6+6 layout margins

        if self.height() == bar_h:
            return

        self.setFixedHeight(bar_h)

        # Force our internal layout to give the input the new height
        self.layout().invalidate()  # type: ignore[union-attr]
        self.layout().activate()  # type: ignore[union-attr]

        # Force the MainWindow layout to reallocate space
        main = self.parent()
        if main is not None and main.layout() is not None:  # type: ignore[attr-defined]
            main.layout().invalidate()  # type: ignore[attr-defined]
            main.layout().activate()  # type: ignore[attr-defined]

    def _on_text_changed(self) -> None:
        self.prompt_changed.emit(self._input.toPlainText())

    def set_prompt(self, prompt: str | None) -> None:
        self._input.blockSignals(True)
        self._input.setPlainText(prompt or "")
        self._input.blockSignals(False)
        self._schedule_update()

    def clear_prompt(self) -> None:
        self.set_prompt(None)

    def focus_input(self) -> None:
        self._input.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self._input.selectAll()

    def current_prompt(self) -> str:
        return self._input.toPlainText()
