"""
core/hotkey_manager.py
Gerenciador de atalhos de teclado globais.
Usa `pynput` para interceptar teclas mesmo quando o app está em background.
"""

import threading
from typing import Callable
from pynput import keyboard


class HotkeyManager:
    """
    Registra e gerencia hotkeys globais de forma simples.
    Cada hotkey recebe uma string no formato "ctrl+shift+space" ou "ctrl+alt+f".
    """

    def __init__(self):
        self._hotkeys: dict[str, Callable] = {}
        self._listener: keyboard.GlobalHotKeys | None = None
        self._lock = threading.Lock()

    def _parse_hotkey(self, key_string: str) -> str:
        """
        Converte "ctrl+shift+space" para o formato do pynput: "<ctrl>+<shift>+<space>".
        """
        parts = key_string.lower().strip().split("+")
        formatted = []
        modifiers = {"ctrl", "shift", "alt", "cmd"}
        special_keys = {
            "space": "<space>",
            "enter": "<enter>",
            "tab": "<tab>",
            "esc": "<esc>",
            "f1": "<f1>", "f2": "<f2>", "f3": "<f3>", "f4": "<f4>",
            "f5": "<f5>", "f6": "<f6>", "f7": "<f7>", "f8": "<f8>",
            "f9": "<f9>", "f10": "<f10>", "f11": "<f11>", "f12": "<f12>",
        }
        for part in parts:
            part = part.strip()
            if part in modifiers:
                formatted.append(f"<{part}>")
            elif part in special_keys:
                formatted.append(special_keys[part])
            else:
                formatted.append(part)  # Letra normal, ex: 'f', 'g'
        return "+".join(formatted)

    def register(self, key_string: str, callback: Callable):
        """Registra um novo atalho global."""
        with self._lock:
            pynput_key = self._parse_hotkey(key_string)
            self._hotkeys[pynput_key] = callback
            self._restart_listener()

    def unregister(self, key_string: str):
        """Remove um atalho global."""
        with self._lock:
            pynput_key = self._parse_hotkey(key_string)
            self._hotkeys.pop(pynput_key, None)
            self._restart_listener()

    def unregister_all(self):
        """Remove todos os atalhos e para o listener."""
        with self._lock:
            self._hotkeys.clear()
            if self._listener:
                self._listener.stop()
                self._listener = None

    def _restart_listener(self):
        """Para o listener atual e inicia um novo com os atalhos atualizados."""
        if self._listener:
            self._listener.stop()

        if not self._hotkeys:
            return

        self._listener = keyboard.GlobalHotKeys(dict(self._hotkeys))
        self._listener.daemon = True
        self._listener.start()
