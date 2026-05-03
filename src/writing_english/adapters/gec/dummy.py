from __future__ import annotations

from writing_english.adapters.base import GECAdapter


class DummyGECAdapter(GECAdapter):
    def check(self, text: str) -> list[dict[str, object]]:
        return []

    def is_available(self) -> bool:
        return True
