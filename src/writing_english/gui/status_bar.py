from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QStatusBar, QLabel, QToolButton, QWidget

from writing_english.gui.icons import load_svg_icon

_BTN_SIZE = 24
_ICON_SIZE = 14


class StatusBarButton(QToolButton):
    """Square icon button for the status bar. All instances share QSS via objectName."""

    def __init__(
        self,
        icon_name: str,
        tooltip: str,
        checkable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("statusBarButton")
        self.setFixedSize(_BTN_SIZE, _BTN_SIZE)
        self.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        self.setIcon(load_svg_icon(icon_name))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Ensure tooltips show even when the status bar would otherwise suppress them
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)


class StatusBar(QStatusBar):
    spell_check_toggled = Signal(bool)
    grammar_check_triggered = Signal()
    typing_sounds_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizeGripEnabled(False)
        self.setFixedHeight(28)
        self.setContentsMargins(0, 0, 0, 0)

        self._buttons: dict[str, StatusBarButton] = {}

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

        # --- action buttons (add more here in the future) ---
        spell_btn = self._add_button(
            "spell_check", "spell-check", "Spell check", checkable=True
        )
        spell_btn.toggled.connect(self.spell_check_toggled)

        grammar_btn = self._add_button(
            "grammar_check", "grammar-check", "Grammar check", checkable=False
        )
        grammar_btn.clicked.connect(self.grammar_check_triggered)

        typing_sounds_btn = self._add_button(
            "typing_sounds", "volume-2", "Typing sounds", checkable=True
        )
        typing_sounds_btn.toggled.connect(self.typing_sounds_toggled)

        # --- stats / mode labels ---
        self.addPermanentWidget(self._words_label)
        self.addPermanentWidget(self._chars_label)
        self.addPermanentWidget(self._mode_label)

        self.addWidget(self._line_col_label)

    def _add_button(
        self, name: str, icon_name: str, tooltip: str, checkable: bool = False
    ) -> StatusBarButton:
        btn = StatusBarButton(icon_name, tooltip, checkable, self)
        self._buttons[name] = btn
        self.addPermanentWidget(btn)
        return btn

    def button(self, name: str) -> StatusBarButton | None:
        return self._buttons.get(name)

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------

    def update_cursor(self, line: int, col: int) -> None:
        self._line_col_label.setText(f"{line}:{col}")

    def update_stats(self, words: int, chars: int) -> None:
        self._words_label.setText(f"{words} words")
        self._chars_label.setText(f"{chars} chars")

    def set_overwrite_mode(self, enabled: bool) -> None:
        self._mode_label.setText("OVR" if enabled else "INSERT")

    def set_spell_check(self, enabled: bool) -> None:
        btn = self._buttons.get("spell_check")
        if btn is None:
            return
        btn.blockSignals(True)
        btn.setChecked(enabled)
        btn.blockSignals(False)

    def set_typing_sounds(self, enabled: bool) -> None:
        btn = self._buttons.get("typing_sounds")
        if btn is None:
            return
        btn.blockSignals(True)
        btn.setChecked(enabled)
        btn.blockSignals(False)

    def set_grammar_loading(self, loading: bool) -> None:
        btn = self._buttons.get("grammar_check")
        if btn is None:
            return
        btn.setEnabled(not loading)
        if loading:
            btn.setIcon(load_svg_icon("grammar-check", color="#F67400"))
            btn.setToolTip("Checking grammar...")
        else:
            btn.setIcon(load_svg_icon("grammar-check", color="#7A7C7F"))
            btn.setToolTip("Grammar check")
