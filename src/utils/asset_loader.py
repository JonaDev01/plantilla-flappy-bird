"""
Cargador dinámico de assets.

Cómo reemplazar assets:
  - Imágenes: coloca el PNG en la carpeta indicada en settings.json
      assets/images/bird/      → bird.png   (o bird_0.png, bird_1.png, bird_2.png)
      assets/images/pipes/     → pipe.png
      assets/images/background/→ background.png
      assets/images/ground/    → ground.png
  - Música:   assets/sounds/music/ → music.ogg
  - Efectos:  assets/sounds/sfx/   → sfx_jump.ogg / sfx_point.ogg / sfx_die.ogg

Si un archivo no existe, se genera un placeholder automáticamente.
"""
from __future__ import annotations

import pygame
from pathlib import Path
from typing import Optional

from .paths import IMAGES_DIR, SOUNDS_DIR


class AssetLoader:
    """Carga y cachea todos los assets del juego."""

    def __init__(self, config: dict) -> None:
        self._config = config
        self._images: dict[str, pygame.Surface] = {}
        self._sounds: dict[str, Optional[pygame.mixer.Sound]] = {}
        self._bird_frames: list[pygame.Surface] = []
        self._music_path: Optional[str] = None

        self._load_all()

    # ------------------------------------------------------------------ #
    # Carga principal
    # ------------------------------------------------------------------ #

    def _load_all(self) -> None:
        self._load_images()
        self._load_sounds()

    def _load_images(self) -> None:
        img_cfg = self._config["assets"]["images"]

        self._load_or_gen(
            "background",
            IMAGES_DIR / "background" / img_cfg["background"],
            self._gen_background,
        )
        self._load_or_gen(
            "ground",
            IMAGES_DIR / "ground" / img_cfg["ground"],
            self._gen_ground,
        )
        self._load_or_gen(
            "pipe",
            IMAGES_DIR / "pipes" / img_cfg["pipe"],
            self._gen_pipe,
        )

        # El pájaro soporta animación de fotogramas múltiples
        self._bird_frames = self._load_bird_frames(img_cfg["bird"])

    def _load_or_gen(self, key: str, path: Path, generator) -> None:
        if path.exists():
            try:
                self._images[key] = pygame.image.load(str(path)).convert_alpha()
                print(f"[Assets] Cargado: {path.name}")
                return
            except pygame.error as exc:
                print(f"[Assets] No se pudo cargar {path.name}: {exc}")
        print(f"[Assets] Usando placeholder para '{key}'")
        self._images[key] = generator()

    def _load_bird_frames(self, bird_filename: str) -> list[pygame.Surface]:
        """
        Intenta cargar fotogramas de animación:
        1. bird_0.png, bird_1.png, bird_2.png (animación)
        2. bird.png (estático)
        3. Genera placeholder con 3 frames
        """
        bird_dir = IMAGES_DIR / "bird"
        frames: list[pygame.Surface] = []

        # Opción 1 — fotogramas numerados
        for i in range(3):
            frame_path = bird_dir / f"bird_{i}.png"
            if frame_path.exists():
                try:
                    frames.append(pygame.image.load(str(frame_path)).convert_alpha())
                except pygame.error:
                    pass

        if frames:
            return frames

        # Opción 2 — archivo único
        single_path = bird_dir / bird_filename
        if single_path.exists():
            try:
                surf = pygame.image.load(str(single_path)).convert_alpha()
                return [surf, surf, surf]  # usa el mismo fotograma 3 veces
            except pygame.error:
                pass

        # Opción 3 — placeholder generado
        print("[Assets] Usando placeholder para 'bird' (3 fotogramas)")
        return [self._gen_bird(frame=i) for i in range(3)]

    # ------------------------------------------------------------------ #
    # Generadores de placeholders
    # ------------------------------------------------------------------ #

    def _gen_background(self) -> pygame.Surface:
        """Degradado de cielo azul."""
        w = self._config["display"]["width"]
        h = self._config["display"]["height"]
        surf = pygame.Surface((w, h))
        sky_top = (112, 197, 235)
        sky_bot = (70, 140, 190)
        for y in range(h):
            t = y / h
            r = int(sky_top[0] * (1 - t) + sky_bot[0] * t)
            g = int(sky_top[1] * (1 - t) + sky_bot[1] * t)
            b = int(sky_top[2] * (1 - t) + sky_bot[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
        # Nubes sencillas
        for cx, cy, r in [(80, 80, 30), (200, 50, 22), (360, 100, 28)]:
            pygame.draw.ellipse(surf, (255, 255, 255), (cx - r, cy - 14, r * 2, 28))
            pygame.draw.ellipse(surf, (255, 255, 255), (cx - r + 10, cy - 22, r * 1.4, 28))
        return surf

    def _gen_ground(self) -> pygame.Surface:
        """Suelo con franja de pasto."""
        w = self._config["display"]["width"]
        h = self._config["game"]["ground_height"]
        surf = pygame.Surface((w, h))
        surf.fill((222, 184, 135))            # arena
        pygame.draw.rect(surf, (124, 180, 56), (0, 0, w, 14))   # pasto
        pygame.draw.rect(surf, (90, 140, 40), (0, 12, w, 4))    # sombra pasto
        return surf

    def _gen_pipe(self) -> pygame.Surface:
        """Tubo verde con tapa. La tapa queda en la parte superior del surface."""
        pw = 64
        ph = self._config["display"]["height"]  # altura máxima posible
        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)

        body   = (78, 175, 62)
        light  = (120, 210, 90)
        shadow = (45, 120, 35)
        cap_c  = (58, 155, 45)
        border = (35, 100, 25)
        cap_h  = 28

        # Cuerpo
        pygame.draw.rect(surf, body,   (8, 0, pw - 16, ph))
        pygame.draw.rect(surf, light,  (8, 0, 10, ph))      # brillo izq
        pygame.draw.rect(surf, shadow, (pw - 18, 0, 10, ph))  # sombra der

        # Tapa (en y=0 del surface — irá en el borde del hueco)
        pygame.draw.rect(surf, cap_c,  (0, 0, pw, cap_h))
        pygame.draw.rect(surf, light,  (2, 2, 10, cap_h - 4))
        pygame.draw.rect(surf, border, (0, 0, pw, cap_h), 2)

        return surf

    def _gen_bird(self, frame: int = 0) -> pygame.Surface:
        """Pájaro amarillo con alas animadas (3 posiciones)."""
        w, h = 44, 32
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Cuerpo
        pygame.draw.ellipse(surf, (255, 210, 0), (6, 6, 30, 22))
        pygame.draw.ellipse(surf, (255, 170, 0), (8, 8, 28, 18))  # tono más oscuro

        # Ala — posición según fotograma
        wing_ys = [14, 7, 18]     # centro, arriba, abajo
        wy = wing_ys[frame % 3]
        pygame.draw.ellipse(surf, (255, 165, 0), (10, wy, 18, 9))
        pygame.draw.ellipse(surf, (220, 130, 0), (11, wy + 1, 14, 6))

        # Ojo
        pygame.draw.circle(surf, (255, 255, 255), (31, 13), 6)
        pygame.draw.circle(surf, (30, 30, 30),   (33, 13), 3)
        pygame.draw.circle(surf, (255, 255, 255), (34, 11), 1)  # reflejo

        # Pico
        beak = [(36, 14), (43, 16), (36, 19)]
        pygame.draw.polygon(surf, (255, 140, 0), beak)

        return surf

    # ------------------------------------------------------------------ #
    # Carga de audio
    # ------------------------------------------------------------------ #

    def _load_sounds(self) -> None:
        if not self._config["audio"]["enabled"]:
            return

        snd_cfg = self._config["assets"]["sounds"]
        sfx_vol = self._config["audio"]["sfx_volume"]

        sfx_map = {
            "jump":  snd_cfg["jump"],
            "point": snd_cfg["point"],
            "die":   snd_cfg["die"],
        }
        for key, filename in sfx_map.items():
            path = SOUNDS_DIR / "sfx" / filename
            self._sounds[key] = self._load_sfx(path, sfx_vol)

        # Música (ruta para pygame.mixer.music)
        music_path = SOUNDS_DIR / "music" / snd_cfg["music"]
        if music_path.exists():
            self._music_path = str(music_path)

    @staticmethod
    def _load_sfx(path: Path, volume: float) -> Optional[pygame.mixer.Sound]:
        if not path.exists():
            return None
        try:
            snd = pygame.mixer.Sound(str(path))
            snd.set_volume(volume)
            return snd
        except pygame.error as exc:
            print(f"[Assets] No se pudo cargar SFX {path.name}: {exc}")
            return None

    # ------------------------------------------------------------------ #
    # Acceso público
    # ------------------------------------------------------------------ #

    def get_image(self, key: str) -> pygame.Surface:
        return self._images[key]

    def get_bird_frames(self) -> list[pygame.Surface]:
        return self._bird_frames

    def get_sound(self, key: str) -> Optional[pygame.mixer.Sound]:
        return self._sounds.get(key)

    def get_music_path(self) -> Optional[str]:
        return self._music_path

    def reload(self) -> None:
        """Recarga todos los assets en caliente (útil al reemplazar archivos)."""
        self._images.clear()
        self._sounds.clear()
        self._bird_frames.clear()
        self._music_path = None
        self._load_all()
        print("[Assets] Assets recargados.")
