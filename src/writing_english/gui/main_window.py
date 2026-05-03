from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QApplication,
)

from writing_english.app.context import AppContext
from writing_english.app.constants import APP_NAME
from writing_english.core.document import Document
from writing_english.editor.editor_widget import EditorWidget
from writing_english.editor.editor_theme import get_colors
from writing_english.gui.menu_bar import MenuBar
from writing_english.gui.prompt_bar import PromptBar
from writing_english.gui.status_bar import StatusBar
from writing_english.gui.system_colors import get_chrome_colors, get_system_theme
from writing_english.gui.focus_mode import FocusModeOverlay
from writing_english.gui.settings_dialog import SettingsDialog
from writing_english.infrastructure.autosave import AutosaveManager


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context
        self._document = Document()
        self._focus_mode_active = False

        self._setup_window()
        self._create_widgets()
        self._connect_signals()
        self._apply_theme()
        self._apply_editor_settings()
        self._connect_actions()

    def _setup_window(self) -> None:
        self.setWindowTitle(f"Untitled — {APP_NAME}")
        self.resize(960, 680)
        self.setMinimumSize(600, 400)

    def _create_widgets(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._menu_bar = MenuBar(self)
        self.setMenuBar(self._menu_bar)

        self._prompt_bar = PromptBar(self)
        layout.addWidget(self._prompt_bar)

        self._editor = EditorWidget(self)
        layout.addWidget(self._editor, 1)

        self._status_bar = StatusBar(self)
        self.setStatusBar(self._status_bar)

        self._focus_overlay = FocusModeOverlay(self)

        self._autosave = AutosaveManager(self)
        self._autosave.set_document(self._document)

    def _connect_signals(self) -> None:
        self._editor.cursor_position.connect(self._status_bar.update_cursor)
        self._editor.stats_changed.connect(self._on_stats_changed)
        self._editor.overwrite_mode_changed.connect(self._status_bar.set_overwrite_mode)
        self._editor.textChanged.connect(self._on_text_changed)
        self._status_bar.spell_check_toggled.connect(self._on_spell_check_toggled)
        self._prompt_bar.prompt_changed.connect(self._on_prompt_edited)
        self._focus_overlay.exit_focus.connect(self.toggle_focus_mode)
        self._app().styleHints().colorSchemeChanged.connect(self._on_system_theme_changed)

    def _connect_actions(self) -> None:
        self._connect_action("new", self.new_document)
        self._connect_action("open", self.open_document)
        self._connect_action("save", self.save_document)
        self._connect_action("save_as", self.save_document_as)
        self._connect_action("undo", self._editor.undo)
        self._connect_action("redo", self._editor.redo)
        self._connect_action("set_prompt", self.set_prompt)
        self._connect_action("toggle_overwrite", self._editor.toggle_overwrite)
        self._connect_action("focus_mode", self.toggle_focus_mode)
        self._connect_action("toggle_line_numbers", self.toggle_line_numbers)
        self._connect_action("toggle_word_wrap", self.toggle_word_wrap)
        self._connect_action("settings", self.open_settings)
        self._connect_action("about", self.show_about)

    def _connect_action(self, name: str, slot: object) -> None:
        action = self._menu_bar.get_action(name)
        if action is not None:
            action.triggered.connect(slot)

    def new_document(self) -> None:
        if self._document.is_modified:
            ret = self._confirm_save()
            if ret == QMessageBox.StandardButton.Cancel:
                return
            if ret == QMessageBox.StandardButton.Save:
                self.save_document()

        self._document = Document()
        self._editor.setPlainText("")
        self._prompt_bar.clear_prompt()
        self._autosave.set_document(self._document)
        self._update_title()
        self._editor._emit_stats()

    def open_document(self) -> None:
        if self._document.is_modified:
            ret = self._confirm_save()
            if ret == QMessageBox.StandardButton.Cancel:
                return
            if ret == QMessageBox.StandardButton.Save:
                self.save_document()

        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open Document",
            str(self._ctx.documents_dir),
            "Markdown Files (*.md);;All Files (*)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            doc = Document.from_file(path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file:\n{e}")
            return

        self._document = doc
        self._editor.setPlainText(doc.content)
        self._prompt_bar.set_prompt(doc.prompt)
        self._autosave.set_document(self._document)
        self._ctx.recent_files.add(path)
        self._update_title()

    def save_document(self) -> None:
        self._sync_content_to_document()
        if self._document.path is None:
            self.save_document_as()
            return
        try:
            self._document.save()
            self._document.mark_saved()
            self._update_title()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file:\n{e}")

    def save_document_as(self) -> None:
        self._sync_content_to_document()
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save Document As",
            str(self._ctx.documents_dir / f"{self._document.display_name}.md"),
            "Markdown Files (*.md);;All Files (*)",
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            self._document.save(path)
            self._document.mark_saved()
            self._ctx.recent_files.add(path)
            self._update_title()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file:\n{e}")

    def set_prompt(self) -> None:
        self._prompt_bar.focus_input()

    @Slot(str)
    def _on_prompt_edited(self, text: str) -> None:
        new_prompt = text if text else None
        if new_prompt == self._document.prompt:
            return
        self._document.prompt = new_prompt
        if not self._document.is_modified:
            self._document.is_modified = True
            self._update_title()

    def toggle_focus_mode(self) -> None:
        self._focus_mode_active = not self._focus_mode_active
        if self._focus_mode_active:
            self._status_bar.hide()
            self._menu_bar.hide()
            self._focus_overlay.enter_focus_mode()
        else:
            self._status_bar.show()
            self._menu_bar.show()
            self._focus_overlay.exit_focus_mode()

    def toggle_line_numbers(self) -> None:
        current = not self._editor._show_line_numbers
        self._editor.set_show_line_numbers(current)

    def toggle_word_wrap(self) -> None:
        current = self._editor.lineWrapMode()
        if current == self._editor.LineWrapMode.WidgetWidth:
            self._editor.setLineWrapMode(self._editor.LineWrapMode.NoWrap)
        else:
            self._editor.setLineWrapMode(self._editor.LineWrapMode.WidgetWidth)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self._ctx.settings, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._apply_editor_settings()
            self._apply_theme()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Writing English",
            "<h3>Writing English</h3>"
            "<p>Version 0.1.0</p>"
            "<p>A focused English writing practice desktop app.</p>",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._document.is_modified:
            ret = self._confirm_save()
            if ret == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if ret == QMessageBox.StandardButton.Save:
                self.save_document()
        self._autosave.stop()
        self._ctx.database.close()
        event.accept()

    def _confirm_save(self) -> QMessageBox.StandardButton:
        return QMessageBox.question(
            self,
            "Unsaved Changes",
            f"'{self._document.display_name}' has unsaved changes. Save before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )

    def _sync_content_to_document(self) -> None:
        self._document.content = self._editor.toPlainText()
        self._document.update_word_count()

    def _update_title(self) -> None:
        modified = " *" if self._document.is_modified else ""
        title = f"{self._document.display_name}{modified} — {APP_NAME}"
        self.setWindowTitle(title)

    @Slot(int, int, int)
    def _on_stats_changed(self, lines: int, words: int, chars: int) -> None:
        self._status_bar.update_stats(words, chars)

    @Slot()
    def _on_text_changed(self) -> None:
        if not self._document.is_modified:
            self._document.is_modified = True
            self._update_title()

    @Slot(bool)
    def _on_spell_check_toggled(self, enabled: bool) -> None:
        self._editor.set_spell_check(enabled)
        self._ctx.settings.spell_check = enabled
        self._ctx.settings.sync()

    @Slot()
    def _on_system_theme_changed(self) -> None:
        if self._ctx.settings.theme == "system":
            self._apply_theme()

    def _apply_theme(self) -> None:
        theme_setting = self._ctx.settings.theme
        theme_name = get_system_theme() if theme_setting == "system" else theme_setting
        colors = get_colors(theme_name)

        if theme_name == "dark":
            qss_path = (
                Path(__file__).parent.parent / "resources" / "styles" / "dark.qss"
            )
        else:
            qss_path = (
                Path(__file__).parent.parent / "resources" / "styles" / "light.qss"
            )

        if qss_path.exists():
            qss_text = qss_path.read_text()
            chrome_bg, chrome_fg = get_chrome_colors(theme_name)
            qss_text = qss_text.replace("@chrome-bg@", chrome_bg)
            qss_text = qss_text.replace("@chrome-fg@", chrome_fg)
            self._app().setStyleSheet(qss_text)

        self._editor.apply_theme(colors)

    def _apply_editor_settings(self) -> None:
        settings = self._ctx.settings
        font = self._editor.font()
        if settings.font_family:
            font.setFamily(settings.font_family)
        if settings.font_size > 0:
            font.setPointSize(settings.font_size)
        self._editor.setFont(font)
        self._editor.set_show_line_numbers(settings.show_line_numbers)
        self._editor.set_spell_check(settings.spell_check)
        self._status_bar.set_spell_check(settings.spell_check)
        if settings.word_wrap:
            self._editor.setLineWrapMode(self._editor.LineWrapMode.WidgetWidth)
        else:
            self._editor.setLineWrapMode(self._editor.LineWrapMode.NoWrap)
        self._autosave.set_interval(settings.autosave_interval_ms)

    def _app(self) -> QApplication:
        from PySide6.QtWidgets import QApplication as QA

        app = QA.instance()
        assert app is not None
        return app  # type: ignore[return-value]
