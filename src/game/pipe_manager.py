"""
Sistema de tuberías (obstáculos).

Cada par de tuberías (arriba + abajo) se representa con la clase Pipe.
PipeManager controla el spawn, movimiento y limpieza.

Para reemplazar el gráfico de los tubos basta con poner un nuevo pipe.png
en assets/images/pipes/ — el sistema lo carga automáticamente.
"""
from __future__ import annotations

import random

import pygame

from utils.asset_loader import AssetLoader


class Pipe:
    """Par de tuberías (superior e inferior) con un hueco en el centro."""

    _HITBOX_SHRINK = 3  # píxeles de margen para juego justo

    def __init__(
        self,
        x: float,
        gap_center_y: int,
        gap_height: int,
        screen_h: int,
        ground_h: int,
        pipe_img: pygame.Surface,
        pipe_img_flipped: pygame.Surface,
    ) -> None:
        self.x = x
        self.gap_center_y = gap_center_y
        self._gap_half = gap_height // 2
        self._screen_h = screen_h
        self._ground_h = ground_h
        self._img = pipe_img
        self._img_flip = pipe_img_flipped
        self._pipe_w = pipe_img.get_width()
        self._pipe_h = pipe_img.get_height()
        self.passed = False

        # Bordes del hueco
        self._gap_top: int = gap_center_y - self._gap_half
        self._gap_bot: int = gap_center_y + self._gap_half

        self._update_rects()

    # ------------------------------------------------------------------ #
    # Update / Draw
    # ------------------------------------------------------------------ #

    def update(self, speed: float) -> None:
        self.x -= speed
        self._update_rects()

    def draw(self, screen: pygame.Surface) -> None:
        px = int(self.x)

        # Tubo inferior: tapa en la parte superior (= borde del hueco)
        screen.blit(self._img, (px, self._gap_bot))

        # Tubo superior: imagen volteada → tapa en la parte inferior (= borde del hueco)
        # Se posiciona para que el borde inferior del surface coincida con gap_top
        screen.blit(self._img_flip, (px, self._gap_top - self._pipe_h))

    # ------------------------------------------------------------------ #
    # Consultas
    # ------------------------------------------------------------------ #

    def collides_with(self, bird_rect: pygame.Rect) -> bool:
        return (
            self._top_rect.colliderect(bird_rect)
            or self._bot_rect.colliderect(bird_rect)
        )

    def check_passed(self, bird_x: float) -> bool:
        """Retorna True la primera vez que el pájaro supera este par de tubos."""
        if not self.passed and bird_x > self.x + self._pipe_w:
            self.passed = True
            return True
        return False

    def is_off_screen(self) -> bool:
        return self.x + self._pipe_w < 0

    # ------------------------------------------------------------------ #
    # Privados
    # ------------------------------------------------------------------ #

    def _update_rects(self) -> None:
        s = self._HITBOX_SHRINK
        px = int(self.x)
        pw = self._pipe_w

        # Tubería superior: de y=0 hasta gap_top
        self._top_rect = pygame.Rect(
            px + s, 0,
            pw - s * 2, self._gap_top - s,
        )
        # Tubería inferior: de gap_bot hasta el suelo
        self._bot_rect = pygame.Rect(
            px + s, self._gap_bot + s,
            pw - s * 2, self._screen_h - self._gap_bot - self._ground_h - s,
        )


class PipeManager:
    """Gestiona la creación, movimiento y eliminación de tuberías."""

    def __init__(
        self,
        assets: AssetLoader,
        screen_w: int,
        screen_h: int,
        game_cfg: dict,
    ) -> None:
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._speed: float = game_cfg["pipe_speed"]
        self._gap_height: int = game_cfg["pipe_gap"]
        self._spawn_interval: int = game_cfg["pipe_spawn_interval"]
        self._ground_h: int = game_cfg["ground_height"]
        self._margin: int = game_cfg["min_pipe_margin"]

        # Assets de tuberías
        pipe_img = assets.get_image("pipe")
        self._pipe_img: pygame.Surface = pipe_img
        self._pipe_img_flip: pygame.Surface = pygame.transform.flip(
            pipe_img, False, True
        )
        self._pipe_w: int = pipe_img.get_width()

        # Límites del centro del hueco
        half_gap = self._gap_height // 2
        self._min_gap_y = self._margin + half_gap
        self._max_gap_y = screen_h - self._ground_h - self._margin - half_gap

        self._pipes: list[Pipe] = []
        self._timer: int = 0

    # ------------------------------------------------------------------ #
    # Update / Draw
    # ------------------------------------------------------------------ #

    def update(self) -> None:
        # Generar nuevo par
        self._timer += 1
        if self._timer >= self._spawn_interval:
            self._timer = 0
            self._spawn()

        # Mover y limpiar
        for pipe in self._pipes:
            pipe.update(self._speed)
        self._pipes = [p for p in self._pipes if not p.is_off_screen()]

    def draw(self, screen: pygame.Surface) -> None:
        for pipe in self._pipes:
            pipe.draw(screen)

    # ------------------------------------------------------------------ #
    # Consultas
    # ------------------------------------------------------------------ #

    def check_collision(self, bird) -> bool:
        bird_rect = bird.get_hitbox()
        return any(p.collides_with(bird_rect) for p in self._pipes)

    def check_score(self, bird) -> bool:
        """Retorna True si el pájaro acaba de pasar algún par de tubos."""
        bird_x = bird.get_x()
        return any(p.check_passed(bird_x) for p in self._pipes)

    def reset(self) -> None:
        self._pipes.clear()
        self._timer = 0

    # ------------------------------------------------------------------ #
    # Privado
    # ------------------------------------------------------------------ #

    def _spawn(self) -> None:
        gap_y = random.randint(self._min_gap_y, self._max_gap_y)
        self._pipes.append(
            Pipe(
                x=float(self._screen_w + 10),
                gap_center_y=gap_y,
                gap_height=self._gap_height,
                screen_h=self._screen_h,
                ground_h=self._ground_h,
                pipe_img=self._pipe_img,
                pipe_img_flipped=self._pipe_img_flip,
            )
        )
