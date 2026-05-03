from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import (
    QColor,
    QContextMenuEvent,
    QFont,
    QPalette,
    QResizeEvent,
    QKeyEvent,
    QTextCursor,
    QTextOption,
    QTextBlockFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from writing_english.adapters.base import GECError
from writing_english.editor.editor_highlighter import EditorHighlighter
from writing_english.editor.editor_theme import EditorColors
from writing_english.editor.line_number_area import LineNumberArea


EDITOR_SIDE_PADDING = 28
LINE_HEIGHT_PERCENT = 160


class EditorWidget(QPlainTextEdit):
    focus_mode_changed = Signal(bool)
    overwrite_mode_changed = Signal(bool)
    cursor_position = Signal(int, int)
    stats_changed = Signal(int, int, int)
    gec_error_clicked = Signal(int)
    typing_sound = Signal(str)
    sentence_completed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._overwrite_mode = False
        self._show_line_numbers = False
        self._line_number_area = LineNumberArea(self)
        self._line_number_area.setVisible(False)
        self._highlighter = EditorHighlighter(self.document())

        self._setup_font()
        self._setup_defaults()
        self._apply_block_format()
        self._connect_signals()

    def _setup_font(self) -> None:
        font = QFont()
        font.setStyleHint(QFont.StyleHint.SansSerif)
        self.setFont(font)

    def _setup_defaults(self) -> None:
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setCursorWidth(2)
        self.setFrameStyle(0)
        self.document().setDocumentMargin(16)
        self._update_text_margins()

    def _connect_signals(self) -> None:
        self.cursorPositionChanged.connect(self._emit_cursor_position)
        self.textChanged.connect(self._emit_stats)
        self.blockCountChanged.connect(self._on_block_count_changed)
        self.updateRequest.connect(self._on_update_request)

    def _on_block_count_changed(self, _new_count: int) -> None:
        self._update_text_margins()
        self._reposition_line_number_area()

    def _on_update_request(self, rect: QRect, dy: int) -> None:
        if dy != 0:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_text_margins()
            self._reposition_line_number_area()

    def apply_theme(self, colors: EditorColors) -> None:
        self.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: {colors.background};
                color: {colors.text};
                selection-background-color: {colors.accent};
                border: none;
                margin: 0px;
                padding: 0px;
            }}
            """
        )
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(colors.background))
        pal.setColor(QPalette.ColorRole.Text, QColor(colors.text))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.background))
        pal.setColor(QPalette.ColorRole.Mid, QColor(colors.line_number))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(colors.accent))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.text))
        self.setPalette(pal)
        self._line_number_area.update()

    def set_overwrite_mode(self, enabled: bool) -> None:
        self._overwrite_mode = enabled
        self.setCursorWidth(2 if not enabled else 8)
        self.overwrite_mode_changed.emit(enabled)

    def toggle_overwrite(self) -> None:
        self.set_overwrite_mode(not self._overwrite_mode)

    @property
    def is_overwrite(self) -> bool:
        return self._overwrite_mode

    def set_grammar_check(self, enabled: bool) -> None:
        self._highlighter.set_gec_enabled(enabled)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = self.createStandardContextMenu()
        cursor = self.cursorForPosition(event.pos())
        pos = cursor.position()
        for err in self._highlighter.gec_errors:
            if err["start"] <= pos < err["start"] + err["length"]:
                actions = menu.actions()
                if actions:
                    menu.insertSeparator(actions[0])
                category = err.get("category", "Grammar")
                action = menu.addAction(
                    f'{category}: Change "{err["original"]}" → "{err["suggestion"]}"'
                )
                action.triggered.connect(
                    lambda _checked=False, e=err: self._apply_gec_correction(e)
                )
                break
        menu.exec(event.globalPos())

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._highlighter.gec_errors:
            cursor = self.cursorForPosition(event.pos())
            pos = cursor.position()
            for i, err in enumerate(self._highlighter.gec_errors):
                if err["start"] <= pos < err["start"] + err["length"]:
                    self.gec_error_clicked.emit(i)
                    break

    def _apply_gec_correction(self, err: GECError) -> None:
        cursor = QTextCursor(self.document())
        cursor.setPosition(err["start"])
        cursor.setPosition(
            err["start"] + err["length"], QTextCursor.MoveMode.KeepAnchor
        )
        cursor.insertText(err["suggestion"])

    def set_show_line_numbers(self, visible: bool) -> None:
        self._show_line_numbers = visible
        self._line_number_area.setVisible(visible)
        self._update_text_margins()
        self._reposition_line_number_area()

    def line_number_area_width(self) -> int:
        if not self._show_line_numbers:
            return 0
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_text_margins(self) -> None:
        gutter = self.line_number_area_width()
        side_pad = EDITOR_SIDE_PADDING
        self.setViewportMargins(gutter + side_pad, 0, side_pad, 0)

    def _reposition_line_number_area(self) -> None:
        cr = self.contentsRect()
        width = self.line_number_area_width()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), width, cr.height())
        )

    def _apply_block_format(self) -> None:
        fmt = QTextBlockFormat()
        fmt.setLineHeight(
            LINE_HEIGHT_PERCENT,
            QTextBlockFormat.LineHeightTypes.ProportionalHeight.value,
        )
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(fmt)

    def setPlainText(self, text: str) -> None:
        super().setPlainText(text)
        self._apply_block_format()

    def setFont(self, font: QFont) -> None:
        super().setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self._update_text_margins()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_text_margins()
        self._reposition_line_number_area()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Insert:
            self.toggle_overwrite()
            return
        if self._overwrite_mode and event.key() in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_Home,
            Qt.Key.Key_End,
            Qt.Key.Key_PageUp,
            Qt.Key.Key_PageDown,
        ):
            super().keyPressEvent(event)
            return
        if self._overwrite_mode and not event.text():
            super().keyPressEvent(event)
            return
        is_sound_key = event.text() or event.key() in (
            Qt.Key.Key_Backspace,
            Qt.Key.Key_Return,
            Qt.Key.Key_Space,
        )
        if is_sound_key and not event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        ):
            if event.key() == Qt.Key.Key_Return:
                self.typing_sound.emit("enter")
            elif event.key() == Qt.Key.Key_Space:
                self.typing_sound.emit("space")
            elif event.key() == Qt.Key.Key_Backspace:
                self.typing_sound.emit("backspace")
            else:
                self.typing_sound.emit("key")
        if self._overwrite_mode and event.text():
            cursor = self.textCursor()
            if (
                not cursor.atEnd()
                and cursor.block().length() > cursor.positionInBlock()
            ):
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor
                )
        super().keyPressEvent(event)

        # Sentence completion detection
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):
            cursor = self.textCursor()
            pos = cursor.position()
            if pos >= 2:
                # Check character before the space/enter
                doc_text = self.toPlainText()
                prev_char = doc_text[pos - 2] if pos > 1 else ""
                if prev_char in (".", "!", "?"):
                    # Check if there is actual content before the punctuation
                    # We look back for non-whitespace
                    lookback = doc_text[: pos - 2].strip()
                    if lookback:
                        self.sentence_completed.emit()

    def _emit_cursor_position(self) -> None:
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_position.emit(line, col)

    def _emit_stats(self) -> None:
        text = self.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        lines = self.blockCount()
        self.stats_changed.emit(lines, words, chars)
