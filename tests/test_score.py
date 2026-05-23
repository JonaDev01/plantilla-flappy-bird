"""Tests del sistema de puntuación."""
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

# Añade src/ al path para importar los módulos del juego
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _make_score_manager(tmp_path: Path):
    """Crea un ScoreManager con un directorio de datos temporal."""
    with patch("game.score.DATA_DIR", tmp_path), \
         patch("game.score._HIGHSCORE_FILE", tmp_path / "highscore.json"):
        from game.score import ScoreManager
        return ScoreManager()


class TestScoreManager:
    def test_score_starts_at_zero(self, tmp_path):
        with patch("game.score.DATA_DIR", tmp_path), \
             patch("game.score._HIGHSCORE_FILE", tmp_path / "highscore.json"):
            from importlib import reload
            import game.score as score_mod
            reload(score_mod)
            sm = score_mod.ScoreManager()
            assert sm.score == 0

    def test_add_point_increments_score(self, tmp_path):
        with patch("game.score.DATA_DIR", tmp_path), \
             patch("game.score._HIGHSCORE_FILE", tmp_path / "highscore.json"):
            from importlib import reload
            import game.score as score_mod
            reload(score_mod)
            sm = score_mod.ScoreManager()
            sm.add_point()
            sm.add_point()
            sm.add_point()
            assert sm.score == 3

    def test_highscore_updates(self, tmp_path):
        with patch("game.score.DATA_DIR", tmp_path), \
             patch("game.score._HIGHSCORE_FILE", tmp_path / "highscore.json"):
            from importlib import reload
            import game.score as score_mod
            reload(score_mod)
            sm = score_mod.ScoreManager()
            for _ in range(5):
                sm.add_point()
            assert sm.highscore == 5

    def test_save_and_load_highscore(self, tmp_path):
        hs_file = tmp_path / "highscore.json"
        with patch("game.score.DATA_DIR", tmp_path), \
             patch("game.score._HIGHSCORE_FILE", hs_file):
            from importlib import reload
            import game.score as score_mod
            reload(score_mod)
            sm = score_mod.ScoreManager()
            for _ in range(7):
                sm.add_point()
            sm.save_highscore()

            # Verificar el archivo
            data = json.loads(hs_file.read_text())
            assert data["highscore"] == 7

            # Nueva instancia debe cargar el récord
            sm2 = score_mod.ScoreManager()
            assert sm2.highscore == 7

    def test_reset_clears_score_only(self, tmp_path):
        with patch("game.score.DATA_DIR", tmp_path), \
             patch("game.score._HIGHSCORE_FILE", tmp_path / "highscore.json"):
            from importlib import reload
            import game.score as score_mod
            reload(score_mod)
            sm = score_mod.ScoreManager()
            for _ in range(4):
                sm.add_point()
            sm.reset()
            assert sm.score == 0
            assert sm.highscore == 4  # el récord se conserva

    def test_corrupt_highscore_file_returns_zero(self, tmp_path):
        hs_file = tmp_path / "highscore.json"
        hs_file.write_text("esto no es JSON{{{", encoding="utf-8")
        with patch("game.score.DATA_DIR", tmp_path), \
             patch("game.score._HIGHSCORE_FILE", hs_file):
            from importlib import reload
            import game.score as score_mod
            reload(score_mod)
            sm = score_mod.ScoreManager()
            assert sm.highscore == 0
