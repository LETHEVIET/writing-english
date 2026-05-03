from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStatusBar, QLabel, QWidget


class StatusBar(QStatusBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizeGripEnabled(False)
        self.setFixedHeight(28)
        self.setContentsMargins(0, 0, 0, 0)

        self._line_col_label = QLabel("1:1")
        self._words_label = QLabel("0 words")
        self._chars_label = QLabel("0 chars")
        self._mode_label = QLabel("INSERT")

        self._line_col_label.setObjectName("statusLineCol")
        self._words_label.setObjectName("statusWords")
        self._chars_label.setObjectName("statusChars")
        self._mode_label.setObjectName("statusMode")

        for lbl in (
            self._line_col_label,
            self._words_label,
            self._chars_label,
            self._mode_label,
        ):
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.addWidget(self._line_col_label)
        self.addPermanentWidget(self._words_label)
        self.addPermanentWidget(self._chars_label)
        self.addPermanentWidget(self._mode_label)

    def update_cursor(self, line: int, col: int) -> None:
        self._line_col_label.setText(f"{line}:{col}")

    def update_stats(self, words: int, chars: int) -> None:
        self._words_label.setText(f"{words} words")
        self._chars_label.setText(f"{chars} chars")

    def set_overwrite_mode(self, enabled: bool) -> None:
        self._mode_label.setText("OVR" if enabled else "INSERT")
