from __future__ import annotations

from writing_english.adapters.base import GECAdapter, GECError


class DummyGECAdapter(GECAdapter):
    def check(self, text: str) -> list[GECError]:
        return []

    def is_available(self) -> bool:
        return True
