"""Simple rule-based intent parser.

This parser recognizes explicit open/close tokens ("open", "launch", "close", etc.)
and also treats a standalone app name as an open_app intent when it matches a known
installed_apps or app_mappings candidate. It deliberately returns the raw app text to
Executor, which performs fuzzy resolution and execution.
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

        # load app candidates from settings if available
        self.app_mappings = {k.lower(): v for k, v in (self.settings.get("app_mappings", {}) or {}).items()}
        self.installed_apps = [a.lower() for a in (self.settings.get("installed_apps", []) or [])]

    def parse(self, text: str) -> Optional[Dict[str, Any]]:
        text_l = (text or "").lower().strip()
        if not text_l:
            return None

        # greetings
        for g in self.commands.get("greetings", []):
            if g in text_l:
                return {"intent": "greet", "text": text}

        # open app (explicit tokens)
        for token in self.commands.get("open_app", []):
            if token in text_l:
                parts = text_l.split()
                try:
                    idx = parts.index(token)
                    app_name = " ".join(parts[idx + 1 :]).strip() or None
                except ValueError:
                    app_name = None
                if app_name:
                    return {"intent": "open_app", "app": app_name, "text": text}

        # close app (explicit tokens)
        for token in self.commands.get("close_app", []):
            if token in text_l:
                parts = text_l.split()
                try:
                    idx = parts.index(token)
                    app_name = " ".join(parts[idx + 1 :]).strip() or None
                except ValueError:
                    app_name = None
                if app_name:
                    return {"intent": "close_app", "app": app_name, "text": text}

        # system status
        for token in self.commands.get("system_status", []):
            if token in text_l:
                return {"intent": "system_status", "text": text}

        # If user utterance is a single word or short phrase that matches a known app name,
        # treat it as an open_app request (e.g., user says "gmail" or "spotify"). This helps
        # when people omit the word "open".
        candidate = text_l
        # direct mapping key match
        if candidate in self.app_mappings:
            return {"intent": "open_app", "app": candidate, "text": text}
        # installed apps direct match
        if candidate in self.installed_apps:
            return {"intent": "open_app", "app": candidate, "text": text}

        # fallback: if the phrase contains a known app token as a word, return open_app
        tokens = candidate.split()
        for t in tokens:
            if t in self.app_mappings or t in self.installed_apps:
                return {"intent": "open_app", "app": candidate, "text": text}

        # fallback: general query detection
        if text_l.startswith("what is") or text_l.startswith("what's"):
            return {"intent": "query", "text": text}

        return None
