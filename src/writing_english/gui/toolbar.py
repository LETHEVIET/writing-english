from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar, QPushButton, QWidget


class Toolbar(QToolBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Main Toolbar", parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setObjectName("mainToolbar")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setIconSize(self.iconSize())
        self.setContentsMargins(0, 0, 0, 0)

        self.new_btn = self._make_button("New")
        self.open_btn = self._make_button("Open")
        self.save_btn = self._make_button("Save")
        self.save_as_btn = self._make_button("Save As")
        self.undo_btn = self._make_button("Undo")
        self.redo_btn = self._make_button("Redo")
        self.prompt_btn = self._make_button("Prompt")

        self.addWidget(self.new_btn)
        self.addWidget(self.open_btn)
        self.addWidget(self.save_btn)
        self.addWidget(self.save_as_btn)
        self.addSeparator()
        self.addWidget(self.undo_btn)
        self.addWidget(self.redo_btn)
        self.addSeparator()
        self.addWidget(self.prompt_btn)

    def _make_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFlat(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("toolbarButton", True)
        return btn
