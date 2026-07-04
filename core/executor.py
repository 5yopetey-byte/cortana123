"""Executor routes parsed intents to command modules and handles dry_run safety.

Enhanced: resolves fuzzy app names using app_mappings and installed_apps, uses RapidFuzz if available,
and requires confirmation for low-confidence matches unless configured otherwise.
"""
import shlex
import subprocess
import shutil
from typing import Any, Dict, Optional, Tuple

from core.logger import get_logger
from core.tts import TTSEngine

# attempt to import RapidFuzz; fall back gracefully
try:
    from rapidfuzz import process, fuzz  # type: ignore
    RAPIDFUZZ_AVAILABLE = True
except Exception:
    RAPIDFUZZ_AVAILABLE = False

LOGGER = get_logger("executor")


class Executor:
    def __init__(self, settings: Optional[Dict] = None, tts: Optional[TTSEngine] = None) -> None:
        self.settings = settings or {}
        self.dry_run = bool(self.settings.get("dry_run", True))
        self.tts = tts
        # confidence threshold (0-100) for fuzzy matches
        self._fuzzy_threshold = int(self.settings.get("fuzzy_threshold", 65))
        # allow executing raw commands (dangerous); default false unless set in settings
        self._allow_raw = bool(self.settings.get("allow_raw_execution", False))
        self._require_confirm_unknown = bool(self.settings.get("require_confirmation_for_unknown", True))

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

    def _resolve_target(self, user_text: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """
        Resolve user_text to (matched_key, mapped_command_or_value, score).
        - matched_key is the canonical candidate string (lowercase).
        - mapped_command_or_value is the command to execute (may be same as matched_key).
        - score is matching score (0-100) or None.
        """
        if not user_text:
            return None, None, None
        query = user_text.strip().lower()

        # Build candidate list (lowercased)
        mappings: Dict[str, str] = {k.lower(): v for k, v in self.settings.get("app_mappings", {}).items()}
        installed = [a.lower() for a in self.settings.get("installed_apps", [])]
        candidates = list(dict.fromkeys(list(mappings.keys()) + installed))  # preserve order, dedupe

        # If no candidates, short-circuit
        if not candidates:
            return None, None, None

        # 1) Try exact substring match (fast)
        for c in candidates:
            if c == query or c in query or query in c:
                mapped = mappings.get(c) or c
                return c, mapped, 100

        # 2) Try fuzzy matching if available
        if RAPIDFUZZ_AVAILABLE:
            try:
                best = process.extractOne(query, candidates, scorer=fuzz.WRatio)
                if best:
                    matched, score, _idx = best  # matched is candidate (already lowercased)
                    matched = matched.lower()
                    mapped = mappings.get(matched) or matched
                    return matched, mapped, int(score)
            except Exception as exc:
                LOGGER.debug("RapidFuzz matching error: %s", exc)

        # 3) Fallback: simple token overlap scoring (lightweight)
        def token_score(a: str, b: str) -> int:
            aset = set(a.split())
            bset = set(b.split())
            common = aset & bset
            if not aset:
                return 0
            return int(100 * len(common) / max(len(aset), 1))

        best_match = None
        best_score = 0
        for c in candidates:
            s = token_score(query, c)
            if s > best_score:
                best_score = s
                best_match = c
        if best_match:
            mapped = mappings.get(best_match) or best_match
            return best_match, mapped, int(best_score)

        return None, None, None

    def _open_app(self, app_name: str) -> str:
        app_name = (app_name or "").strip()
        if not app_name:
            return "No application specified."

        # Resolve target
        matched, cmd, score = self._resolve_target(app_name)

        # If matched and high confidence, use it
        if matched and (score is None or score >= self._fuzzy_threshold):
            chosen_cmd = cmd
            LOGGER.info("Resolved '%s' -> '%s' (score=%s)", app_name, chosen_cmd, score)
        elif matched:
            # ambiguous/low confidence
            LOGGER.info("Low-confidence match for '%s' -> '%s' (score=%s)", app_name, cmd, score)
            if self._require_confirm_unknown:
                # ask for confirmation via TTS/console
                prompt = f"I think you meant {matched}. Say yes to open it."
                if self.tts:
                    self.tts.speak(prompt)
                # fallback confirmation via console
                try:
                    reply = input(f"{prompt} [y/N]: ").strip().lower()
                except Exception:
                    reply = "n"
                if reply not in ("y", "yes"):
                    return "Cancelled."
            chosen_cmd = cmd
        else:
            # No good match
            if not self._allow_raw:
                return f"Unknown application '{app_name}'. I won't run arbitrary commands. Add it to app_mappings or installed_apps to allow launching."
            chosen_cmd = app_name  # user explicitly allowed raw execution

        # If command starts with 'xdg-open ' treat as such; else execute
        if chosen_cmd.startswith("xdg-open "):
            parts = shlex.split(chosen_cmd)
            exec_cmd = parts
        else:
            # split where appropriate
            if " " in chosen_cmd:
                exec_cmd = shlex.split(chosen_cmd)
            else:
                exec_cmd = [chosen_cmd]

        if self.dry_run:
            LOGGER.info("[dry_run] Would run: %s", exec_cmd)
            return f"(dry-run) Would open {app_name} -> {' '.join(exec_cmd)}"

        try:
            subprocess.Popen(exec_cmd)
            return f"Opened {app_name}"
        except FileNotFoundError:
            # try xdg-open fallback
            try:
                subprocess.Popen(["xdg-open", app_name])
                return f"Opened {app_name} with xdg-open"
            except Exception as exc:
                LOGGER.exception("Failed to open %s: %s", app_name, exc)
                return f"Failed to open {app_name}: {exc}"
        except Exception as exc:
            LOGGER.exception("Failed to open %s: %s", app_name, exc)
            return f"Failed to open {app_name}: {exc}"

    def _close_app(self, app_name: str) -> str:
        app_name = (app_name or "").strip()
        if not app_name:
            return "No application specified."

        matched, cmd, score = self._resolve_target(app_name)
        target_name = matched or app_name

        if self.dry_run:
            LOGGER.info("[dry_run] Would close: %s", target_name)
            return f"(dry-run) Would close {target_name}"

        # Try pkill first (process name)
        try:
            subprocess.run(["pkill", "-f", target_name])
            return f"Closed {target_name}"
        except Exception as exc:
            LOGGER.warning("pkill failed for %s: %s", target_name, exc)

        # Try wmctrl to close windows by title if installed
        if shutil.which("wmctrl"):
            try:
                out = subprocess.check_output(["wmctrl", "-l"]).decode("utf-8", errors="ignore")
                for line in out.splitlines():
                    if target_name.lower() in line.lower():
                        win_id = line.split()[0]
                        subprocess.run(["wmctrl", "-ic", win_id])
                return f"Attempted to close windows matching {target_name}"
            except Exception as exc:
                LOGGER.exception("wmctrl-based close failed: %s", exc)

        return f"Unable to close {target_name} (no supported method succeeded)."

    def _system_status(self) -> str:
        # lightweight status using psutil if available
        try:
            import psutil  # type: ignore
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            return f"CPU {cpu:.0f} percent, memory {mem.percent:.0f} percent used."
        except Exception:
            return "System status unavailable (psutil not installed)."
