"""Clipboard helper using pyperclip."""
from typing import Optional
from core.logger import get_logger

LOGGER = get_logger("commands.clipboard")

try:
    import pyperclip  # type: ignore
except Exception:
    pyperclip = None


def copy(text: str) -> str:
    if not pyperclip:
        return "Clipboard functionality unavailable."
    pyperclip.copy(text)
    return "Copied to clipboard."

def paste() -> str:
    if not pyperclip:
        return "Clipboard functionality unavailable."
    return pyperclip.paste() or ""
