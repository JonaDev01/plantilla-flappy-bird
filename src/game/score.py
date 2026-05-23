"""
Sistema de puntuación y récord local.
El récord se guarda en data/highscore.json automáticamente.
"""
from __future__ import annotations

import json
from pathlib import Path

from utils.paths import DATA_DIR

_HIGHSCORE_FILE: Path = DATA_DIR / "highscore.json"


class ScoreManager:
    def __init__(self) -> None:
        self.score: int = 0
        self.highscore: int = self._load_highscore()

    # ------------------------------------------------------------------ #
    # Acciones
    # ------------------------------------------------------------------ #

    def add_point(self) -> None:
        self.score += 1
        if self.score > self.highscore:
            self.highscore = self.score

    def save_highscore(self) -> None:
        """Guarda el récord en disco."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            _HIGHSCORE_FILE.write_text(
                json.dumps({"highscore": self.highscore}, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            print(f"[Score] No se pudo guardar el récord: {exc}")

    def reset(self) -> None:
        self.score = 0

    # ------------------------------------------------------------------ #
    # Privado
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_highscore() -> int:
        if not _HIGHSCORE_FILE.exists():
            return 0
        try:
            data = json.loads(_HIGHSCORE_FILE.read_text(encoding="utf-8"))
            return int(data.get("highscore", 0))
        except (json.JSONDecodeError, ValueError, OSError):
            return 0
