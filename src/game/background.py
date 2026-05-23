"""
Fondo y suelo con scroll horizontal infinito.

Para reemplazar el fondo o el suelo:
  assets/images/background/background.png
  assets/images/ground/ground.png
"""
from __future__ import annotations

import pygame
from utils.asset_loader import AssetLoader


class Background:
    def __init__(
        self,
        assets: AssetLoader,
        screen_w: int,
        screen_h: int,
        game_cfg: dict,
    ) -> None:
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._ground_h: int = game_cfg["ground_height"]
        self._ground_y: int = screen_h - self._ground_h

        self._bg_img: pygame.Surface = assets.get_image("background")
        self._gnd_img: pygame.Surface = assets.get_image("ground")

        # Velocidades de scroll (el suelo al ritmo de los tubos; el fondo más lento)
        pipe_speed: float = game_cfg["pipe_speed"]
        self._bg_speed: float = pipe_speed * 0.25
        self._gnd_speed: float = pipe_speed

        self._bg_offset: float = 0.0
        self._gnd_offset: float = 0.0

    # ------------------------------------------------------------------ #
    # Update / Draw
    # ------------------------------------------------------------------ #

    def update(self) -> None:
        bg_w = self._bg_img.get_width()
        gnd_w = self._gnd_img.get_width()
        self._bg_offset = (self._bg_offset + self._bg_speed) % bg_w
        self._gnd_offset = (self._gnd_offset + self._gnd_speed) % gnd_w

    def draw(self, screen: pygame.Surface) -> None:
        self._tile_blit(screen, self._bg_img, -int(self._bg_offset), 0)
        self._tile_blit(screen, self._gnd_img, -int(self._gnd_offset), self._ground_y)

    # ------------------------------------------------------------------ #
    # Privados
    # ------------------------------------------------------------------ #

    def _tile_blit(
        self,
        screen: pygame.Surface,
        img: pygame.Surface,
        start_x: int,
        y: int,
    ) -> None:
        """Dibuja copias de `img` en horizontal hasta cubrir el ancho de pantalla."""
        img_w = img.get_width()
        x = start_x
        while x < self._screen_w:
            screen.blit(img, (x, y))
            x += img_w
