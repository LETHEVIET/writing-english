# Writing English

A focused, cross-platform desktop app for English writing practice. Built with PySide6 (Qt6), styled after iA Writer's minimal aesthetic.

## Features

- **Clean writing environment** — distraction-free editor with prompt bar, status bar, and optional line numbers
- **Prompt-based practice** — set a writing prompt and focus on the task
- **Markdown + YAML frontmatter** — documents store metadata (prompt, timestamps, session duration) in standard `.md` files
- **Auto-save** — configurable background saves to `~/Documents/Writing English/`
- **Light & dark themes** — system theme auto-detection with manual override
- **Focus Mode** (`F11`) — hides all chrome, leaving only the prompt and editor
- **Grammar Error Correction** — ONNX-based GEC via [GECToR](https://github.com/grammarly/gector) with 11 error categories
- **Typing sounds** — 13 mechanical keyboard sound packs (alpaca, mxblue, topre, etc.)
- **Sticker rewards** — animated sticker popups on sentence completion
- **Session tracking** — per-document writing timer with duration display
- **Recent files** — SQLite-backed history, accessible from the File menu
- **Plugin architecture** — extensible design for future GEC and LLM adapters
- **Update checking** — automatic checks via GitHub Releases, configurable in settings

## Screenshots

<!-- TODO: add screenshots to a docs/screenshots/ directory
![Light theme](docs/screenshots/light.png)
![Dark theme](docs/screenshots/dark.png)
![Focus mode](docs/screenshots/focus.png)
-->

## Installation

**Prerequisites:** [uv](https://docs.astral.sh/uv/) (Python package manager)

```bash
git clone https://github.com/<owner>/writing-english.git
cd writing-english

# Install Python 3.14 and dependencies
uv python install 3.14
uv sync

# Run the app
uv run writing-english
```

For GEC (grammar checking) support, install the optional dependencies:

```bash
uv sync --all-extras
```

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Lint
uv run ruff check .
uv run ruff format --check .

# Type check
uv run mypy src/writing_english
```

## Building

Build a standalone executable with Nuitka:

```bash
uv run python scripts/build.py
```

Output goes to `dist/`. The script auto-detects your platform (Linux, macOS, Windows).

Alternatively, push a `v*` tag to trigger CI builds and a GitHub Release:

```bash
git tag v0.2.0
git push origin v0.2.0
```

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New | `Ctrl+N` |
| Open | `Ctrl+O` |
| Save | `Ctrl+S` |
| Save As | `Ctrl+Shift+S` |
| Undo / Redo | `Ctrl+Z` / `Ctrl+Y` |
| Set Prompt | `Ctrl+Shift+P` |
| Settings | `Ctrl+,` |
| Focus Mode | `F11` |
| Toggle Line Numbers | `Ctrl+Shift+L` |
| Toggle Word Wrap | `Alt+Z` |
| Toggle Overwrite | `Insert` |

## Document Format

Documents are `.md` files with YAML frontmatter:

```markdown
---
prompt: "Write 200 words about a place you feel most at peace."
created: 2026-05-03T09:00:00+00:00
last_modified: 2026-05-03T09:45:00+00:00
session_duration: 2700
total_words: 215
---

There is a small wooden bench tucked beneath...
```

Plain `.md` files without frontmatter are also supported.

## Architecture

```
writing_english/
├── app/          — Application bootstrap, context, constants
├── config/       — Settings (QSettings), defaults
├── core/         — Document, session, and prompt models
├── editor/       — Editor widget, highlighter, themes, typing sounds
├── gui/          — Main window, menus, dialogs, status bar, focus mode
├── infrastructure/ — File I/O, SQLite, autosave, recent files, updater
├── adapters/     — Abstract adapter interfaces + GEC/LLM implementations
├── plugins/      — Plugin host and interface
└── resources/    — QSS stylesheets, sound files, icons
```

## Credits

- **GEC model** — Based on [Grammarly/gector](https://github.com/grammarly/gector) (Neural Grammar Error Correction). The ONNX Runtime adaptation builds on the PyTorch reimplementation by [gotutiyan/gector](https://github.com/gotutiyan/gector).
- **Typing sounds** — Mechanical keyboard sound packs from [tplai/kbsim](https://github.com/tplai/kbsim).

## License

MIT
