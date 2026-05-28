"""
Sistema de audio completo.

━━━ MÚSICA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Coloca uno o varios archivos en:  assets/sounds/music/
  • Formatos soportados: .ogg  .mp3  .wav
  • Para agregar música:  solo copia el archivo — se detecta automático.
  • Modos de playlist (config/settings.json → audio.playlist_mode):
      "shuffle"      → orden aleatorio cada vez
      "sequential"   → orden alfabético, en bucle
      "single"       → repite la primera pista encontrada

━━━ EFECTOS DE SONIDO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Carpeta:  assets/sounds/sfx/
  • Nombres configurables en:  config/settings.json → assets.sounds.sfx
      {
        "jump":  "sfx_jump.ogg",
        "point": "sfx_point.ogg",
        "die":   "sfx_die.ogg"
      }
  • Para reemplazar un SFX: sustituye el archivo conservando el nombre.
  • Para usar nombres distintos: edita el JSON, no el código.

━━━ CONTROLES DE VOLUMEN (teclado / arcade) ━━━━━━━━━━━━━━━━━━━━━━━━━━
  M        → silenciar / activar
  +  /  =  → subir volumen maestro
  -        → bajar volumen maestro
  N        → saltar a la siguiente pista

  El volumen se guarda automáticamente en data/audio_settings.json
  y se restaura al iniciar, incluso tras apagar la máquina.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

import pygame

from utils.paths import SOUNDS_DIR, DATA_DIR

# Formatos de audio soportados por pygame
_AUDIO_EXT: frozenset[str] = frozenset({".ogg", ".mp3", ".wav"})

# Archivo de persistencia de ajustes de volumen
_PERSIST_FILE: Path = DATA_DIR / "audio_settings.json"

# Evento que pygame lanza al terminar una pista
_MUSIC_END_EVENT: int = pygame.USEREVENT + 1


class AudioManager:
    """
    Gestiona música, SFX y controles de volumen para la máquina arcade.

    Volumen efectivo = master_volume × channel_volume
    El mute pone el volumen efectivo a 0 sin perder los valores guardados.
    """

    VOLUME_STEP: float = 0.05   # salto de volumen por pulsación
    MIN_VOL:     float = 0.0
    MAX_VOL:     float = 1.0

    def __init__(self, config: dict) -> None:
        self._cfg      = config
        self._audio_cfg: dict = config.get("audio", {})

        # Volúmenes (se pueden sobreescribir desde disco)
        self._master:    float = float(self._audio_cfg.get("master_volume", 1.0))
        self._music_vol: float = float(self._audio_cfg.get("music_volume",  0.5))
        self._sfx_vol:   float = float(self._audio_cfg.get("sfx_volume",    0.8))
        self._muted:     bool  = bool (self._audio_cfg.get("muted",          False))

        self._playlist_mode: str = self._audio_cfg.get("playlist_mode", "shuffle")

        # Estado interno
        self._tracks:    list[Path] = []
        self._track_idx: int = 0
        self._sfx:       dict[str, Optional[pygame.mixer.Sound]] = {}
        self.mixer_ok:   bool = False

        # Cargar ajustes persistidos (sobreescribe defaults del JSON)
        self._load_persisted_settings()

        # Salir si audio desactivado
        if not self._audio_cfg.get("enabled", True):
            print("[Audio] Desactivado en configuracion.")
            return

        # Inicializar mixer
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.mixer_ok = True
        except pygame.error as exc:
            print(f"[Audio] No se pudo inicializar el mixer: {exc}")
            return

        # Registrar evento de fin de pista para avanzar playlist
        pygame.mixer.music.set_endevent(_MUSIC_END_EVENT)

        self._scan_music_tracks()
        self._load_sfx()
        self._apply_all_volumes()

    # ──────────────────────────────────────────────────────────────────── #
    # Música
    # ──────────────────────────────────────────────────────────────────── #

    def play_music(self) -> None:
        """Inicia la reproducción de la playlist desde el principio."""
        if not self.mixer_ok or not self._tracks:
            return
        if self._playlist_mode == "shuffle":
            random.shuffle(self._tracks)
        self._track_idx = 0
        self._play_track(self._track_idx)

    def next_track(self) -> None:
        """Salta a la siguiente pista de la playlist."""
        if not self.mixer_ok or not self._tracks:
            return
        self._track_idx = (self._track_idx + 1) % len(self._tracks)
        self._play_track(self._track_idx)

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Llama esto en el bucle de eventos para que la playlist
        avance automáticamente cuando termina una pista.
        """
        if event.type == _MUSIC_END_EVENT:
            self.next_track()

    @property
    def current_track_name(self) -> str:
        """Nombre del archivo de la pista actual (sin extensión)."""
        if not self._tracks:
            return "—"
        return self._tracks[self._track_idx].stem

    @property
    def track_count(self) -> int:
        return len(self._tracks)

    # ──────────────────────────────────────────────────────────────────── #
    # Efectos de sonido
    # ──────────────────────────────────────────────────────────────────── #

    def play_sfx(self, key: str) -> None:
        """Reproduce un efecto de sonido por clave (jump / point / die)."""
        if not self.mixer_ok or self._muted:
            return
        sfx = self._sfx.get(key)
        if sfx:
            sfx.play()

    # ──────────────────────────────────────────────────────────────────── #
    # Control de volumen
    # ──────────────────────────────────────────────────────────────────── #

    def volume_up(self) -> None:
        self.set_master_volume(self._master + self.VOLUME_STEP)

    def volume_down(self) -> None:
        self.set_master_volume(self._master - self.VOLUME_STEP)

    def toggle_mute(self) -> None:
        self._muted = not self._muted
        self._apply_all_volumes()
        state = "SILENCIADO" if self._muted else "ACTIVADO"
        print(f"[Audio] {state}")

    def set_master_volume(self, vol: float) -> None:
        self._master = self._clamp(vol)
        # Desactivar mute automáticamente si el usuario sube el volumen
        if self._master > 0 and self._muted:
            self._muted = False
        self._apply_all_volumes()

    def set_music_volume(self, vol: float) -> None:
        self._music_vol = self._clamp(vol)
        self._apply_music_volume()

    def set_sfx_volume(self, vol: float) -> None:
        self._sfx_vol = self._clamp(vol)
        self._apply_sfx_volume()

    # ──────────────────────────────────────────────────────────────────── #
    # Propiedades de consulta
    # ──────────────────────────────────────────────────────────────────── #

    @property
    def master_volume(self) -> float:
        return self._master

    @property
    def music_volume(self) -> float:
        return self._music_vol

    @property
    def sfx_volume(self) -> float:
        return self._sfx_vol

    @property
    def muted(self) -> bool:
        return self._muted

    # ──────────────────────────────────────────────────────────────────── #
    # Persistencia
    # ──────────────────────────────────────────────────────────────────── #

    def save_settings(self) -> None:
        """
        Guarda la configuración de audio en data/audio_settings.json.
        Se llama automáticamente al salir del juego.
        """
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "master_volume": round(self._master,    3),
                "music_volume":  round(self._music_vol, 3),
                "sfx_volume":    round(self._sfx_vol,   3),
                "muted":         self._muted,
            }
            _PERSIST_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print("[Audio] Configuracion guardada.")
        except OSError as exc:
            print(f"[Audio] No se pudo guardar configuracion: {exc}")

    # ──────────────────────────────────────────────────────────────────── #
    # Ciclo de vida
    # ──────────────────────────────────────────────────────────────────── #

    def cleanup(self) -> None:
        if self.mixer_ok:
            pygame.mixer.music.stop()
            pygame.mixer.quit()

    # ──────────────────────────────────────────────────────────────────── #
    # Privados
    # ──────────────────────────────────────────────────────────────────── #

    def _scan_music_tracks(self) -> None:
        """Escanea assets/sounds/music/ y registra todas las pistas."""
        music_dir = SOUNDS_DIR / "music"
        if not music_dir.exists():
            print("[Audio] Carpeta de musica no encontrada.")
            return

        self._tracks = sorted(
            f for f in music_dir.iterdir()
            if f.is_file() and f.suffix.lower() in _AUDIO_EXT
        )

        if self._tracks:
            print(f"[Audio] {len(self._tracks)} pista(s) encontrada(s) en music/")
            for t in self._tracks:
                print(f"         • {t.name}")
        else:
            print("[Audio] No hay archivos de musica en assets/sounds/music/")

    def _load_sfx(self) -> None:
        """Carga los efectos de sonido definidos en settings.json."""
        sfx_dir  = SOUNDS_DIR / "sfx"
        sfx_cfg: dict[str, str] = (
            self._cfg.get("assets", {})
                     .get("sounds", {})
                     .get("sfx", {})
        )
        for key, filename in sfx_cfg.items():
            path = sfx_dir / filename
            self._sfx[key] = self._load_sound_file(path)

        loaded = [k for k, v in self._sfx.items() if v]
        missing = [k for k, v in self._sfx.items() if not v]
        if loaded:
            print(f"[Audio] SFX cargados: {', '.join(loaded)}")
        if missing:
            print(f"[Audio] SFX no encontrados (sin sonido): {', '.join(missing)}")

    def _play_track(self, idx: int) -> None:
        track = self._tracks[idx]
        try:
            pygame.mixer.music.load(str(track))
            self._apply_music_volume()
            pygame.mixer.music.play()
            print(f"[Audio] ▶  {track.name}")
        except pygame.error as exc:
            print(f"[Audio] Error al reproducir {track.name}: {exc}")

    def _apply_all_volumes(self) -> None:
        self._apply_music_volume()
        self._apply_sfx_volume()

    def _apply_music_volume(self) -> None:
        if not self.mixer_ok:
            return
        effective = 0.0 if self._muted else self._master * self._music_vol
        pygame.mixer.music.set_volume(effective)

    def _apply_sfx_volume(self) -> None:
        effective = 0.0 if self._muted else self._master * self._sfx_vol
        for sfx in self._sfx.values():
            if sfx:
                sfx.set_volume(effective)

    def _load_persisted_settings(self) -> None:
        if not _PERSIST_FILE.exists():
            return
        try:
            data = json.loads(_PERSIST_FILE.read_text(encoding="utf-8"))
            self._master    = self._clamp(float(data.get("master_volume", self._master)))
            self._music_vol = self._clamp(float(data.get("music_volume",  self._music_vol)))
            self._sfx_vol   = self._clamp(float(data.get("sfx_volume",    self._sfx_vol)))
            self._muted     = bool(data.get("muted", self._muted))
            print("[Audio] Ajustes de volumen restaurados desde disco.")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            print(f"[Audio] No se pudieron restaurar ajustes: {exc}")

    @staticmethod
    def _load_sound_file(path: Path) -> Optional[pygame.mixer.Sound]:
        if not path.exists():
            return None
        try:
            return pygame.mixer.Sound(str(path))
        except pygame.error as exc:
            print(f"[Audio] No se pudo cargar {path.name}: {exc}")
            return None

    @staticmethod
    def _clamp(val: float) -> float:
        return max(AudioManager.MIN_VOL, min(AudioManager.MAX_VOL, val))
