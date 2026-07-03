"""Plugin manager: loads python packages from plugins/ directory.

Each plugin may implement a register(executor) function to extend executor or register commands.
"""
import importlib.util
import importlib
from pathlib import Path
from typing import Dict, Optional
from core.logger import get_logger

LOGGER = get_logger("plugins")


class PluginManager:
    def __init__(self, settings: Optional[Dict] = None, executor=None) -> None:
        self.settings = settings or {}
        self.plugins_dir = Path("plugins")
        self.executor = executor
        self.loaded = {}

    def load_plugins(self) -> None:
        self.plugins_dir.mkdir(exist_ok=True)
        for child in self.plugins_dir.iterdir():
            if child.is_dir() and (child / "__init__.py").exists():
                name = child.name
                try:
                    module = importlib.import_module(f"plugins.{name}")
                    if hasattr(module, "register"):
                        module.register(self.executor)
                    self.loaded[name] = module
                    LOGGER.info("Loaded plugin: %s", name)
                except Exception as exc:
                    LOGGER.exception("Failed to load plugin %s: %s", name, exc)
