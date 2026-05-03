from __future__ import annotations

from pathlib import Path


class FileSystem:
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def exists(self, path: Path) -> bool:
        return path.exists()

    def list_markdown_files(self, directory: Path) -> list[Path]:
        if not directory.exists():
            return []
        return sorted(
            [
                p
                for p in directory.iterdir()
                if p.suffix == ".md" and not p.name.startswith(".")
            ]
        )
