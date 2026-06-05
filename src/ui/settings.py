"""
ui/settings.py
Tela de configurações do FlowPad.
Permite alterar hotkeys globais sem editar o arquivo JSON manualmente.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from utils.config import Config


COLORS = {
    "bg":       "#1A1A2E",
    "surface":  "#16213E",
    "border":   "#0F3460",
    "accent":   "#5CE07A",
    "text":     "#E8EAF0",
    "text_dim": "#8892A4",
}

# Modificadores e teclas especiais aceitas pelo pynput
_VALID_MODIFIERS = {"ctrl", "shift", "alt", "cmd"}
_VALID_SPECIALS = {
    "space", "enter", "tab", "esc", "backspace",
    "f1", "f2", "f3", "f4", "f5", "f6",
    "f7", "f8", "f9", "f10", "f11", "f12",
}


def _validate_hotkey(key_string: str) -> bool:
    """
    Valida se a string está no formato aceito pelo HotkeyManager.
    Ex: "ctrl+shift+space", "ctrl+alt+n" — retorna True se válido.
    """
    parts = [p.strip().lower() for p in key_string.split("+") if p.strip()]
    if len(parts) < 2:
        return False
    modifiers = [p for p in parts if p in _VALID_MODIFIERS]
    keys = [p for p in parts if p not in _VALID_MODIFIERS]
    if not modifiers or not keys:
        return False
    for key in keys:
        if not (key in _VALID_SPECIALS or (len(key) == 1 and key.isalpha())):
            return False
    return True


class SettingsWindow(tk.Toplevel):
    """
    Janela de configurações com campos para alterar as hotkeys globais.
    Ao salvar, persiste no config.json e chama on_hotkeys_changed para
    recarregar os atalhos sem reiniciar o app.
    """

    def __init__(
        self,
        master: tk.Tk,
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
        self.geometry("440x300")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
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
        header = tk.Frame(self, bg=COLORS["surface"], pady=10, padx=16)
        header.pack(fill="x")
        tk.Label(
            header, text="⚙️  Configurações",
            bg=COLORS["surface"], fg=COLORS["accent"],
            font=("Consolas", 12, "bold"),
        ).pack(side="left")

        body = tk.Frame(self, bg=COLORS["bg"], padx=24, pady=20)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)

        hotkeys = self.config.get("hotkeys", {})

        # Hotkey — Captura rápida
        tk.Label(
            body, text="Hotkey — Captura Rápida",
            bg=COLORS["bg"], fg=COLORS["text_dim"], font=("Consolas", 9),
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.capture_var = tk.StringVar(
            value=hotkeys.get("quick_capture", "ctrl+shift+space")
        )
        tk.Entry(
            body, textvariable=self.capture_var,
            bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat", font=("Consolas", 11), width=30,
        ).grid(row=1, column=0, sticky="ew", ipady=7, pady=(0, 14))

        # Hotkey — Dashboard
        tk.Label(
            body, text="Hotkey — Dashboard",
            bg=COLORS["bg"], fg=COLORS["text_dim"], font=("Consolas", 9),
        ).grid(row=2, column=0, sticky="w", pady=(0, 4))

        self.dashboard_var = tk.StringVar(
            value=hotkeys.get("dashboard", "ctrl+shift+f")
        )
        tk.Entry(
            body, textvariable=self.dashboard_var,
            bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat", font=("Consolas", 11), width=30,
        ).grid(row=3, column=0, sticky="ew", ipady=7, pady=(0, 6))

        tk.Label(
            body,
            text="Formato: ctrl+shift+space  |  ctrl+alt+n  |  ctrl+shift+f",
            bg=COLORS["bg"], fg=COLORS["text_dim"], font=("Consolas", 7),
        ).grid(row=4, column=0, sticky="w", pady=(0, 18))

        # Botões
        btn_frame = tk.Frame(body, bg=COLORS["bg"])
        btn_frame.grid(row=5, column=0, sticky="e")

        tk.Button(
            btn_frame, text="Cancelar",
            bg=COLORS["surface"], fg=COLORS["text_dim"],
            relief="flat", bd=0, padx=10, pady=5,
            font=("Consolas", 9), cursor="hand2",
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_frame, text="Salvar",
            bg=COLORS["accent"], fg=COLORS["bg"],
            relief="flat", bd=0, padx=14, pady=5,
            font=("Consolas", 9, "bold"), cursor="hand2",
            command=self._save,
        ).pack(side="left")

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _save(self):
        capture = self.capture_var.get().strip().lower()
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

        new_hotkeys = {"quick_capture": capture, "dashboard": dashboard}
        self.config.set("hotkeys", new_hotkeys)
        self.on_hotkeys_changed(new_hotkeys)
        self.destroy()
