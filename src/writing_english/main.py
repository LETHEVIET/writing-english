from __future__ import annotations

import sys

from writing_english.app.application import bootstrap_app, bootstrap_context
from writing_english.gui.main_window import MainWindow


def main() -> None:
    app = bootstrap_app()
    context = bootstrap_context()
    window = MainWindow(context)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
