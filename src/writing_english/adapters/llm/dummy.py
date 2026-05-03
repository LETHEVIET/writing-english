from __future__ import annotations

from writing_english.adapters.base import LLMAdapter


class DummyLLMAdapter(LLMAdapter):
    def generate(self, prompt: str, context: str) -> str:
        return ""

    def is_available(self) -> bool:
        return True
