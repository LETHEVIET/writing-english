from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from writing_english.adapters.base import AdapterRegistry
    from writing_english.app.context import AppContext


class PluginInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @abstractmethod
    def initialize(self, app_context: AppContext) -> None: ...

    @abstractmethod
    def register_adapters(self, adapter_registry: AdapterRegistry) -> None: ...

    @abstractmethod
    def shutdown(self) -> None: ...
