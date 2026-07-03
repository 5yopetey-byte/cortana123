"""Simple rule-based intent parser.

This is intentionally small and deterministic for low-latency operation.
"""
from typing import Dict, Any, Optional
import json
from pathlib import Path
from core.logger import get_logger

LOGGER = get_logger("parser")


class IntentParser:
    def __init__(self, settings: Optional[Dict] = None) -> None:
        self.settings = settings or {}
        self.commands_path = Path("config/commands.json")
        try:
            with self.commands_path.open("r", encoding="utf-8") as fh:
                self.commands = json.load(fh)
        except Exception:
            self.commands = {}

    def parse(self, text: str) -> Optional[Dict[str, Any]]:
        text_l = text.lower().strip()
        # greetings
        for g in self.commands.get("greetings", []):
            if g in text_l:
                return {"intent": "greet", "text": text}
        # open app
        for token in self.commands.get("open_app", []):
            if token in text_l:
                # naive: last word app name
                parts = text_l.split()
                # attempt to extract app name after token
                try:
                    idx = parts.index(token)
                    app_name = " ".join(parts[idx + 1 :]) or None
                except ValueError:
                    app_name = None
                return {"intent": "open_app", "app": app_name, "text": text}
        # close app
        for token in self.commands.get("close_app", []):
            if token in text_l:
                parts = text_l.split()
                try:
                    idx = parts.index(token)
                    app_name = " ".join(parts[idx + 1 :]) or None
                except ValueError:
                    app_name = None
                return {"intent": "close_app", "app": app_name, "text": text}
        # system status
        for token in self.commands.get("system_status", []):
            if token in text_l:
                return {"intent": "system_status", "text": text}
        # fallback: simple intent guessing
        if text_l.startswith("what is") or text_l.startswith("what's"):
            return {"intent": "query", "text": text}
        return None
