"""Tests del cargador de configuración."""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.config import load_config, _deep_merge


class TestDeepMerge:
    def test_simple_merge(self):
        base     = {"a": 1, "b": 2}
        override = {"b": 99, "c": 3}
        result   = _deep_merge(base, override)
        assert result == {"a": 1, "b": 99, "c": 3}

    def test_nested_merge(self):
        base     = {"display": {"width": 480, "height": 640, "fps": 60}}
        override = {"display": {"fps": 30}}
        result   = _deep_merge(base, override)
        assert result["display"]["fps"] == 30
        assert result["display"]["width"] == 480  # conservado

    def test_override_does_not_mutate_base(self):
        base     = {"x": {"y": 1}}
        override = {"x": {"y": 2}}
        _deep_merge(base, override)
        assert base["x"]["y"] == 1


class TestLoadConfig:
    def test_loads_valid_json(self, tmp_path):
        cfg_file = tmp_path / "settings.json"
        cfg_file.write_text(
            json.dumps({"display": {"fps": 30}}), encoding="utf-8"
        )
        cfg = load_config(cfg_file)
        assert cfg["display"]["fps"] == 30
        # Defaults deben estar presentes
        assert "gravity" in cfg["game"]

    def test_missing_file_returns_defaults(self, tmp_path):
        cfg = load_config(tmp_path / "nonexistent.json")
        assert cfg["display"]["width"] == 480
        assert cfg["game"]["gravity"] == 0.5

    def test_corrupt_json_returns_defaults(self, tmp_path):
        cfg_file = tmp_path / "bad.json"
        cfg_file.write_text("{corrupt json{{", encoding="utf-8")
        cfg = load_config(cfg_file)
        assert cfg["display"]["fps"] == 60

    def test_gpio_disabled_by_default(self, tmp_path):
        cfg = load_config(tmp_path / "nonexistent.json")
        assert cfg["gpio"]["enabled"] is False
