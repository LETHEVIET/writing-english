from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget


class FocusModeOverlay(QWidget):
    exit_focus = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.hide()

    def enter_focus_mode(self) -> None:
        self.show()

    def exit_focus_mode(self) -> None:
        self.hide()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape or event.key() == Qt.Key.Key_F11:
            self.exit_focus.emit()
        super().keyPressEvent(event)
