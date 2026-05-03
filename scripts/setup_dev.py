#!/usr/bin/env python3
"""One-command dev environment setup."""

import subprocess
import sys


def main() -> None:
    commands = [
        [sys.executable, "-m", "uv", "python", "install", "3.14"],
        [sys.executable, "-m", "uv", "venv", "--python", "3.14"],
        [sys.executable, "-m", "uv", "sync", "--all-extras"],
    ]
    for cmd in commands:
        subprocess.run(cmd, check=True)
    print("Setup complete.")


if __name__ == "__main__":
    main()
