"""System commands (safe defaults)."""
from typing import Optional
from core.logger import get_logger
import shutil
import subprocess

LOGGER = get_logger("commands.system")


def get_status() -> str:
    try:
        import psutil  # type: ignore
        cpu = psutil.cpu_percent(interval=0.2)
        mem = psutil.virtual_memory()
        return f"CPU {cpu:.0f} percent. Memory {mem.percent:.0f} percent used."
    except Exception:
        return "System monitoring is not available (psutil missing)."


def shutdown(dry_run: bool = True) -> str:
    if dry_run:
        LOGGER.info("Shutdown requested (dry run).")
        return "(dry-run) Would shut down the system."
    if shutil.which("systemctl"):
        subprocess.run(["systemctl", "poweroff"])
        return "Shutting down."
    else:
        return "No supported shutdown command found."
