"""Entry point for Cortana Local prototype.

Loop:
- start UI
- start wakeword detector
- on wakeword: record/listen -> stt -> parse -> execute -> tts
"""
import argparse
import threading
import time
from typing import Optional

from core.logger import get_logger
from core.speech import SpeechEngine
from core.tts import TTSEngine
from core.parser import IntentParser
from core.executor import Executor
from core.wakeword import WakeWordDetector
from core.plugins import PluginManager
from ui.window import AvatarWindow
from config import load_settings

LOGGER = get_logger("main")


def run_loop(settings_path: Optional[str] = None) -> None:
    settings = load_settings(settings_path)
    LOGGER.info("Starting Cortana Local prototype")
    tts = TTSEngine(settings)
    speech = SpeechEngine(settings)
    parser = IntentParser(settings)
    executor = Executor(settings, tts=tts)
    plugin_mgr = PluginManager(settings, executor=executor)
    plugin_mgr.load_plugins()

    ui = AvatarWindow(settings) if settings.get("ui", {}).get("enabled", True) else None
    if ui:
        ui.start()

    # Wakeword detector runs in a separate thread so the main loop can block on speech
    wake_detector = WakeWordDetector(settings)

    try:
        wake_detector.start()
        while True:
            LOGGER.debug("Waiting for wakeword...")
            wake_detector.wait_for_wake()
            LOGGER.info("Wakeword detected; listening...")
            if ui:
                ui.set_state("listening")
            text = speech.listen()
            LOGGER.info("Heard: %s", text)
            if not text:
                tts.speak("I didn't catch that.")
                if ui:
                    ui.set_state("idle")
                continue

            intent = parser.parse(text)
            LOGGER.debug("Parsed intent: %s", intent)
            if intent:
                result = executor.execute(intent)
                if isinstance(result, str):
                    tts.speak(result)
                elif result is None:
                    # executor already handled speaking
                    pass
                else:
                    tts.speak("Done.")
            else:
                tts.speak("I did not understand that command.")

            if ui:
                ui.set_state("idle")

    except KeyboardInterrupt:
        LOGGER.info("Shutting down (KeyboardInterrupt)")
    finally:
        wake_detector.stop()
        if ui:
            ui.stop()
        LOGGER.info("Exited.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", help="Path to settings.json", default="config/settings.json")
    args = parser.parse_args()
    run_loop(args.config)


if __name__ == "__main__":
    main()
