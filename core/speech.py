"""Speech engine wrapper: prefer Vosk offline recognition if installed and a model is available.

Fallback: read from stdin (developer mode).
"""
from typing import Dict, Optional
import shutil
import os
import wave
import sys
from core.logger import get_logger

LOGGER = get_logger("speech")

try:
    from vosk import Model, KaldiRecognizer  # type: ignore
    import pyaudio  # type: ignore
    VOSK_AVAILABLE = True
except Exception:
    VOSK_AVAILABLE = False
    LOGGER.info("Vosk or PyAudio not available; speech.listen() will fall back to console input.")


class SpeechEngine:
    def __init__(self, settings: Optional[Dict] = None) -> None:
        self.settings = settings or {}
        self.model_path = self.settings.get("vosk_model_path", "assets/models/vosk")
        self.model = None
        if VOSK_AVAILABLE and os.path.isdir(self.model_path):
            try:
                self.model = Model(self.model_path)
                LOGGER.info("Loaded Vosk model from %s", self.model_path)
            except Exception as exc:  # pragma: no cover - environment dependent
                LOGGER.warning("Failed to load Vosk model: %s", exc)
                self.model = None
        else:
            if VOSK_AVAILABLE:
                LOGGER.warning("Vosk installed but model directory not found at %s", self.model_path)

    def listen(self, timeout: Optional[float] = 5.0) -> Optional[str]:
        """Listen from microphone and return a best-guess text string.

        If Vosk is not available or model missing, fallback to console input.
        """
        if self.model:
            try:
                return self._listen_vosk(timeout=timeout)
            except Exception as exc:  # pragma: no cover - audio not always available
                LOGGER.exception("Error during Vosk recognition: %s", exc)
                return None

        # Fallback: console input (developer mode)
        LOGGER.info("Speech fallback: type your phrase and press Enter")
        try:
            return input("> ").strip()
        except EOFError:
            return None

    def _listen_vosk(self, timeout: Optional[float] = 5.0) -> Optional[str]:
        import pyaudio  # type: ignore
        rec = KaldiRecognizer(self.model, 16000)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()
        LOGGER.debug("Listening for speech (Vosk)...")
        collected = []
        import time
        start_ts = time.time()
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                res = rec.Result()
                import json
                text = json.loads(res).get("text", "")
                stream.stop_stream()
                stream.close()
                p.terminate()
                return text
            if timeout and (time.time() - start_ts) > timeout:
                # timed out: try partial
                res = rec.FinalResult()
                import json
                text = json.loads(res).get("text", "")
                stream.stop_stream()
                stream.close()
                p.terminate()
                return text
