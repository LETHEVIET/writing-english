from __future__ import annotations

from pathlib import Path

from writing_english.adapters.base import AdapterRegistry
from writing_english.app.context import AppContext
from writing_english.plugins.interface import PluginInterface


class PluginHost:
    def __init__(self) -> None:
        self._plugins: list[PluginInterface] = []
        self._adapter_registry = AdapterRegistry()

    def load_plugins(self, plugins_dir: Path) -> None:
        if not plugins_dir.exists():
            return
        for path in plugins_dir.iterdir():
            if path.suffix == ".py" and not path.name.startswith("_"):
                self._load_plugin(path)

    def _load_plugin(self, path: Path) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PluginInterface)
                and attr is not PluginInterface
            ):
                plugin = attr()
                self._plugins.append(plugin)

    def initialize_all(self, app_context: AppContext) -> None:
        for plugin in self._plugins:
            plugin.initialize(app_context)
            plugin.register_adapters(self._adapter_registry)

    def shutdown_all(self) -> None:
        for plugin in self._plugins:
            plugin.shutdown()

    @property
    def adapter_registry(self) -> AdapterRegistry:
        return self._adapter_registry
