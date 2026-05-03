from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml


FRONTMATTER_KEYS = {
    "prompt",
    "created",
    "last_modified",
    "session_duration",
    "total_words",
}


@dataclass
class Document:
    path: Optional[Path] = None
    prompt: Optional[str] = None
    content: str = ""
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    session_duration: int = 0
    total_words: int = 0
    _extra_frontmatter: dict[str, object] = field(default_factory=dict)
    _is_modified: bool = False

    @property
    def is_modified(self) -> bool:
        return self._is_modified

    @is_modified.setter
    def is_modified(self, value: bool) -> None:
        self._is_modified = value

    @property
    def display_name(self) -> str:
        if self.path:
            return self.path.stem
        return "Untitled"

    def mark_saved(self) -> None:
        self._is_modified = False

    def to_frontmatter(self) -> str:
        data: dict[str, object] = {}
        if self.prompt is not None:
            data["prompt"] = self.prompt
        data["created"] = self.created.isoformat()
        data["last_modified"] = datetime.now(timezone.utc).isoformat()
        data["session_duration"] = self.session_duration
        data["total_words"] = self.total_words
        data.update(self._extra_frontmatter)
        return (
            "---\n"
            + str(yaml.dump(data, allow_unicode=True, sort_keys=False))
            + "---\n"
        )

    def serialize(self) -> str:
        return self.to_frontmatter() + self.content

    @classmethod
    def parse(cls, text: str) -> Document:
        doc = cls()
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end != -1:
                raw = text[4:end]
                try:
                    data: dict[str, object] = yaml.safe_load(raw) or {}
                except yaml.YAMLError:
                    doc.content = text
                    return doc

                for key in FRONTMATTER_KEYS:
                    val = data.pop(key, None)
                    if key == "prompt":
                        doc.prompt = str(val) if val is not None else None
                    elif key == "created" and val is not None:
                        doc.created = _parse_iso(str(val))
                    elif key == "last_modified" and val is not None:
                        doc.last_modified = _parse_iso(str(val))
                    elif key == "session_duration" and val is not None:
                        doc.session_duration = int(str(val))
                    elif key == "total_words" and val is not None:
                        doc.total_words = int(str(val))

                doc._extra_frontmatter = data
                doc.content = text[end + 6 :]
                return doc
        doc.content = text
        return doc

    @classmethod
    def from_file(cls, path: Path) -> Document:
        text = path.read_text(encoding="utf-8")
        doc = cls.parse(text)
        doc.path = path
        return doc

    def save(self, path: Optional[Path] = None) -> None:
        target = path or self.path
        if target is None:
            raise ValueError("No path specified")
        self.last_modified = datetime.now(timezone.utc)
        target.write_text(self.serialize(), encoding="utf-8")
        self.path = target
        self._is_modified = False

    def update_word_count(self) -> None:
        self.total_words = len(self.content.split()) if self.content.strip() else 0


def _parse_iso(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return datetime.now(timezone.utc)
