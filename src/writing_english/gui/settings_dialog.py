from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
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
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLabel,
)

from writing_english.app.constants import SETTINGS_PATH
from writing_english.config.settings import Settings

_SOUNDS_DIR = Path(__file__).resolve().parent.parent / "resources" / "sounds"


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

        self._spell_check = QCheckBox("Enable spell check")
        editor_layout.addRow(self._spell_check)

        self._typing_sounds = QCheckBox("Typing sounds")
        editor_layout.addRow(self._typing_sounds)

        self._typing_sound_pack = QComboBox()
        if _SOUNDS_DIR.exists():
            packs = sorted([d.name for d in _SOUNDS_DIR.iterdir() if d.is_dir()])
            self._typing_sound_pack.addItems(packs)
        editor_layout.addRow("Sound Pack:", self._typing_sound_pack)

        self._sounds_citation = QLabel("<a href='https://github.com/tplai/kbsim/tree/master'>Sounds from kbsim</a>")
        self._sounds_citation.setOpenExternalLinks(True)
        self._sounds_citation.setStyleSheet("font-size: 11px; color: #888;")
        editor_layout.addRow("", self._sounds_citation)

        layout.addWidget(editor_group)

        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        self._theme = QComboBox()
        self._theme.addItems(["system", "light", "dark"])
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

        storage_group = QGroupBox("Storage")
        storage_layout = QFormLayout(storage_group)

        app_data_row = QWidget()
        app_data_layout = QVBoxLayout(app_data_row)
        app_data_layout.setContentsMargins(0, 0, 0, 0)
        self._app_data_dir = QLineEdit()
        self._app_data_dir.setReadOnly(True)
        app_data_layout.addWidget(self._app_data_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_app_data_dir)
        app_data_layout.addWidget(browse_btn)
        storage_layout.addRow("App Data Directory:", app_data_row)

        self._settings_path_label = QLabel()
        self._settings_path_label.setWordWrap(True)
        self._settings_path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        storage_layout.addRow("Settings File:", self._settings_path_label)

        layout.addWidget(storage_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_browse_app_data_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Select App Data Directory",
            self._app_data_dir.text() or str(Path.home()),
        )
        if path:
            self._app_data_dir.setText(path)
            self._settings_path_label.setText(str(Path(path) / "settings.ini"))

    def _load_values(self) -> None:
        self._font_family.setCurrentText(self._settings.font_family)
        self._font_size.setValue(self._settings.font_size)
        self._line_height.setValue(self._settings.line_height)
        self._word_wrap.setChecked(self._settings.word_wrap)
        self._show_line_numbers.setChecked(self._settings.show_line_numbers)
        self._spell_check.setChecked(self._settings.spell_check)
        self._typing_sounds.setChecked(self._settings.typing_sounds)
        self._typing_sound_pack.setCurrentText(self._settings.typing_sound_pack)
        self._theme.setCurrentText(self._settings.theme)
        self._autosave_interval.setValue(self._settings.autosave_interval_ms // 1000)
        self._app_data_dir.setText(self._settings.app_data_dir)
        self._settings_path_label.setText(str(SETTINGS_PATH))

    def _on_accept(self) -> None:
        self._settings.font_family = self._font_family.currentText()
        self._settings.font_size = self._font_size.value()
        self._settings.line_height = self._line_height.value()
        self._settings.word_wrap = self._word_wrap.isChecked()
        self._settings.show_line_numbers = self._show_line_numbers.isChecked()
        self._settings.spell_check = self._spell_check.isChecked()
        self._settings.typing_sounds = self._typing_sounds.isChecked()
        self._settings.typing_sound_pack = self._typing_sound_pack.currentText()
        self._settings.theme = self._theme.currentText()
        self._settings.autosave_interval_ms = self._autosave_interval.value() * 1000

        new_app_data_dir = self._app_data_dir.text()
        if new_app_data_dir != self._settings.app_data_dir:
            self._settings.app_data_dir = new_app_data_dir
            QMessageBox.information(
                self,
                "Restart Required",
                "The app data directory has been changed.\n"
                "Please restart the application for the change to take effect.",
            )

        self._settings.sync()
        self.accept()
