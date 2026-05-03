from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QSettings, Slot, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QApplication,
    QDialog,
)

from writing_english.app.context import AppContext
from writing_english.app.constants import APP_NAME, GECTOR_ONNX_DIR
from writing_english.core.document import Document
from writing_english.editor.editor_widget import EditorWidget
from writing_english.editor.editor_theme import get_colors
from writing_english.gui.menu_bar import MenuBar
from writing_english.gui.prompt_bar import PromptBar
from writing_english.gui.status_bar import StatusBar
from writing_english.gui.system_colors import get_chrome_colors, get_system_theme
from writing_english.gui.focus_mode import FocusModeOverlay
from writing_english.gui.settings_dialog import SettingsDialog
from writing_english.gui.analysis_widget import AnalysisWidget
from writing_english.gui.sticker_reward import StickerRewardController
from writing_english.adapters.gec.gector_adapter import GectorAdapter
from writing_english.editor.grammar_controller import GrammarCheckController
from writing_english.editor.typing_sounds import TypingSoundManager
from writing_english.infrastructure.autosave import AutosaveManager


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context
        self._document = Document()
        self._focus_mode_active = False
        self._analysis_was_visible = False

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
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._menu_bar = MenuBar(self)
        self.setMenuBar(self._menu_bar)

        self._prompt_bar = PromptBar(self)
        main_layout.addWidget(self._prompt_bar)

        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(4)

        self._editor = EditorWidget(self)
        self._splitter.addWidget(self._editor)

        self._analysis = AnalysisWidget(self)
        self._analysis.hide()
        self._splitter.addWidget(self._analysis)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setSizes([500, 200])

        main_layout.addWidget(self._splitter, 1)

        self._status_bar = StatusBar(self)
        self.setStatusBar(self._status_bar)

        self._focus_overlay = FocusModeOverlay(self)

        model_dir = (
            Path(self._ctx.settings.gector_model_dir)
            if self._ctx.settings.gector_model_dir
            else GECTOR_ONNX_DIR
        )
        self._gector_adapter = GectorAdapter(model_dir=model_dir)
        self._grammar_ctrl = GrammarCheckController(
            self._editor, self._editor._highlighter, self._gector_adapter, parent=self
        )

        self._autosave = AutosaveManager(self)
        self._autosave.set_document(self._document)

        self._typing_sounds = TypingSoundManager()
        self._typing_sounds.initialize(self._ctx.settings.typing_sound_pack)

        self._session_timer = QTimer(self)
        self._session_timer.setInterval(1000)
        self._session_timer.timeout.connect(self._on_timer_tick)
        self._is_timer_running = False

        self._sticker_rewards = StickerRewardController(self._editor)

        self._restore_layout()
        self._update_timer_display()

    def _connect_signals(self) -> None:
        self._editor.cursor_position.connect(self._status_bar.update_cursor)
        self._editor.stats_changed.connect(self._on_stats_changed)
        self._editor.overwrite_mode_changed.connect(self._status_bar.set_overwrite_mode)
        self._editor.textChanged.connect(self._on_text_changed)
        self._status_bar.timer_toggled.connect(self._on_timer_toggled)
        self._status_bar.grammar_check_triggered.connect(
            self._on_grammar_check_triggered
        )
        self._grammar_ctrl.check_started.connect(self._on_grammar_check_started)
        self._grammar_ctrl.check_finished.connect(self._on_grammar_check_finished)
        self._grammar_ctrl.results_ready.connect(self._on_grammar_results_ready)
        self._grammar_ctrl.status_changed.connect(self._status_bar.showMessage)
        self._analysis.correction_clicked.connect(self._apply_grammar_correction)
        self._analysis.close_requested.connect(self._hide_analysis)
        self._editor.gec_error_clicked.connect(self._highlight_analysis_error)
        self._prompt_bar.prompt_changed.connect(self._on_prompt_edited)
        self._editor.typing_sound.connect(self._on_typing_sound)
        self._status_bar.typing_sounds_toggled.connect(self._on_typing_sounds_toggled)
        self._status_bar.sticker_rewards_toggled.connect(
            self._on_sticker_rewards_toggled
        )
        self._editor.sentence_completed.connect(self._sticker_rewards.show_random_sticker)
        self._focus_overlay.exit_focus.connect(self.toggle_focus_mode)
        self._app().styleHints().colorSchemeChanged.connect(
            self._on_system_theme_changed
        )

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
        self._update_timer_display()

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
            self._analysis_was_visible = self._analysis.isVisible()
            self._status_bar.hide()
            self._menu_bar.hide()
            self._analysis.hide()
            self._focus_overlay.enter_focus_mode()
        else:
            self._status_bar.show()
            self._menu_bar.show()
            if self._analysis_was_visible:
                self._analysis.show()
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
        self._grammar_ctrl.shutdown()
        self._autosave.stop()
        self._save_layout()
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
        if not self._is_timer_running:
            self._is_timer_running = True
            self._session_timer.start()
            self._status_bar.set_timer_state(True)

    @Slot(str)
    def _on_typing_sound(self, sound_type: str) -> None:
        if sound_type == "enter":
            self._typing_sounds.play_enter()
        elif sound_type == "space":
            self._typing_sounds.play_space()
        elif sound_type == "backspace":
            self._typing_sounds.play_backspace()
        else:
            self._typing_sounds.play_key()

    @Slot(bool)
    def _on_timer_toggled(self, checked: bool) -> None:
        self._is_timer_running = checked
        if checked:
            self._session_timer.start()
        else:
            self._session_timer.stop()
        self._status_bar.set_timer_state(checked)

    @Slot()
    def _on_timer_tick(self) -> None:
        self._document.session_duration += 1
        self._update_timer_display()

    def _update_timer_display(self) -> None:
        duration = self._document.session_duration
        h = duration // 3600
        m = (duration % 3600) // 60
        s = duration % 60
        self._status_bar.set_timer_display(f"{h:02d}:{m:02d}:{s:02d}")

    @Slot(bool)
    def _on_typing_sounds_toggled(self, enabled: bool) -> None:
        self._typing_sounds.enabled = enabled
        self._ctx.settings.typing_sounds = enabled
        self._ctx.settings.sync()

    @Slot(bool)
    def _on_sticker_rewards_toggled(self, enabled: bool) -> None:
        self._sticker_rewards.set_enabled(enabled)
        self._ctx.settings.sticker_rewards = enabled
        self._ctx.settings.sync()

    @Slot()
    def _on_grammar_check_triggered(self) -> None:
        if not self._gector_adapter.is_available():
            from writing_english.gui.model_setup_dialog import ModelSetupDialog

            dialog = ModelSetupDialog(self._ctx.settings, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            model_dir = Path(self._ctx.settings.gector_model_dir)
            self._gector_adapter = GectorAdapter(model_dir=model_dir)
            self._grammar_ctrl.set_adapter(self._gector_adapter)
            if not self._gector_adapter.is_available():
                self._status_bar.showMessage(
                    "Grammar check unavailable — model setup failed"
                )
                return
        self._analysis.show()
        self._splitter.setSizes([self._splitter.height() - 200, 200])
        self._grammar_ctrl.check_now()

    @Slot()
    def _on_grammar_check_started(self) -> None:
        self._status_bar.set_grammar_loading(True)
        self._status_bar.showMessage("Checking grammar...")

    @Slot()
    def _on_grammar_check_finished(self) -> None:
        self._status_bar.set_grammar_loading(False)
        self._status_bar.clearMessage()

    def _on_grammar_results_ready(self, errors: list) -> None:
        if not self._analysis.isVisible():
            self._analysis.show()
            self._splitter.setSizes([self._splitter.height() - 200, 200])
        self._analysis.set_grammar_results(errors)

    @Slot(int, int, str)
    def _apply_grammar_correction(
        self, start: int, length: int, suggestion: str
    ) -> None:
        from PySide6.QtGui import QTextCursor

        cursor = QTextCursor(self._editor.document())
        cursor.setPosition(start)
        cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(suggestion)

    def _hide_analysis(self) -> None:
        self._analysis.hide()
        self._analysis.clear_grammar_results()
        self._grammar_ctrl.set_autocheck(False)
        self._editor._highlighter.clear_gec_errors()

    @Slot(int)
    def _highlight_analysis_error(self, index: int) -> None:
        if not self._analysis.isVisible():
            self._analysis.show()
            self._splitter.setSizes([self._splitter.height() - 200, 200])
        self._analysis.highlight_error(index)

    def _save_layout(self) -> None:
        s = QSettings("WritingEnglish", "Writing English")
        s.beginGroup("MainWindow")
        s.setValue("geometry", self.saveGeometry())
        s.endGroup()

    def _restore_layout(self) -> None:
        s = QSettings("WritingEnglish", "Writing English")
        s.beginGroup("MainWindow")
        geo = s.value("geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        s.endGroup()

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
        self._editor._highlighter.set_gec_underline_color(colors.gec_underline)

    def _apply_editor_settings(self) -> None:
        settings = self._ctx.settings
        font = self._editor.font()
        if settings.font_family:
            font.setFamily(settings.font_family)
        if settings.font_size > 0:
            font.setPointSize(settings.font_size)
        self._editor.setFont(font)
        self._editor.set_show_line_numbers(settings.show_line_numbers)
        self._typing_sounds.enabled = settings.typing_sounds
        self._status_bar.set_typing_sounds(settings.typing_sounds)
        self._typing_sounds.change_pack(settings.typing_sound_pack)
        self._sticker_rewards.set_enabled(settings.sticker_rewards)
        self._sticker_rewards.set_folder(settings.sticker_folder)
        self._status_bar.set_sticker_rewards(settings.sticker_rewards)
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
