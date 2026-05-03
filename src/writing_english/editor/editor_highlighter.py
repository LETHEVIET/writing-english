from __future__ import annotations

import re
from typing import Any

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QTextDocument

from writing_english.adapters.base import GECError

_WORD_RE = re.compile(r"[A-Za-z']+")


class EditorHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument) -> None:
        super().__init__(parent)
        self._highlighting_rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._spell_check_enabled = False
        self._spell_checker: Any | None = None
        self._spell_fmt = QTextCharFormat()
        self._spell_fmt.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SpellCheckUnderline
        )
        self._spell_fmt.setUnderlineColor(QColor("#DA4453"))

        self._gec_enabled = False
        self._gec_errors: list[GECError] = []
        self._gec_fmt = QTextCharFormat()
        self._gec_fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        self._gec_fmt.setUnderlineColor(QColor("#F67400"))

    def set_spell_check(self, enabled: bool) -> None:
        if enabled and self._spell_checker is None:
            from spellchecker import SpellChecker

            self._spell_checker = SpellChecker()
        self._spell_check_enabled = enabled
        self.rehighlight()

    def set_spell_enabled_color(self, color: str) -> None:
        self._spell_fmt.setUnderlineColor(QColor(color))
        self.rehighlight()

    def set_gec_enabled(self, enabled: bool) -> None:
        self._gec_enabled = enabled
        if not enabled:
            self._gec_errors = []
        self.rehighlight()

    def set_gec_underline_color(self, color: str) -> None:
        self._gec_fmt.setUnderlineColor(QColor(color))
        self.rehighlight()

    def set_gec_errors(self, errors: list[GECError]) -> None:
        self._gec_errors = errors
        self.rehighlight()

    def clear_gec_errors(self) -> None:
        self._gec_errors = []
        self.rehighlight()

    @property
    def gec_errors(self) -> list[GECError]:
        return self._gec_errors

    def highlightBlock(self, text: str) -> None:
        if self._spell_check_enabled and self._spell_checker is not None:
            checker = self._spell_checker
            for m in _WORD_RE.finditer(text):
                word = m.group()
                if word in checker.unknown([word]):
                    self.setFormat(m.start(), len(word), self._spell_fmt)

        if self._gec_enabled:
            block_pos = self.currentBlock().position()
            block_end = block_pos + len(text)
            for err in self._gec_errors:
                err_start = err["start"]
                err_end = err_start + err["length"]
                if err_end <= block_pos or err_start >= block_end:
                    continue
                rel_start = max(0, err_start - block_pos)
                rel_end = min(len(text), err_end - block_pos)
                self.setFormat(rel_start, rel_end - rel_start, self._gec_fmt)
