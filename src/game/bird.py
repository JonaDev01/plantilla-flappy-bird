"""
Entidad del pájaro.
Maneja física (gravedad + salto), rotación visual y animación de frames.
"""
from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.asset_loader import AssetLoader


class Bird:
    # Límites de rotación (grados)
    _ROT_MAX = 30       # inclinación hacia arriba (subiendo)
    _ROT_MIN = -90      # picada (cayendo rápido)
    _ROT_SPEED_UP = 6   # grados/frame al subir
    _ROT_SPEED_DOWN = 3 # grados/frame al bajar

    # Animación
    _FRAME_SPEED = 6    # frames de juego entre cambio de fotograma

    def __init__(
        self,
        assets: "AssetLoader",
        screen_w: int,
        screen_h: int,
        game_cfg: dict,
    ) -> None:
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._gravity: float = game_cfg["gravity"]
        self._jump_strength: float = game_cfg["jump_strength"]

        # Posición y física
        self.x: float = screen_w // 4
        self.y: float = screen_h // 2
        self._vy: float = 0.0          # velocidad vertical
        self._angle: float = 0.0

        # Frames de animación
        self._frames: list[pygame.Surface] = assets.get_bird_frames()
        self._frame_idx: int = 0
        self._frame_timer: int = 0

        # Hitbox reducida para juego justo
        self._update_hitbox()
        self._jump_consumed: bool = False

    # ------------------------------------------------------------------ #
    # Update / Draw
    # ------------------------------------------------------------------ #

    def update(self, jump_pressed: bool, assets: "AssetLoader") -> None:
        # ── Física ──────────────────────────────────────────────────────
        self._vy += self._gravity
        self.y += self._vy

        # ── Salto (un único pulso por pulsación) ────────────────────────
        if jump_pressed and not self._jump_consumed:
            self._vy = self._jump_strength
            self._jump_consumed = True
            sfx = assets.get_sound("jump")
            if sfx:
                sfx.play()
        if not jump_pressed:
            self._jump_consumed = False

        # ── Rotación ────────────────────────────────────────────────────
        if self._vy < 0:
            self._angle = min(self._ROT_MAX, self._angle + self._ROT_SPEED_UP)
        else:
            self._angle = max(self._ROT_MIN, self._angle - self._ROT_SPEED_DOWN)

        # ── Animación ───────────────────────────────────────────────────
        self._frame_timer += 1
        if self._frame_timer >= self._FRAME_SPEED:
            self._frame_timer = 0
            self._frame_idx = (self._frame_idx + 1) % len(self._frames)

        self._update_hitbox()

    def draw(self, screen: pygame.Surface) -> None:
        frame = self._frames[self._frame_idx]
        rotated = pygame.transform.rotate(frame, self._angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated, rect)

        # Descomentar para depurar hitbox:
        # pygame.draw.rect(screen, (255, 0, 0), self._hitbox, 1)

    # ------------------------------------------------------------------ #
    # Consultas públicas
    # ------------------------------------------------------------------ #

    def get_hitbox(self) -> pygame.Rect:
        return self._hitbox

    def get_x(self) -> float:
        return self.x

    def is_dead(self, screen_h: int, ground_height: int) -> bool:
        """True si toca el suelo o sale por arriba."""
        return (
            self._hitbox.bottom >= screen_h - ground_height
            or self._hitbox.top <= 0
        )

    # ------------------------------------------------------------------ #
    # Privados
    # ------------------------------------------------------------------ #

    def _update_hitbox(self) -> None:
        fw = self._frames[0].get_width()
        fh = self._frames[0].get_height()
        shrink = 5          # píxeles que se reduce por lado
        self._hitbox = pygame.Rect(
            int(self.x) - fw // 2 + shrink,
            int(self.y) - fh // 2 + shrink,
            fw - shrink * 2,
            fh - shrink * 2,
        )
