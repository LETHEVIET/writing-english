from __future__ import annotations

import re

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QTextDocument

_WORD_RE = re.compile(r"[A-Za-z']+")


class EditorHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument) -> None:
        super().__init__(parent)
        self._highlighting_rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._spell_check_enabled = False
        self._spell_checker: object | None = None
        self._spell_fmt = QTextCharFormat()
        self._spell_fmt.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SpellCheckUnderline
        )
        self._spell_fmt.setUnderlineColor(QColor("#E06C75"))

    def set_spell_check(self, enabled: bool) -> None:
        if enabled and self._spell_checker is None:
            from spellchecker import SpellChecker  # type: ignore[import-untyped]

            self._spell_checker = SpellChecker()
        self._spell_check_enabled = enabled
        self.rehighlight()

    def set_gec_highlight(self, start: int, length: int, color: QColor) -> None:
        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        fmt.setUnderlineColor(color)
        rule = (QRegularExpression(".{0}"), fmt)
        self._highlighting_rules.append(rule)

    def highlightBlock(self, text: str) -> None:
        if not self._spell_check_enabled or self._spell_checker is None:
            return
        checker = self._spell_checker  # type: ignore[attr-defined]
        for m in _WORD_RE.finditer(text):
            word = m.group()
            if word in checker.unknown([word]):
                self.setFormat(m.start(), len(word), self._spell_fmt)
