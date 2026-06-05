"""
tests/test_config.py
Testes unitários para o módulo de configuração.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import Config, DEFAULT_CONFIG


class TestConfig:
    def test_defaults_are_loaded(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        config = Config()
        assert config.get("theme") == "dark"
        assert "quick_capture" in config.get("hotkeys", {})

    def test_get_missing_key_returns_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        config = Config()
        assert config.get("chave_inexistente", "fallback") == "fallback"

    def test_set_persists_value(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        config = Config()
        config.set("theme", "light")
        # Recarrega do disco
        config2 = Config()
        assert config2.get("theme") == "light"
