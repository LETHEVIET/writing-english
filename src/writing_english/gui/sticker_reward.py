from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    Property,
    QObject,
    QParallelAnimationGroup,
)
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QLabel, QWidget


class StickerLabel(QLabel):
    def __init__(self, pixmap: QPixmap, parent: QWidget) -> None:
        super().__init__(parent)
        self.setPixmap(pixmap)
        self.setScaledContents(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedSize(160, 160)
        self._opacity = 1.0

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()

    opacity = Property(float, fget=get_opacity, fset=set_opacity)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        if self.pixmap():
            painter.drawPixmap(self.rect(), self.pixmap())


class StickerRewardController(QObject):
    def __init__(self, parent_widget: QWidget) -> None:
        super().__init__(parent_widget)
        self._parent = parent_widget
        self._enabled = False
        self._folder = ""
        self._active_animations: list[QParallelAnimationGroup] = []

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_folder(self, folder: str) -> None:
        self._folder = folder

    def show_random_sticker(self) -> None:
        if not self._enabled or not self._folder:
            return

        folder_path = Path(self._folder)
        if not folder_path.exists() or not folder_path.is_dir():
            return

        png_files = list(folder_path.glob("*.png"))
        if not png_files:
            return

        sticker_path = random.choice(png_files)
        pixmap = QPixmap(str(sticker_path))
        if pixmap.isNull():
            return

        label = StickerLabel(pixmap, self._parent)

        # Position it at the bottom right of the parent, with padding and slight random offset
        parent_rect = self._parent.rect()
        padding = 40
        x = parent_rect.width() - label.width() - padding + random.randint(-20, 0)
        y = parent_rect.height() - label.height() - padding + random.randint(-20, 0)
        label.move(x, y)
        label.show()

        # Animation Group: fade out and move up
        anim_group = QParallelAnimationGroup(label)
        
        fade_anim = QPropertyAnimation(label, b"opacity")
        fade_anim.setDuration(2500)
        fade_anim.setStartValue(1.0)
        fade_anim.setEndValue(0.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        
        move_anim = QPropertyAnimation(label, b"pos")
        move_anim.setDuration(2500)
        move_anim.setStartValue(QPoint(x, y))
        move_anim.setEndValue(QPoint(x, y - 80))
        move_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        anim_group.addAnimation(fade_anim)
        anim_group.addAnimation(move_anim)
        
        self._active_animations.append(anim_group)
        
        def cleanup() -> None:
            if anim_group in self._active_animations:
                self._active_animations.remove(anim_group)
            label.deleteLater()
            
        anim_group.finished.connect(cleanup)
        anim_group.start()
