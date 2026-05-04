#!/usr/bin/env python3
"""Build a distributable executable with PyInstaller."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SRC_DIR = PROJECT_ROOT / "src" / "writing_english"
DIST_DIR = PROJECT_ROOT / "dist"
RESOURCES_DIR = SRC_DIR / "resources"

SYSTEM = platform.system()
_MACHINE = platform.machine().lower()

_SUFFIX_MAP = {
    "Linux": "linux",
    "Windows": "windows",
    "Darwin": "macos",
}

_PLATFORM_SUFFIX = _SUFFIX_MAP.get(SYSTEM, "unknown")
_BINARY_NAME = f"WritingEnglish-{_PLATFORM_SUFFIX}-{_MACHINE}"


def build() -> None:
    DIST_DIR.mkdir(exist_ok=True)

    sep = ";" if SYSTEM == "Windows" else ":"
    add_data = f"{RESOURCES_DIR}{sep}resources"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--clean",
        f"--add-data={add_data}",
        f"--name={_BINARY_NAME}",
        f"--distpath={DIST_DIR}",
        "--workpath=build",
        "--specpath=build",
        str(SRC_DIR / "main.py"),
    ]

    if SYSTEM == "Windows":
        cmd.insert(cmd.index("--onefile"), "--windowed")

    print(f"Building for {SYSTEM} ({_MACHINE})...")
    subprocess.run(cmd, check=True)

    _cleanup()
    print(f"Build complete: {DIST_DIR}")


def _cleanup() -> None:
    build_dir = PROJECT_ROOT / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)

    for item in DIST_DIR.iterdir():
        if item.is_dir():
            shutil.rmtree(item)


if __name__ == "__main__":
    build()
