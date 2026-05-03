from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QTextDocument


class EditorHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument) -> None:
        super().__init__(parent)
        self._highlighting_rules: list[tuple[QRegularExpression, QTextCharFormat]] = []

    def set_gec_highlight(self, start: int, length: int, color: QColor) -> None:
        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        fmt.setUnderlineColor(color)
        rule = (QRegularExpression(".{0}"), fmt)
        self._highlighting_rules.append(rule)

    def highlightBlock(self, text: str) -> None:
        pass
