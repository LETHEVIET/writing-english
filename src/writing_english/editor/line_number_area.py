from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QFont, QPalette
from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from writing_english.editor.editor_widget import EditorWidget


class LineNumberArea(QWidget):
    def __init__(self, editor: EditorWidget) -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        bg = self._editor.palette().color(QPalette.ColorRole.AlternateBase)
        fg = self._editor.palette().color(QPalette.ColorRole.Mid)
        painter.fillRect(event.rect(), bg)

        block = self._editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self._editor.blockBoundingGeometry(block)
            .translated(self._editor.contentOffset())
            .top()
        )
        bottom = top + round(self._editor.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(fg)
                font = QFont(self._editor.font())
                editor_ps = self._editor.font().pointSize()
                if editor_ps > 0:
                    font.setPointSize(editor_ps - 1)
                painter.setFont(font)
                fm = painter.fontMetrics()
                painter.drawText(
                    0,
                    top,
                    self.width() - 4,
                    fm.height(),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self._editor.blockBoundingRect(block).height())
            block_number += 1
