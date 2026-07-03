"""TTS wrapper: prefer Piper CLI if available, fallback to pyttsx3."""
from typing import Dict, Optional
import shutil
import subprocess
import tempfile
import os

from core.logger import get_logger

LOGGER = get_logger("tts")

try:
    import pyttsx3  # type: ignore
    PYTTSX3_AVAILABLE = True
except Exception:
    PYTTSX3_AVAILABLE = False


class TTSEngine:
    def __init__(self, settings: Optional[Dict] = None) -> None:
        self.settings = settings or {}
        self.piper_cmd = self.settings.get("voice", {}).get("piper_cmd", "piper")
        self.use_piper = bool(shutil.which(self.piper_cmd))
        self.pytt_engine = None
        if not self.use_piper and PYTTSX3_AVAILABLE:
            self.pytt_engine = pyttsx3.init()
            rate = self.settings.get("voice", {}).get("pyttsx3_rate", 150)
            self.pytt_engine.setProperty("rate", rate)
            volume = self.settings.get("voice", {}).get("volume", 0.9)
            self.pytt_engine.setProperty("volume", volume)

    def speak(self, text: str) -> None:
        if not text:
            return
        if self.use_piper:
            self._speak_piper(text)
            return
        if self.pytt_engine:
            self.pytt_engine.say(text)
            self.pytt_engine.runAndWait()
            return
        # Last resort: print
        LOGGER.info("TTS: %s", text)

    def _speak_piper(self, text: str) -> None:
        # Use piper CLI to synthesize to a temp file then play via aplay or simpleaudio
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
                out_path = fh.name
            cmd = [self.piper_cmd, "--voice", "en_us", "--text", text, "--out", out_path]
            subprocess.run(cmd, check=True)
            # play via aplay if available, else fallback to pyttsx3 if installed
            if shutil.which("aplay"):
                subprocess.run(["aplay", out_path])
            else:
                # fallback: pyttsx3 or print
                if PYTTSX3_AVAILABLE:
                    if not self.pytt_engine:
                        self.pytt_engine = __import__("pyttsx3").init()
                    self.pytt_engine.say(text)
                    self.pytt_engine.runAndWait()
                else:
                    LOGGER.info("Synthesized TTS file at %s (no player found).", out_path)
        except Exception as exc:
            LOGGER.warning("Piper TTS failed: %s", exc)
            if PYTTSX3_AVAILABLE:
                if not self.pytt_engine:
                    self.pytt_engine = __import__("pyttsx3").init()
                self.pytt_engine.say(text)
                self.pytt_engine.runAndWait()
