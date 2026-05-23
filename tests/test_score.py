"""Tests del sistema de puntuación."""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from game.score import ScoreManager


def make_sm(tmp_path: Path, initial_data: dict | None = None) -> ScoreManager:
    """Crea un ScoreManager aislado con un archivo de récord temporal."""
    hs_file = tmp_path / "highscore.json"
    if initial_data is not None:
        hs_file.write_text(json.dumps(initial_data), encoding="utf-8")
    return ScoreManager(highscore_path=hs_file)


class TestScoreManager:
    def test_score_starts_at_zero(self, tmp_path):
        sm = make_sm(tmp_path)
        assert sm.score == 0

    def test_add_point_increments_score(self, tmp_path):
        sm = make_sm(tmp_path)
        sm.add_point()
        sm.add_point()
        sm.add_point()
        assert sm.score == 3

    def test_highscore_updates_while_playing(self, tmp_path):
        sm = make_sm(tmp_path)
        for _ in range(5):
            sm.add_point()
        assert sm.highscore == 5

    def test_save_and_reload_highscore(self, tmp_path):
        hs_file = tmp_path / "highscore.json"
        sm = ScoreManager(highscore_path=hs_file)
        for _ in range(7):
            sm.add_point()
        sm.save_highscore()

        # Verificar el archivo
        data = json.loads(hs_file.read_text(encoding="utf-8"))
        assert data["highscore"] == 7

        # Nueva instancia debe cargar el récord
        sm2 = ScoreManager(highscore_path=hs_file)
        assert sm2.highscore == 7

    def test_reset_clears_score_only(self, tmp_path):
        sm = make_sm(tmp_path)
        for _ in range(4):
            sm.add_point()
        sm.reset()
        assert sm.score == 0
        assert sm.highscore == 4  # el récord se conserva en memoria

    def test_previous_highscore_loaded_on_start(self, tmp_path):
        sm = make_sm(tmp_path, initial_data={"highscore": 42})
        assert sm.highscore == 42

    def test_corrupt_highscore_file_returns_zero(self, tmp_path):
        hs_file = tmp_path / "highscore.json"
        hs_file.write_text("esto no es JSON{{{", encoding="utf-8")
        sm = ScoreManager(highscore_path=hs_file)
        assert sm.highscore == 0

    def test_missing_file_returns_zero(self, tmp_path):
        sm = ScoreManager(highscore_path=tmp_path / "nonexistent.json")
        assert sm.highscore == 0
