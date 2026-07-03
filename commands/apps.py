"""Application control helpers (open/close apps)."""
import subprocess
from typing import Optional
from core.logger import get_logger

LOGGER = get_logger("commands.apps")


def open_app(command: str) -> str:
    try:
        subprocess.Popen(command.split())
        return f"Opening {command}"
    except Exception as exc:
        LOGGER.exception("open_app failed: %s", exc)
        return f"Failed to open {command}: {exc}"


def close_app(name: str) -> str:
    try:
        subprocess.run(["pkill", "-f", name])
        return f"Closed {name}"
    except Exception as exc:
        LOGGER.exception("close_app failed: %s", exc)
        return f"Failed to close {name}: {exc}"
