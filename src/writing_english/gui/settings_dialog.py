from __future__ import annotations


from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QDialogButtonBox,
    QWidget,
)

from writing_english.config.settings import Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        editor_group = QGroupBox("Editor")
        editor_layout = QFormLayout(editor_group)

        self._font_family = QComboBox()
        self._font_family.setEditable(True)
        self._font_family.addItems(
            [
                "JetBrains Mono",
                "Fira Code",
                "Consolas",
                "Monaco",
                "Source Code Pro",
                "IBM Plex Mono",
                "monospace",
            ]
        )
        editor_layout.addRow("Font Family:", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(0, 36)
        self._font_size.setSpecialValueText("Default")
        editor_layout.addRow("Font Size:", self._font_size)

        self._line_height = QDoubleSpinBox()
        self._line_height.setRange(1.0, 3.0)
        self._line_height.setSingleStep(0.1)
        editor_layout.addRow("Line Height:", self._line_height)

        self._word_wrap = QCheckBox("Enable word wrap")
        editor_layout.addRow(self._word_wrap)

        self._show_line_numbers = QCheckBox("Show line numbers")
        editor_layout.addRow(self._show_line_numbers)

        layout.addWidget(editor_group)

        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        self._theme = QComboBox()
        self._theme.addItems(["light", "dark"])
        appearance_layout.addRow("Theme:", self._theme)

        layout.addWidget(appearance_group)

        general_group = QGroupBox("General")
        general_layout = QFormLayout(general_group)

        self._autosave_interval = QSpinBox()
        self._autosave_interval.setRange(5, 300)
        self._autosave_interval.setSuffix(" seconds")
        self._autosave_interval.setSingleStep(5)
        general_layout.addRow("Auto-save Interval:", self._autosave_interval)

        layout.addWidget(general_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_values(self) -> None:
        self._font_family.setCurrentText(self._settings.font_family)
        self._font_size.setValue(self._settings.font_size)
        self._line_height.setValue(self._settings.line_height)
        self._word_wrap.setChecked(self._settings.word_wrap)
        self._show_line_numbers.setChecked(self._settings.show_line_numbers)
        self._theme.setCurrentText(self._settings.theme)
        self._autosave_interval.setValue(self._settings.autosave_interval_ms // 1000)

    def _on_accept(self) -> None:
        self._settings.font_family = self._font_family.currentText()
        self._settings.font_size = self._font_size.value()
        self._settings.line_height = self._line_height.value()
        self._settings.word_wrap = self._word_wrap.isChecked()
        self._settings.show_line_numbers = self._show_line_numbers.isChecked()
        self._settings.theme = self._theme.currentText()
        self._settings.autosave_interval_ms = self._autosave_interval.value() * 1000
        self._settings.sync()
        self.accept()
