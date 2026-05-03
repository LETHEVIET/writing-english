from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    pass


class GECError(TypedDict):
    start: int
    length: int
    original: str
    suggestion: str
    message: str
    category: str


class GECAdapter(ABC):
    @abstractmethod
    def check(self, text: str) -> list[GECError]: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: str) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class AdapterRegistry:
    def __init__(self) -> None:
        self._gec: GECAdapter | None = None
        self._llm: LLMAdapter | None = None

    def register_gec(self, adapter: GECAdapter) -> None:
        self._gec = adapter

    def get_gec(self) -> GECAdapter | None:
        return self._gec

    def register_llm(self, adapter: LLMAdapter) -> None:
        self._llm = adapter

    def get_llm(self) -> LLMAdapter | None:
        return self._llm
