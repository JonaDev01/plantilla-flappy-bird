"""
Plantilla FlappyBird — Punto de entrada principal.

Uso:
  python src/main.py           (desde la raíz del proyecto)
  python -m main               (desde src/)

Controles de juego:
  ESPACIO / ↑ / W   → saltar
  R  (Game Over)    → reiniciar rápido
  F11               → pantalla completa / ventana
  ESC               → salir

Controles de audio (operador / arcade):
  M                 → silenciar / activar
  +  /  =           → subir volumen maestro
  -                 → bajar volumen maestro
  N                 → siguiente pista de música
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from utils.config import load_config
from utils.asset_loader import AssetLoader
from game.bird import Bird
from game.pipe_manager import PipeManager
from game.background import Background
from game.score import ScoreManager
from game.gpio_handler import GPIOHandler
from game.audio_manager import AudioManager

# ────────────────────────────────────────────────────────────────────────
# Estados
# ────────────────────────────────────────────────────────────────────────
MENU      = "MENU"
PLAYING   = "PLAYING"
GAME_OVER = "GAME_OVER"

# Paleta UI
WHITE  = (255, 255, 255)
BLACK  = (  0,   0,   0)
YELLOW = (255, 220,   0)
RED    = (220,  60,  60)
GOLD   = (255, 200,   0)
GRAY   = (180, 180, 180)
GREEN  = ( 60, 200,  60)
ORANGE = (220, 160,  40)


# ────────────────────────────────────────────────────────────────────────
# HUD de volumen
# ────────────────────────────────────────────────────────────────────────
class _VolumeHUD:
    """
    Panel flotante de volumen que aparece brevemente al cambiar el audio.
    Diseñado para ser visible en una cabina de arcade.
    """
    _SHOW_FRAMES = 180   # 3 s a 60 fps
    _FADE_FRAMES = 40    # últimos 40 frames hacen fade-out
    _PANEL_W     = 210
    _PANEL_H     = 54
    _BAR_W       = 160
    _BAR_H       = 12

    def __init__(self, font: pygame.font.Font) -> None:
        self._font  = font
        self._timer = 0

    def notify(self) -> None:
        """Llama esto cada vez que cambie el volumen."""
        self._timer = self._SHOW_FRAMES

    def update(self) -> None:
        if self._timer > 0:
            self._timer -= 1

    @property
    def visible(self) -> bool:
        return self._timer > 0

    def draw(self, screen: pygame.Surface, audio: AudioManager) -> None:
        if not self.visible:
            return

        # Alpha: fade-out en los últimos fotogramas
        ratio = min(1.0, self._timer / self._FADE_FRAMES)
        alpha = int(255 * ratio)

        sw = screen.get_width()
        px = sw - self._PANEL_W - 10
        py = 10

        # Fondo semitransparente
        panel = pygame.Surface((self._PANEL_W, self._PANEL_H), pygame.SRCALPHA)
        panel.fill((10, 10, 10, int(190 * ratio)))
        pygame.draw.rect(panel, (80, 80, 80, int(200 * ratio)),
                         (0, 0, self._PANEL_W, self._PANEL_H), 1)
        screen.blit(panel, (px, py))

        if audio.muted:
            # Mensaje de silenciado
            txt = self._font.render("SILENCIADO", True, RED)
            txt.set_alpha(alpha)
            screen.blit(txt, txt.get_rect(
                centerx=px + self._PANEL_W // 2,
                centery=py + self._PANEL_H // 2,
            ))
        else:
            pct = int(audio.master_volume * 100)

            # Etiqueta
            lbl = self._font.render(f"VOL  {pct:3d}%", True, WHITE)
            lbl.set_alpha(alpha)
            screen.blit(lbl, (px + 10, py + 7))

            # Barra de volumen
            bx = px + 10
            by = py + 32
            # Fondo de la barra
            pygame.draw.rect(screen, (50, 50, 50), (bx, by, self._BAR_W, self._BAR_H))
            # Relleno según nivel
            fw = int(self._BAR_W * audio.master_volume)
            if fw > 0:
                color = (
                    GREEN  if audio.master_volume > 0.55 else
                    ORANGE if audio.master_volume > 0.25 else
                    RED
                )
                bar_surf = pygame.Surface((fw, self._BAR_H))
                bar_surf.fill(color)
                bar_surf.set_alpha(alpha)
                screen.blit(bar_surf, (bx, by))
            # Borde
            pygame.draw.rect(screen, (100, 100, 100), (bx, by, self._BAR_W, self._BAR_H), 1)


# ────────────────────────────────────────────────────────────────────────
# Juego principal
# ────────────────────────────────────────────────────────────────────────
class PlantillaFlappyBird:
    """Máquina de estados principal del juego."""

    def __init__(self) -> None:
        pygame.init()

        self._cfg  = load_config()
        disp       = self._cfg["display"]

        # Pantalla
        flags = pygame.FULLSCREEN if disp["fullscreen"] else 0
        self._screen = pygame.display.set_mode((disp["width"], disp["height"]), flags)
        pygame.display.set_caption(disp["title"])
        self._clock    = pygame.time.Clock()
        self._fps:      int  = disp["fps"]
        self._show_fps: bool = disp["show_fps"]
        self._W:        int  = disp["width"]
        self._H:        int  = disp["height"]

        # Subsistemas
        self._assets = AssetLoader(self._cfg)
        self._audio  = AudioManager(self._cfg)
        self._gpio   = GPIOHandler(self._cfg)
        self._init_fonts()

        # HUD de volumen
        self._vol_hud = _VolumeHUD(self._font_sm)

        # Entidades del juego
        self._score: ScoreManager = ScoreManager()
        self._bg:    Background   = None   # type: ignore[assignment]
        self._bird:  Bird         = None   # type: ignore[assignment]
        self._pipes: PipeManager  = None   # type: ignore[assignment]
        self._reset()

        # Arrancar música
        self._audio.play_music()

        self._state: str = MENU

    # ──────────────────────────────────────────────────────────────────── #
    # Bucle principal
    # ──────────────────────────────────────────────────────────────────── #

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
                    running, jump = self._handle_key(event.key, running, jump)

                # Avance automático de playlist al terminar una pista
                self._audio.handle_event(event)

            # ── GPIO ────────────────────────────────────────────────────
            if self._gpio.get_jump():
                jump = True

            # ── Lógica por estado ────────────────────────────────────────
            if self._state == MENU:
                self._update_menu(jump)
            elif self._state == PLAYING:
                self._update_playing(jump)
            elif self._state == GAME_OVER:
                self._update_game_over(jump)

            self._vol_hud.update()

            # ── Render ──────────────────────────────────────────────────
            self._draw()
            pygame.display.flip()

        self._shutdown()

    # ──────────────────────────────────────────────────────────────────── #
    # Teclado
    # ──────────────────────────────────────────────────────────────────── #

    def _handle_key(
        self, key: int, running: bool, jump: bool
    ) -> tuple[bool, bool]:
        # Salir
        if key == pygame.K_ESCAPE:
            running = False

        # Salto
        elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            jump = True

        # Pantalla completa
        elif key == pygame.K_F11:
            pygame.display.toggle_fullscreen()

        # Reiniciar (Game Over)
        elif key == pygame.K_r and self._state == GAME_OVER:
            self._restart()

        # ── Audio ────────────────────────────────────────────────────────
        elif key == pygame.K_m:
            self._audio.toggle_mute()
            self._vol_hud.notify()

        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self._audio.volume_up()
            self._vol_hud.notify()

        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._audio.volume_down()
            self._vol_hud.notify()

        elif key == pygame.K_n:
            self._audio.next_track()
            self._vol_hud.notify()

        return running, jump

    # ──────────────────────────────────────────────────────────────────── #
    # Updates por estado
    # ──────────────────────────────────────────────────────────────────── #

    def _update_menu(self, jump: bool) -> None:
        self._bg.update()
        if jump:
            self._state = PLAYING

    def _update_playing(self, jump: bool) -> None:
        self._bg.update()
        self._bird.update(jump, self._audio)
        self._pipes.update()

        if self._pipes.check_score(self._bird):
            self._score.add_point()
            self._audio.play_sfx("point")
            self._gpio.on_score(self._score.score)

        ground_h = self._cfg["game"]["ground_height"]
        if (
            self._pipes.check_collision(self._bird)
            or self._bird.is_dead(self._H, ground_h)
        ):
            self._score.save_highscore()
            self._audio.play_sfx("die")
            self._gpio.on_game_over()
            self._state = GAME_OVER

    def _update_game_over(self, jump: bool) -> None:
        self._bg.update()
        if jump:
            self._restart()

    # ──────────────────────────────────────────────────────────────────── #
    # Renderizado
    # ──────────────────────────────────────────────────────────────────── #

    def _draw(self) -> None:
        self._bg.draw(self._screen)

        if self._state in (PLAYING, GAME_OVER):
            self._pipes.draw(self._screen)
            self._bird.draw(self._screen)

        if self._state == MENU:
            self._draw_menu()
        elif self._state == PLAYING:
            self._draw_hud()
        elif self._state == GAME_OVER:
            self._draw_game_over()

        # HUD de volumen (siempre encima de todo)
        self._vol_hud.draw(self._screen, self._audio)

        if self._show_fps:
            fps_surf = self._font_sm.render(
                f"FPS {int(self._clock.get_fps())}", True, YELLOW
            )
            self._screen.blit(fps_surf, (4, 4))

    def _draw_menu(self) -> None:
        cx = self._W // 2

        panel = pygame.Surface((self._W - 60, 230), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 145))
        self._screen.blit(panel, (30, self._H // 3 - 30))

        self._blit_c(self._font_xl.render("FLAPPY",  True, YELLOW), cx, self._H // 3)
        self._blit_c(self._font_xl.render("BIRD",    True, YELLOW), cx, self._H // 3 + 68)
        self._blit_c(
            self._font_md.render(f"RÉCORD: {self._score.highscore}", True, GOLD),
            cx, self._H // 3 + 145,
        )
        self._blit_c(
            self._font_sm.render("ESPACIO / BOTÓN para iniciar", True, WHITE),
            cx, self._H * 2 // 3,
        )
        # Hint de audio
        hint_audio = self._font_xs.render("M=silenciar  +/-=volumen  N=siguiente", True, GRAY)
        self._blit_c(hint_audio, cx, self._H * 2 // 3 + 28)

    def _draw_hud(self) -> None:
        cx = self._W // 2
        shadow = self._font_lg.render(str(self._score.score), True, BLACK)
        text   = self._font_lg.render(str(self._score.score), True, WHITE)
        self._screen.blit(shadow, shadow.get_rect(centerx=cx + 2, top=18))
        self._screen.blit(text,   text.get_rect(centerx=cx,       top=16))

    def _draw_game_over(self) -> None:
        self._draw_hud()

        overlay = pygame.Surface((self._W, self._H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self._screen.blit(overlay, (0, 0))

        panel_h = 250
        panel_y = self._H // 2 - panel_h // 2
        panel = pygame.Surface((self._W - 60, panel_h), pygame.SRCALPHA)
        panel.fill((15, 15, 15, 210))
        self._screen.blit(panel, (30, panel_y))

        cx = self._W // 2
        self._blit_c(self._font_lg.render("GAME OVER",                         True, RED),   cx, panel_y + 18)
        self._blit_c(self._font_md.render(f"Puntos : {self._score.score}",      True, WHITE), cx, panel_y + 90)
        self._blit_c(self._font_md.render(f"Récord : {self._score.highscore}",  True, GOLD),  cx, panel_y + 140)
        self._blit_c(self._font_sm.render("ESPACIO / R / BOTÓN para reiniciar", True, GRAY),  cx, panel_y + 200)

    # ──────────────────────────────────────────────────────────────────── #
    # Helpers
    # ──────────────────────────────────────────────────────────────────── #

    def _restart(self) -> None:
        self._reset()
        self._state = PLAYING

    def _reset(self) -> None:
        game_cfg    = self._cfg["game"]
        self._bg    = Background(self._assets, self._W, self._H, game_cfg)
        self._bird  = Bird(self._assets, self._W, self._H, game_cfg)
        self._pipes = PipeManager(self._assets, self._W, self._H, game_cfg)
        self._score.reset()

    def _shutdown(self) -> None:
        self._audio.save_settings()   # persistir volumen antes de salir
        self._audio.cleanup()
        self._gpio.cleanup()
        pygame.quit()
        sys.exit(0)

    def _init_fonts(self) -> None:
        self._font_xl = pygame.font.SysFont("monospace", 62, bold=True)
        self._font_lg = pygame.font.SysFont("monospace", 48, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 30, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 20)
        self._font_xs = pygame.font.SysFont("monospace", 15)

    def _blit_c(self, surf: pygame.Surface, cx: int, y: int) -> None:
        self._screen.blit(surf, surf.get_rect(centerx=cx, top=y))


# ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PlantillaFlappyBird().run()
