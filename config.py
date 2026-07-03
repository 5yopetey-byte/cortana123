"""Configuration loader utilities."""
import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_settings(path: Optional[str] = None) -> Dict[str, Any]:
    config_path = Path(path or "config/settings.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Settings file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)
