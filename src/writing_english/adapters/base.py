from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class GECAdapter(ABC):
    @abstractmethod
    def check(self, text: str) -> list[dict[str, object]]: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: str) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class SpellCheckAdapter(ABC):
    @abstractmethod
    def check(self, text: str) -> list[dict[str, object]]: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class AdapterRegistry:
    def __init__(self) -> None:
        self._gec: GECAdapter | None = None
        self._llm: LLMAdapter | None = None
        self._spellcheck: SpellCheckAdapter | None = None

    def register_gec(self, adapter: GECAdapter) -> None:
        self._gec = adapter

    def get_gec(self) -> GECAdapter | None:
        return self._gec

    def register_llm(self, adapter: LLMAdapter) -> None:
        self._llm = adapter

    def get_llm(self) -> LLMAdapter | None:
        return self._llm

    def register_spellcheck(self, adapter: SpellCheckAdapter) -> None:
        self._spellcheck = adapter

    def get_spellcheck(self) -> SpellCheckAdapter | None:
        return self._spellcheck
