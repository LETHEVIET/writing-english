from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QSize, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

_ICONS_DIR = Path(__file__).parent.parent / "resources" / "icons"


def load_svg_icon(name: str, color: str = "#888888", size: int = 14) -> QIcon:
    path = _ICONS_DIR / f"{name}.svg"
    svg_bytes = path.read_bytes().replace(b"currentColor", color.encode())
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)
