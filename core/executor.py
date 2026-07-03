"""Executor routes parsed intents to command modules and handles dry_run safety."""
import importlib
import shlex
import subprocess
from typing import Any, Dict, Optional

from core.logger import get_logger
from core.tts import TTSEngine

LOGGER = get_logger("executor")


class Executor:
    def __init__(self, settings: Optional[Dict] = None, tts: Optional[TTSEngine] = None) -> None:
        self.settings = settings or {}
        self.dry_run = bool(self.settings.get("dry_run", True))
        self.tts = tts

    def execute(self, intent: Dict[str, Any]) -> Optional[str]:
        name = intent.get("intent")
        if not name:
            return "I couldn't determine the intent."
        # Map known intents to modules
        if name == "greet":
            return "Hello. I'm ready."
        if name == "open_app":
            app = intent.get("app") or "application"
            return self._open_app(app)
        if name == "close_app":
            app = intent.get("app") or "application"
            return self._close_app(app)
        if name == "system_status":
            return self._system_status()
        if name == "query":
            return "I can't answer general queries offline yet."
        return "This command is not implemented."

    def _open_app(self, app_name: str) -> str:
        if self.dry_run:
            LOGGER.info("[dry_run] Would open: %s", app_name)
            return f"(dry-run) Would open {app_name}"
        try:
            # naive attempt: use 'xdg-open' for file/URL or run app_name as command
            subprocess.Popen(shlex.split(app_name))
            return f"Opened {app_name}"
        except Exception as exc:
            LOGGER.exception("Failed to open %s: %s", app_name, exc)
            return f"Failed to open {app_name}: {exc}"

    def _close_app(self, app_name: str) -> str:
        if self.dry_run:
            LOGGER.info("[dry_run] Would close: %s", app_name)
            return f"(dry-run) Would close {app_name}"
        try:
            # naive: pkill by name
            subprocess.run(["pkill", "-f", app_name])
            return f"Closed {app_name}"
        except Exception as exc:
            LOGGER.exception("Failed to close %s: %s", app_name, exc)
            return f"Failed to close {app_name}: {exc}"

    def _system_status(self) -> str:
        # lightweight status using psutil if available
        try:
            import psutil  # type: ignore
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            return f"CPU {cpu:.0f} percent, memory {mem.percent:.0f} percent used."
        except Exception:
            return "System status unavailable (psutil not installed)."
