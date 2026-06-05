"""
core/plugin_manager.py
Carrega extensões (plugins) de uma pasta para adicionar tipos e hotkeys ao FlowPad.

Cada plugin é um arquivo .py na pasta src/plugins/ que expõe:

    def register(app) -> dict:
        return {
            "types": {"meu_tipo": {"label": "...", "color": "#RRGGBB"}},
            "hotkeys": {"ctrl+shift+x": lambda: app.open_quick_capture("meu_tipo")},
        }
"""

import importlib.util
from pathlib import Path


class PluginManager:
    """Escaneia plugin_dir, importa cada .py e chama register(app)."""

    def __init__(self):
        self._extra_types: dict[str, dict] = {}
        self._loaded: list[str] = []

    def load_plugins(self, plugin_dir: str, app) -> None:
        """Carrega todos os plugins válidos do diretório."""
        path = Path(plugin_dir)
        if not path.exists():
            return
        for file in sorted(path.glob("*.py")):
            if file.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(file.stem, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "register"):
                    result = module.register(app) or {}
                    self._extra_types.update(result.get("types", {}))
                    for key, cb in result.get("hotkeys", {}).items():
                        app.hotkey_manager.register(key, cb)
                    self._loaded.append(file.stem)
                    print(f"[PluginManager] Plugin '{file.stem}' carregado.")
            except Exception as exc:
                print(f"[PluginManager] Falha ao carregar '{file.name}': {exc}")

    def get_extra_types(self) -> dict[str, dict]:
        """Tipos de entrada registrados por plugins."""
        return dict(self._extra_types)

    @property
    def loaded_plugins(self) -> list[str]:
        return list(self._loaded)
