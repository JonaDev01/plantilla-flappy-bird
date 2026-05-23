"""
Cargador de configuración.
Lee config/settings.json y fusiona con valores por defecto.
"""
import json
from pathlib import Path
from .paths import CONFIG_DIR

_DEFAULTS: dict = {
    "display": {
        "width": 480,
        "height": 640,
        "fps": 60,
        "fullscreen": False,
        "title": "FlappyClone",
        "show_fps": False,
    },
    "game": {
        "gravity": 0.5,
        "jump_strength": -9.5,
        "pipe_speed": 3.0,
        "pipe_gap": 155,
        "pipe_spawn_interval": 90,
        "ground_height": 80,
        "min_pipe_margin": 70,
    },
    "gpio": {
        "enabled": False,
        "jump_pin": 17,
        "signal_pin": 27,
        "signal_mode": "score_threshold",
        "signal_score_threshold": 10,
        "signal_pulse_seconds": 0.2,
    },
    "assets": {
        "images": {
            "bird": "bird.png",
            "pipe": "pipe.png",
            "background": "background.png",
            "ground": "ground.png",
        },
        "sounds": {
            "music": "music.ogg",
            "jump": "sfx_jump.ogg",
            "point": "sfx_point.ogg",
            "die": "sfx_die.ogg",
        },
    },
    "audio": {
        "music_volume": 0.4,
        "sfx_volume": 0.7,
        "enabled": True,
    },
}


def load_config(path: Path | None = None) -> dict:
    """Carga settings.json y fusiona con los valores por defecto."""
    settings_path = path or (CONFIG_DIR / "settings.json")
    if not settings_path.exists():
        print(f"[Config] {settings_path} no encontrado — usando valores por defecto.")
        return _deep_merge({}, _DEFAULTS)

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"[Config] Error al leer JSON: {exc} — usando valores por defecto.")
        return _deep_merge({}, _DEFAULTS)

    return _deep_merge(_DEFAULTS, user_data)


def _deep_merge(base: dict, override: dict) -> dict:
    """Fusión profunda: override tiene prioridad sobre base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
