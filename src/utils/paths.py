"""
Rutas base del proyecto.
Fuente única de verdad — todos los módulos importan desde aquí.
"""
from pathlib import Path

# src/utils/paths.py → subir dos niveles → raíz del proyecto
ROOT_DIR: Path = Path(__file__).parent.parent.parent.resolve()

ASSETS_DIR: Path = ROOT_DIR / "assets"
IMAGES_DIR: Path = ASSETS_DIR / "images"
SOUNDS_DIR: Path = ASSETS_DIR / "sounds"
CONFIG_DIR: Path = ROOT_DIR / "config"
DATA_DIR: Path = ROOT_DIR / "data"
