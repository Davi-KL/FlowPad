"""
utils/config.py
Gerencia as configurações do usuário em JSON.
Separado dos dados para facilitar reset e compartilhamento de config.
"""

import json
import os
from pathlib import Path


DEFAULT_CONFIG = {
    "hotkeys": {
        "quick_capture": "ctrl+shift+space",
        "dashboard": "ctrl+shift+f",
    },
    "theme": "dark",
    "language": "pt-BR",
    "reminder_check_interval_min": 1,
    "window": {
        "capture_width": 480,
        "capture_height": 320,
        "dashboard_width": 800,
        "dashboard_height": 600,
    },
    "quick_capture_default_type": "insight",
}


class Config:
    """
    Carrega, acessa e salva as configurações do FlowPad.
    Mescla com DEFAULT_CONFIG para garantir compatibilidade entre versões.
    """

    def __init__(self):
        # Diretório AppData/Roaming/FlowPad no Windows; ~/.flowpad em outros SOs
        app_dir = self._get_app_dir()
        self.config_path = app_dir / "config.json"
        self.data_path = str(app_dir / "entries.json")
        app_dir.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _get_app_dir(self) -> Path:
        if os.name == "nt":  # Windows
            base = os.environ.get("APPDATA", Path.home())
            return Path(base) / "FlowPad"
        return Path.home() / ".flowpad"

    def _load(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                # Mescla profunda: padrões + configurações do usuário
                return self._deep_merge(DEFAULT_CONFIG, user_config)
            except (json.JSONDecodeError, IOError):
                pass
        return dict(DEFAULT_CONFIG)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default=None):
        """Acessa uma chave de configuração."""
        return self._data.get(key, default)

    def set(self, key: str, value):
        """Define uma chave e salva imediatamente."""
        self._data[key] = value
        self._save()

    def _save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
