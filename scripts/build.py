#!/usr/bin/env python3
"""Build a distributable executable with Nuitka."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SRC_DIR = PROJECT_ROOT / "src" / "writing_english"
DIST_DIR = PROJECT_ROOT / "dist"
RESOURCES_DIR = SRC_DIR / "resources"

SYSTEM = platform.system()


def build() -> None:
    DIST_DIR.mkdir(exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--assume-yes-for-downloads",
        "--standalone",
        "--onefile",
        "--enable-plugin=pyside6",
        "--lto=no",
        f"--include-data-dir={RESOURCES_DIR}=resources",
        f"--output-dir={DIST_DIR}",
        str(SRC_DIR / "main.py"),
    ]

    if SYSTEM == "Windows":
        cmd.insert(cmd.index("--standalone"), "--windows-console-mode=disable")
        cmd.extend(["--output-filename=WritingEnglish.exe"])
    elif SYSTEM == "Darwin":
        cmd.extend(
            [
                "--output-filename=WritingEnglish",
                "--macos-create-app-bundle",
                "--macos-app-name=Writing English",
            ]
        )
    else:
        cmd.extend(["--output-filename=WritingEnglish"])

    print(f"Building for {SYSTEM}...")
    print(f"Command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    print(f"Build complete: {DIST_DIR}")


if __name__ == "__main__":
    build()
