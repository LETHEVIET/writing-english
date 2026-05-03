from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from writing_english.adapters.base import GECError


class SectionHeader(QWidget):
    toggled = Signal(bool)

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = True
        self._build_ui(title)

    def _build_ui(self, title: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self._arrow = QLabel("▼")
        self._arrow.setStyleSheet("color: #A4A4A4; font-size: 10px;")
        layout.addWidget(self._arrow)

        self._title = QLabel(title)
        font = self._title.font()
        font.setBold(True)
        self._title.setFont(font)
        layout.addWidget(self._title)

        self._count = QLabel("0")
        self._count.setObjectName("analysisCountBadge")
        layout.addWidget(self._count)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        self._expanded = not self._expanded
        self._arrow.setText("▼" if self._expanded else "▶")
        self.toggled.emit(self._expanded)

    def set_count(self, count: int) -> None:
        self._count.setText(str(count))
        self._count.setVisible(count > 0)


class GrammarSection(QWidget):
    correction_clicked = Signal(int, int, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._error_rows: list[QWidget] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = SectionHeader("Grammar")
        self._header.toggled.connect(self._on_header_toggled)
        layout.addWidget(self._header)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(24, 4, 8, 8)
        self._content_layout.setSpacing(4)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._empty_label = QLabel("Click the grammar check button to start.")
        self._empty_label.setObjectName("analysisEmptyLabel")
        self._empty_label.setWordWrap(True)
        self._content_layout.addWidget(self._empty_label)

        layout.addWidget(self._content)
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    def _on_header_toggled(self, expanded: bool) -> None:
        self._content.setVisible(expanded)

    def set_results(self, errors: list[GECError]) -> None:
        self._remove_error_rows()
        self._header.set_count(len(errors))

        if not errors:
            self._empty_label.setText("No grammar issues found.")
            self._empty_label.setVisible(True)
            return

        self._empty_label.setVisible(False)

        font = self.font()
        font.setBold(True)
        font.setPointSize(8)
        fm = QFontMetrics(font)
        max_cat_width = 0
        for err in errors:
            cat = err.get("category", "Grammar")
            max_cat_width = max(max_cat_width, fm.horizontalAdvance(cat))
        max_cat_width = max(max_cat_width, 60)

        for err in errors:
            row = self._create_error_row(err, max_cat_width)
            self._error_rows.append(row)
            self._content_layout.addWidget(row)

    def clear(self) -> None:
        self._remove_error_rows()
        self._header.set_count(0)
        self._empty_label.setText("Click the grammar check button to start.")
        self._empty_label.setVisible(True)

    def highlight_error(self, index: int, scroll_area: QScrollArea | None = None) -> None:
        self._clear_error_highlight()
        if 0 <= index < len(self._error_rows):
            row = self._error_rows[index]
            row.setObjectName("analysisErrorRowActive")
            row.style().unpolish(row)
            row.style().polish(row)
            if scroll_area is not None:
                content = scroll_area.widget()
                if content is not None:
                    pos_in_content = row.mapTo(content, row.rect().topLeft())
                    scroll_area.ensureVisible(
                        0, pos_in_content.y(), 0, row.height() + 20
                    )

    def _clear_error_highlight(self) -> None:
        for row in self._error_rows:
            if row.objectName() == "analysisErrorRowActive":
                row.setObjectName("analysisErrorRow")
                row.style().unpolish(row)
                row.style().polish(row)

    def _remove_error_rows(self) -> None:
        for row in self._error_rows:
            row.setParent(None)
            row.deleteLater()
        self._error_rows.clear()

    def _create_error_row(self, err: GECError, cat_width: int) -> QWidget:
        row = QFrame()
        row.setObjectName("analysisErrorRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        category = err.get("category", "Grammar")

        cat_text = QLabel(category)
        font = cat_text.font()
        font.setBold(True)
        font.setPointSize(8)
        cat_text.setFont(font)
        cat_text.setFixedWidth(cat_width)
        cat_text.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(cat_text)

        dot = QLabel("·")
        dot.setStyleSheet("color: #888888;")
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(dot)

        orig_label = QLabel(err["original"])
        orig_label.setObjectName("analysisOriginal")
        orig_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(orig_label)

        arrow = QLabel("→")
        arrow.setObjectName("analysisArrow")
        arrow.setStyleSheet("color: #888888;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(arrow)

        sugg_label = QLabel(err["suggestion"])
        sugg_label.setObjectName("analysisSuggestion")
        sugg_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(sugg_label)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        fix_btn = QPushButton("Fix")
        fix_btn.setObjectName("analysisFixButton")
        fix_btn.setFixedSize(36, 20)
        fix_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fix_btn.clicked.connect(
            lambda _checked=False, e=err: self.correction_clicked.emit(
                e["start"], e["length"], e["suggestion"]
            )
        )
        layout.addWidget(fix_btn)

        return row


class AnalysisWidget(QWidget):
    correction_clicked = Signal(int, int, str)
    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("analysisWidget")
        self.setMinimumHeight(80)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("analysisHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 8, 4)

        title = QLabel("Analysis")
        font = title.font()
        font.setBold(True)
        font.setPointSize(10)
        title.setFont(font)
        header_layout.addWidget(title)

        header_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("analysisClearButton")
        self._clear_btn.setFixedHeight(20)
        self._clear_btn.clicked.connect(self._on_clear)
        header_layout.addWidget(self._clear_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("analysisCloseButton")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setObjectName("analysisScroll")

        self._sections_widget = QWidget()
        sections_layout = QVBoxLayout(self._sections_widget)
        sections_layout.setContentsMargins(0, 4, 0, 4)
        sections_layout.setSpacing(0)
        sections_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._grammar_section = GrammarSection()
        self._grammar_section.correction_clicked.connect(self.correction_clicked.emit)
        sections_layout.addWidget(self._grammar_section)

        sections_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self._scroll.setWidget(self._sections_widget)
        layout.addWidget(self._scroll, 1)

    def set_grammar_results(self, errors: list[GECError]) -> None:
        self._grammar_section.set_results(errors)

    def clear_grammar_results(self) -> None:
        self._grammar_section.clear()

    def highlight_error(self, index: int) -> None:
        self._grammar_section.highlight_error(index, self._scroll)

    def _on_clear(self) -> None:
        self._grammar_section.clear()
