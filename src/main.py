"""
Plantilla FlappyBird — Punto de entrada principal.

Uso:
  python src/main.py           (desde la raíz del proyecto)
  python -m main               (desde src/)

Controles:
  ESPACIO / flecha arriba   → saltar
  F11                       → pantalla completa / ventana
  ESC                       → salir
  R (en Game Over)          → reiniciar rápido
"""
from __future__ import annotations

import sys
import os

# Asegura que las importaciones relativas funcionen
# sin importar desde qué directorio se invoque el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from utils.config import load_config
from utils.asset_loader import AssetLoader
from game.bird import Bird
from game.pipe_manager import PipeManager
from game.background import Background
from game.score import ScoreManager
from game.gpio_handler import GPIOHandler

# ────────────────────────────────────────────────────────────────────────
# Estados del juego
# ────────────────────────────────────────────────────────────────────────
MENU      = "MENU"
PLAYING   = "PLAYING"
GAME_OVER = "GAME_OVER"

# Paleta UI
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0  )
YELLOW = (255, 220, 0  )
RED    = (220, 60,  60 )
GOLD   = (255, 200, 0  )
GRAY   = (180, 180, 180)


class PlantillaFlappyBird:
    """Máquina de estados principal del juego."""

    def __init__(self) -> None:
        pygame.init()

        self._cfg = load_config()
        disp = self._cfg["display"]

        # Pantalla
        flags = pygame.FULLSCREEN if disp["fullscreen"] else 0
        self._screen = pygame.display.set_mode((disp["width"], disp["height"]), flags)
        pygame.display.set_caption(disp["title"])
        self._clock = pygame.time.Clock()
        self._fps: int = disp["fps"]
        self._show_fps: bool = disp["show_fps"]

        self._W: int = disp["width"]
        self._H: int = disp["height"]

        # Audio
        self._mixer_ok = False
        if self._cfg["audio"]["enabled"]:
            try:
                pygame.mixer.init()
                self._mixer_ok = True
            except pygame.error as exc:
                print(f"[Audio] No se pudo inicializar el mixer: {exc}")

        # Assets, GPIO, fuentes
        self._assets = AssetLoader(self._cfg)
        self._gpio   = GPIOHandler(self._cfg)
        self._init_fonts()

        # Entidades (se crean/reciclan con _reset())
        self._bg:    Background  = None   # type: ignore[assignment]
        self._bird:  Bird        = None   # type: ignore[assignment]
        self._pipes: PipeManager = None   # type: ignore[assignment]
        self._score: ScoreManager = ScoreManager()
        self._reset()

        # Música
        self._start_music()

        # Estado
        self._state: str = MENU

    # ------------------------------------------------------------------ #
    # Bucle principal
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        running = True
        while running:
            self._clock.tick(self._fps)
            jump = False

            # ── Eventos ─────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        jump = True
                    elif event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    elif event.key == pygame.K_r and self._state == GAME_OVER:
                        self._restart()

            # ── Botón GPIO ──────────────────────────────────────────────
            if self._gpio.get_jump():
                jump = True

            # ── Máquina de estados ──────────────────────────────────────
            if self._state == MENU:
                self._update_menu(jump)
            elif self._state == PLAYING:
                self._update_playing(jump)
            elif self._state == GAME_OVER:
                self._update_game_over(jump)

            # ── Renderizado ─────────────────────────────────────────────
            self._draw()
            pygame.display.flip()

        self._shutdown()

    # ------------------------------------------------------------------ #
    # Updates por estado
    # ------------------------------------------------------------------ #

    def _update_menu(self, jump: bool) -> None:
        self._bg.update()
        if jump:
            self._state = PLAYING

    def _update_playing(self, jump: bool) -> None:
        self._bg.update()
        self._bird.update(jump, self._assets)
        self._pipes.update()

        # Puntuación
        if self._pipes.check_score(self._bird):
            self._score.add_point()
            self._play_sfx("point")
            self._gpio.on_score(self._score.score)

        # Colisión o caída fuera de pantalla
        ground_h = self._cfg["game"]["ground_height"]
        if (
            self._pipes.check_collision(self._bird)
            or self._bird.is_dead(self._H, ground_h)
        ):
            self._score.save_highscore()
            self._play_sfx("die")
            self._gpio.on_game_over()
            self._state = GAME_OVER

    def _update_game_over(self, jump: bool) -> None:
        self._bg.update()
        if jump:
            self._restart()

    # ------------------------------------------------------------------ #
    # Renderizado
    # ------------------------------------------------------------------ #

    def _draw(self) -> None:
        # Fondo siempre visible
        self._bg.draw(self._screen)

        if self._state in (PLAYING, GAME_OVER):
            self._pipes.draw(self._screen)
            self._bird.draw(self._screen)

        # UI por estado
        if self._state == MENU:
            self._draw_menu()
        elif self._state == PLAYING:
            self._draw_hud()
        elif self._state == GAME_OVER:
            self._draw_game_over()

        # FPS (debug)
        if self._show_fps:
            fps_surf = self._font_sm.render(
                f"FPS: {int(self._clock.get_fps())}", True, YELLOW
            )
            self._screen.blit(fps_surf, (4, 4))

    def _draw_menu(self) -> None:
        cx = self._W // 2

        # Panel semitransparente
        panel = pygame.Surface((self._W - 60, 220), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        self._screen.blit(panel, (30, self._H // 3 - 30))

        title1 = self._font_xl.render("FLAPPY", True, YELLOW)
        title2 = self._font_xl.render("CLONE",  True, YELLOW)
        prompt  = self._font_sm.render(
            "ESPACIO / BOTÓN para iniciar", True, WHITE
        )
        rec = self._font_md.render(
            f"RÉCORD: {self._score.highscore}", True, GOLD
        )

        self._blit_centered(title1, cx, self._H // 3)
        self._blit_centered(title2, cx, self._H // 3 + 68)
        self._blit_centered(rec,    cx, self._H // 3 + 140)
        self._blit_centered(prompt, cx, self._H * 2 // 3)

    def _draw_hud(self) -> None:
        """Muestra el puntaje actual en la parte superior."""
        shadow = self._font_lg.render(str(self._score.score), True, BLACK)
        text   = self._font_lg.render(str(self._score.score), True, WHITE)
        cx = self._W // 2
        self._screen.blit(shadow, shadow.get_rect(centerx=cx + 2, top=18))
        self._screen.blit(text,   text.get_rect(centerx=cx, top=16))

    def _draw_game_over(self) -> None:
        self._draw_hud()

        # Overlay oscuro
        overlay = pygame.Surface((self._W, self._H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self._screen.blit(overlay, (0, 0))

        # Panel central
        panel_h = 240
        panel_y = self._H // 2 - panel_h // 2
        panel = pygame.Surface((self._W - 60, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 200))
        self._screen.blit(panel, (30, panel_y))

        cx = self._W // 2
        go   = self._font_lg.render("GAME OVER",             True, RED)
        pts  = self._font_md.render(f"Puntos : {self._score.score}",     True, WHITE)
        rec  = self._font_md.render(f"Récord : {self._score.highscore}", True, GOLD)
        hint = self._font_sm.render("ESPACIO / R / BOTÓN para reiniciar", True, GRAY)

        self._blit_centered(go,   cx, panel_y + 20)
        self._blit_centered(pts,  cx, panel_y + 90)
        self._blit_centered(rec,  cx, panel_y + 140)
        self._blit_centered(hint, cx, panel_y + 195)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _restart(self) -> None:
        self._reset()
        self._state = PLAYING

    def _reset(self) -> None:
        game_cfg = self._cfg["game"]
        self._bg    = Background(self._assets, self._W, self._H, game_cfg)
        self._bird  = Bird(self._assets, self._W, self._H, game_cfg)
        self._pipes = PipeManager(self._assets, self._W, self._H, game_cfg)
        self._score.reset()

    def _play_sfx(self, key: str) -> None:
        if self._mixer_ok:
            sfx = self._assets.get_sound(key)
            if sfx:
                sfx.play()

    def _start_music(self) -> None:
        if not self._mixer_ok:
            return
        path = self._assets.get_music_path()
        if path:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self._cfg["audio"]["music_volume"])
                pygame.mixer.music.play(-1)
            except pygame.error as exc:
                print(f"[Audio] No se pudo cargar la música: {exc}")

    def _shutdown(self) -> None:
        self._gpio.cleanup()
        pygame.quit()
        sys.exit(0)

    def _init_fonts(self) -> None:
        self._font_xl = pygame.font.SysFont("monospace", 62, bold=True)
        self._font_lg = pygame.font.SysFont("monospace", 48, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 30, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 20)

    def _blit_centered(
        self, surf: pygame.Surface, cx: int, y: int
    ) -> None:
        self._screen.blit(surf, surf.get_rect(centerx=cx, top=y))


# ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PlantillaFlappyBird().run()
