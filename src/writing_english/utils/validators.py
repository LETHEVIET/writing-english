from __future__ import annotations


def is_valid_prompt(text: str) -> bool:
    return len(text.strip()) > 0


def is_safe_filename(name: str) -> bool:
    forbidden = {"<", ">", ":", '"', "/", "\\", "|", "?", "*"}
    return bool(name) and not forbidden.intersection(name)
