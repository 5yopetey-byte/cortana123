"""Media controls (playerctl wrapper if available)."""
import shutil
import subprocess
from core.logger import get_logger

LOGGER = get_logger("commands.media")


def play_pause() -> str:
    if shutil.which("playerctl"):
        subprocess.run(["playerctl", "play-pause"])
        return "Toggled play/pause."
    return "playerctl not available."
