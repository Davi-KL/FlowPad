"""
ui/settings.py
Tela de configurações do FlowPad — hotkeys e tema.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from utils.config import Config
from ui.colors import COLORS as C


_VALID_MODIFIERS = {"ctrl", "shift", "alt", "cmd"}
_VALID_SPECIALS = {
    "space", "enter", "tab", "esc", "backspace",
    "f1", "f2", "f3", "f4", "f5", "f6",
    "f7", "f8", "f9", "f10", "f11", "f12",
}


def _validate_hotkey(key_string: str) -> bool:
    """Valida formato de hotkey: precisa de ao menos um modificador + uma tecla."""
    parts = [p.strip().lower() for p in key_string.split("+") if p.strip()]
    if len(parts) < 2:
        return False
    modifiers = [p for p in parts if p in _VALID_MODIFIERS]
    keys = [p for p in parts if p not in _VALID_MODIFIERS]
    if not modifiers or not keys:
        return False
    return all(k in _VALID_SPECIALS or (len(k) == 1 and k.isalpha()) for k in keys)


class SettingsWindow(ctk.CTkToplevel):
    """
    Janela de configurações com campos para alterar hotkeys e o tema visual.
    Salva no config.json e recarrega atalhos sem reiniciar o app.
    """

    def __init__(
        self,
        master: ctk.CTk,
        config: Config,
        on_hotkeys_changed: Callable[[dict], None],
    ):
        super().__init__(master)
        self.config = config
        self.on_hotkeys_changed = on_hotkeys_changed

        self._configure_window()
        self._build_ui()
        self._center()

    def _configure_window(self):
        self.title("FlowPad — Configurações")
        self.geometry("460x360")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.attributes("-topmost", True)

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - self.winfo_width()) // 2
        y = (sh - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="⚙️  Configurações",
            font=("Consolas", 13, "bold"), text_color=C["accent"],
        ).pack(side="left", padx=16)

        body = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        hotkeys = self.config.get("hotkeys", {})

        # Tema
        ctk.CTkLabel(
            body, text="Tema Visual",
            font=("Consolas", 9), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        current_theme = self.config.get("theme", "dark").capitalize()
        self._theme_var = ctk.StringVar(value=current_theme)
        ctk.CTkSegmentedButton(
            body,
            values=["Dark", "Light"],
            variable=self._theme_var,
            command=self._on_theme_preview,
            font=("Consolas", 10),
            height=32,
        ).pack(fill="x", pady=(0, 16))

        # Hotkey captura rápida
        ctk.CTkLabel(
            body, text="Hotkey — Captura Rápida",
            font=("Consolas", 9), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.capture_var = tk.StringVar(
            value=hotkeys.get("quick_capture", "ctrl+shift+space")
        )
        ctk.CTkEntry(
            body, textvariable=self.capture_var,
            font=("Consolas", 11), height=36,
            fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], border_width=1,
        ).pack(fill="x", pady=(0, 12))

        # Hotkey dashboard
        ctk.CTkLabel(
            body, text="Hotkey — Dashboard",
            font=("Consolas", 9), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.dashboard_var = tk.StringVar(
            value=hotkeys.get("dashboard", "ctrl+shift+f")
        )
        ctk.CTkEntry(
            body, textvariable=self.dashboard_var,
            font=("Consolas", 11), height=36,
            fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], border_width=1,
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            body, text="Formato: ctrl+shift+space  |  ctrl+alt+n",
            font=("Consolas", 8), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", pady=(0, 16))

        # Botões
        btn_row = ctk.CTkFrame(body, fg_color=C["bg"], corner_radius=0)
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row, text="Cancelar", command=self.destroy,
            fg_color=C["surface"], hover_color=C["border"],
            text_color=C["text_dim"], font=("Consolas", 11),
            width=110, height=34, corner_radius=6,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row, text="Salvar", command=self._save,
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color=C["bg"], font=("Consolas", 11, "bold"),
            width=110, height=34, corner_radius=6,
        ).pack(side="right")

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_theme_preview(self, value: str):
        ctk.set_appearance_mode(value.lower())

    def _save(self):
        capture  = self.capture_var.get().strip().lower()
        dashboard = self.dashboard_var.get().strip().lower()

        if not _validate_hotkey(capture):
            messagebox.showerror(
                "Formato inválido",
                f"Hotkey inválida: '{capture}'\n\nUse o formato: ctrl+shift+space",
                parent=self,
            )
            return

        if not _validate_hotkey(dashboard):
            messagebox.showerror(
                "Formato inválido",
                f"Hotkey inválida: '{dashboard}'\n\nUse o formato: ctrl+shift+f",
                parent=self,
            )
            return

        theme = self._theme_var.get().lower()
        self.config.set("theme", theme)
        ctk.set_appearance_mode(theme)

        new_hotkeys = {"quick_capture": capture, "dashboard": dashboard}
        self.config.set("hotkeys", new_hotkeys)
        self.on_hotkeys_changed(new_hotkeys)
        self.destroy()
