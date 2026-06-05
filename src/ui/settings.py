"""
ui/settings.py
Tela de configurações do FlowPad — hotkeys, tema e pasta de dados.
"""

import os
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
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
    Janela de configurações com campos para alterar hotkeys, tema e pasta de dados.
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
        self.geometry("460x560")
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
        body.pack(fill="both", expand=True, padx=24, pady=12)

        hotkeys = self.config.get("hotkeys", {})

        # ── Tema ──────────────────────────────────────────────────────────
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
        ).pack(fill="x", pady=(0, 14))

        # ── Hotkeys ───────────────────────────────────────────────────────
        self._hotkey_fields = [
            ("Hotkey — Captura Rápida",  "quick_capture",          "ctrl+shift+space"),
            ("Hotkey — Dashboard",        "dashboard",              "ctrl+shift+f"),
            ("Hotkey — Lembrete Direto",  "quick_capture_reminder", "ctrl+alt+r"),
        ]
        self._hotkey_vars: dict[str, tk.StringVar] = {}

        for label, key, default in self._hotkey_fields:
            ctk.CTkLabel(
                body, text=label,
                font=("Consolas", 9), text_color=C["text_dim"], anchor="w",
            ).pack(fill="x", pady=(0, 2))

            var = tk.StringVar(value=hotkeys.get(key, default))
            self._hotkey_vars[key] = var
            ctk.CTkEntry(
                body, textvariable=var,
                font=("Consolas", 11), height=34,
                fg_color=C["surface"], text_color=C["text"],
                border_color=C["border"], border_width=1,
            ).pack(fill="x", pady=(0, 8))

        hint_row = ctk.CTkFrame(body, fg_color=C["bg"], corner_radius=0)
        hint_row.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            hint_row, text="Formato: ctrl+shift+space  |  ctrl+alt+n",
            font=("Consolas", 8), text_color=C["text_dim"], anchor="w",
        ).pack(side="left")

        ctk.CTkButton(
            hint_row, text="Restaurar padrões", command=self._reset_hotkeys,
            fg_color="transparent", hover_color=C["border"],
            text_color=C["text_dim"], font=("Consolas", 8),
            width=120, height=22, corner_radius=4,
        ).pack(side="right")

        # ── Clipboard ─────────────────────────────────────────────────────
        ctk.CTkFrame(body, fg_color=C["border"], height=1, corner_radius=0).pack(
            fill="x", pady=(0, 10)
        )

        self._monitor_var = tk.BooleanVar(value=self.config.get("clipboard_monitor", True))
        ctk.CTkSwitch(
            body,
            text="Monitorar clipboard automaticamente",
            variable=self._monitor_var,
            onvalue=True,
            offvalue=False,
            font=("Consolas", 10),
            text_color=C["text"],
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            body,
            text="Salva tudo que você copiar (Ctrl+C) no histórico de Clipboard.",
            font=("Consolas", 8), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", pady=(0, 10))

        # ── Pasta de dados ────────────────────────────────────────────────
        ctk.CTkFrame(body, fg_color=C["border"], height=1, corner_radius=0).pack(
            fill="x", pady=(0, 10)
        )

        ctk.CTkLabel(
            body, text="Pasta de Dados  (OneDrive / Dropbox / etc.)",
            font=("Consolas", 9), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        dir_row = ctk.CTkFrame(body, fg_color=C["bg"], corner_radius=0)
        dir_row.pack(fill="x", pady=(0, 4))

        current_dir = os.path.dirname(self.config.data_path)
        self._data_dir_var = tk.StringVar(value=current_dir)
        ctk.CTkEntry(
            dir_row, textvariable=self._data_dir_var,
            font=("Consolas", 10), height=32,
            fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], border_width=1,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            dir_row, text="Procurar…", command=self._browse_data_dir,
            fg_color=C["surface"], hover_color=C["border"],
            text_color=C["text"], font=("Consolas", 10),
            width=80, height=32, corner_radius=6,
        ).pack(side="left")

        ctk.CTkLabel(
            body, text="⚠  Reinicie o FlowPad para aplicar mudanças de pasta.",
            font=("Consolas", 8), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", pady=(0, 12))

        # ── Botões ────────────────────────────────────────────────────────
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

    def _reset_hotkeys(self):
        """Restaura todos os hotkeys para os valores padrão."""
        for _, key, default in self._hotkey_fields:
            self._hotkey_vars[key].set(default)

    def _on_theme_preview(self, value: str):
        ctk.set_appearance_mode(value.lower())

    def _browse_data_dir(self):
        path = filedialog.askdirectory(title="Selecionar pasta de dados", parent=self)
        if path:
            self._data_dir_var.set(path)

    def _save(self):
        # Valida todos os hotkeys
        new_hotkeys = {}
        for key, var in self._hotkey_vars.items():
            value = var.get().strip().lower()
            if not _validate_hotkey(value):
                messagebox.showerror(
                    "Formato inválido",
                    f"Hotkey inválida: '{value}'\n\nUse o formato: ctrl+shift+space",
                    parent=self,
                )
                return
            new_hotkeys[key] = value

        theme = self._theme_var.get().lower()
        self.config.set("theme", theme)
        ctk.set_appearance_mode(theme)

        self.config.set("clipboard_monitor", self._monitor_var.get())

        # Preserva qualquer hotkey extra que não esteja na tela
        existing_hotkeys = self.config.get("hotkeys", {})
        existing_hotkeys.update(new_hotkeys)
        self.config.set("hotkeys", existing_hotkeys)
        self.on_hotkeys_changed(new_hotkeys)

        # Salva pasta de dados customizada
        new_dir = self._data_dir_var.get().strip()
        current_dir = os.path.dirname(self.config.data_path)
        if new_dir and new_dir != current_dir:
            self._migrate_data(current_dir, new_dir)

        self.destroy()

    def _migrate_data(self, current_dir: str, new_dir: str):
        """Oferece migração do entries.json para a nova pasta antes de salvar."""
        src = Path(current_dir) / "entries.json"
        dst_dir = Path(new_dir)
        dst = dst_dir / "entries.json"

        # Garante que a pasta de destino existe
        try:
            dst_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Erro", f"Não foi possível acessar a pasta:\n{e}", parent=self)
            return

        if src.exists():
            if dst.exists():
                # Destino já tem um entries.json — pergunta o que fazer
                action = messagebox.askyesnocancel(
                    "Conflito de arquivos",
                    f"A pasta de destino já contém um entries.json.\n\n"
                    f"• Sim  — substituir pelo arquivo atual\n"
                    f"• Não  — manter o arquivo existente no destino\n"
                    f"• Cancelar — não mudar a pasta",
                    parent=self,
                )
                if action is None:   # Cancelar
                    return
                if action:           # Sim — sobrescreve
                    try:
                        shutil.copy2(src, dst)
                    except OSError as e:
                        messagebox.showerror("Erro ao copiar", str(e), parent=self)
                        return
                # Não — mantém o existente, apenas muda o caminho
            else:
                # Destino vazio: copia silenciosamente
                try:
                    shutil.copy2(src, dst)
                except OSError as e:
                    messagebox.showerror("Erro ao copiar", str(e), parent=self)
                    return

        self.config.set("custom_data_dir", new_dir)
        messagebox.showinfo(
            "Pasta alterada",
            "Pasta de dados atualizada.\nReinicie o FlowPad para aplicar a mudança.",
            parent=self,
        )
