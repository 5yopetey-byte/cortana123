"""Simple launcher that can be used to start the assistant in background or foreground."""
import subprocess
import sys
from pathlib import Path


def launch_detached():
    env = None
    script = Path(__file__).parent / "main.py"
    subprocess.Popen([sys.executable, str(script)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    launch_detached()
