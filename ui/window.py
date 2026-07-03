"""Simple Pygame CE avatar window with idle/listening/speaking states."""

import threading
import time
from typing import Dict, Optional

import pygame

from core.logger import get_logger

LOGGER = get_logger("ui")


class AvatarWindow:
    def __init__(self, settings: Optional[Dict] = None):
        self.settings = settings or {}
        ui_cfg = self.settings.get("ui", {})
        self.width = ui_cfg.get("width", 480)
        self.height = ui_cfg.get("height", 240)
        self._state = "idle"  # idle, listening, speaking
        self._thread = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def set_state(self, state: str) -> None:
        self._state = state

    def stop(self) -> None:
        self._running = False

    def _run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Cortana Local")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont(None, 28)
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False

            screen.fill((10, 10, 30))
            # draw a simple circle avatar
            color = {"idle": (100, 160, 255), "listening": (255, 200, 50), "speaking": (120, 255, 140)}.get(
                self._state, (100, 160, 255)
            )
            pygame.draw.circle(screen, color, (self.width // 2, self.height // 2), min(self.width, self.height) // 4)
            # state text
            txt = font.render(self._state.upper(), True, (255, 255, 255))
            screen.blit(txt, (10, 10))
            pygame.display.flip()
            clock.tick(30)
        pygame.quit()
