from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPlainTextEdit


MIN_PROMPT_HEIGHT = 40
MAX_PROMPT_HEIGHT = 400


class PromptBar(QWidget):
    prompt_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("promptBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 6, 28, 6)
        layout.setSpacing(10)

        self._label = QLabel("Prompt")
        self._label.setObjectName("promptBarLabel")
        label_font = QFont()
        label_font.setPointSize(10)
        label_font.setCapitalization(QFont.Capitalization.AllUppercase)
        label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        label_font.setBold(True)
        self._label.setFont(label_font)
        self._label.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._input = QPlainTextEdit()
        self._input.setObjectName("promptBarInput")
        self._input.setPlaceholderText("Set a writing prompt…")
        self._input.setFrameStyle(0)
        self._input.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self._input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._input.setMaximumHeight(MAX_PROMPT_HEIGHT)
        self._input.setMinimumHeight(MIN_PROMPT_HEIGHT)
        self._input.textChanged.connect(self._on_text_changed)

        layout.addWidget(self._label)
        layout.addWidget(self._input, 1)

        self._on_text_changed()

    def _on_text_changed(self) -> None:
        text = self._input.toPlainText()
        self.prompt_changed.emit(text)
        doc = self._input.document()
        line_count = doc.lineCount()
        line_height = self._input.fontMetrics().lineSpacing()
        content_height = line_count * line_height + 8
        height = min(MAX_PROMPT_HEIGHT, max(MIN_PROMPT_HEIGHT, content_height))
        self._input.setFixedHeight(height)
        self.setFixedHeight(height + 16)

    def set_prompt(self, prompt: str | None) -> None:
        self._input.blockSignals(True)
        self._input.setPlainText(prompt or "")
        self._input.blockSignals(False)
        self._on_text_changed()

    def clear_prompt(self) -> None:
        self.set_prompt(None)

    def focus_input(self) -> None:
        self._input.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self._input.selectAll()

    def current_prompt(self) -> str:
        return self._input.toPlainText()
