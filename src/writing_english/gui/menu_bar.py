from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenuBar, QMenu, QWidget


class MenuBar(QMenuBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self._file_menu: QMenu = self.addMenu("&File")
        self._edit_menu: QMenu = self.addMenu("&Edit")
        self._view_menu: QMenu = self.addMenu("&View")
        self._tools_menu: QMenu = self.addMenu("&Tools")
        self._help_menu: QMenu = self.addMenu("&Help")

        self._actions: dict[str, QAction] = {}
        self._build_file_menu()
        self._build_edit_menu()
        self._build_view_menu()
        self._build_tools_menu()
        self._build_help_menu()

    def _build_file_menu(self) -> None:
        self._add_action(
            "new", "&New", QKeySequence(QKeySequence.StandardKey.New), self._file_menu
        )
        self._add_action(
            "open",
            "&Open...",
            QKeySequence(QKeySequence.StandardKey.Open),
            self._file_menu,
        )
        self._add_action(
            "save",
            "&Save",
            QKeySequence(QKeySequence.StandardKey.Save),
            self._file_menu,
        )
        self._add_action(
            "save_as",
            "Save &As...",
            QKeySequence(QKeySequence.StandardKey.SaveAs),
            self._file_menu,
        )
        self._file_menu.addSeparator()
        self._recent_menu = self._file_menu.addMenu("Recent Files")
        self._file_menu.addSeparator()
        self._add_action("quit", "&Quit", QKeySequence("Ctrl+Q"), self._file_menu)

    def _build_edit_menu(self) -> None:
        self._add_action(
            "undo",
            "&Undo",
            QKeySequence(QKeySequence.StandardKey.Undo),
            self._edit_menu,
        )
        self._add_action(
            "redo",
            "&Redo",
            QKeySequence(QKeySequence.StandardKey.Redo),
            self._edit_menu,
        )
        self._edit_menu.addSeparator()
        self._add_action(
            "set_prompt",
            "Set &Prompt...",
            QKeySequence("Ctrl+Shift+P"),
            self._edit_menu,
        )
        self._add_action(
            "toggle_overwrite",
            "Toggle O&verwrite",
            QKeySequence("Insert"),
            self._edit_menu,
        )

    def _build_view_menu(self) -> None:
        self._add_action(
            "focus_mode", "&Focus Mode", QKeySequence("F11"), self._view_menu
        )
        self._view_menu.addSeparator()
        self._add_action(
            "toggle_line_numbers",
            "Toggle &Line Numbers",
            QKeySequence("Ctrl+Shift+L"),
            self._view_menu,
        )
        self._add_action(
            "toggle_word_wrap",
            "Toggle &Word Wrap",
            QKeySequence("Alt+Z"),
            self._view_menu,
        )

    def _build_tools_menu(self) -> None:
        self._add_action(
            "settings", "&Settings...", QKeySequence("Ctrl+,"), self._tools_menu
        )

    def _build_help_menu(self) -> None:
        self._add_action("check_updates", "Check for &Updates", None, self._help_menu)
        self._help_menu.addSeparator()
        self._add_action("about", "&About", None, self._help_menu)

    def _add_action(
        self, name: str, text: str, shortcut: QKeySequence | None, menu: QMenu
    ) -> None:
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        menu.addAction(action)
        self._actions[name] = action

    def get_action(self, name: str) -> QAction | None:
        return self._actions.get(name)

    def get_recent_menu(self) -> QMenu:
        return self._recent_menu
