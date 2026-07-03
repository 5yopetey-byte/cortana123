"""Wakeword detector with a safe fallback.

Primary attempt: OpenWakeWord (if installed & configured).
Fallback: console-enter key (developer mode) — press Enter to trigger.
"""
import threading
import shutil
import subprocess
import sys
import time
from typing import Dict, Optional

from core.logger import get_logger

LOGGER = get_logger("wakeword")


class WakeWordDetector:
    def __init__(self, settings: Optional[Dict] = None) -> None:
        self.settings = settings or {}
        self._wake_event = threading.Event()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._use_openwake = bool(shutil.which("openwakeword"))

    def _openwake_thread(self):
        # This is a minimal wrapper: adjust for your OpenWakeWord CLI usage.
        cmd = ["openwakeword", "--model", self.settings.get("openwakeword_model", "assets/wakeword/model.pmdl")]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except Exception as exc:
            LOGGER.warning("Failed to start openwakeword: %s", exc)
            return

        for line in proc.stdout or []:
            if not self._running:
                break
            line = line.strip()
            if "detected" in line.lower():
                LOGGER.debug("OpenWakeWord signalled detection")
                self._wake_event.set()

        proc.terminate()

    def _fallback_thread(self):
        # Developer-friendly fallback: press Enter to simulate wakeword
        LOGGER.info("Fallback wakeword active. Press Enter to trigger the assistant.")
        while self._running:
            try:
                # Blocking read — good for low CPU usage
                input()
                if not self._running:
                    break
                LOGGER.debug("Fallback wakeword triggered by Enter")
                self._wake_event.set()
            except EOFError:
                time.sleep(0.1)

    def start(self):
        if self._running:
            return
        self._running = True
        if self._use_openwake:
            LOGGER.info("Using OpenWakeWord for wakeword detection")
            self._thread = threading.Thread(target=self._openwake_thread, daemon=True)
        else:
            LOGGER.info("OpenWakeWord not found — using Enter fallback for wakeword")
            self._thread = threading.Thread(target=self._fallback_thread, daemon=True)
        self._thread.start()

    def wait_for_wake(self, timeout: Optional[float] = None) -> bool:
        fired = self._wake_event.wait(timeout)
        if fired:
            self._wake_event.clear()
        return fired

    def stop(self) -> None:
        self._running = False
        # unblock input() by writing to stdin if possible (not necessary normally)
        self._wake_event.set()
