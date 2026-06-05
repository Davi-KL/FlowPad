"""
ui/view_clipboard.py
Visão de Clipboard — cards FILO com botão de cópia por item.
Suporta captura automática via Ctrl+Shift+C (tratado em app.py).
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from core.storage import Storage, Entry

COLORS = {
    "bg":       "#1A1A2E",
    "surface":  "#16213E",
    "accent":   "#5CB8E0",
    "accent2":  "#F4C542",
    "text":     "#E8EAF0",
    "text_dim": "#8892A4",
    "selected": "#0F3460",
    "danger":   "#E05C5C",
}


class ClipboardView(tk.Frame):
    """Cards de clipboard em ordem FILO com botão de cópia por item."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, bg=COLORS["bg"])
        self.storage = storage
        self.on_new = on_new
        self._clips: list[Entry] = []
        self._selected_idx = -1

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=8)
        header.pack(fill="x")

        tk.Label(
            header, text="📋  Clipboard",
            bg=COLORS["bg"], fg=COLORS["accent"],
            font=("Consolas", 11, "bold")
        ).pack(side="left")

        tk.Label(
            header, text="Ctrl+Shift+C captura a área de transferência",
            bg=COLORS["bg"], fg=COLORS["text_dim"],
            font=("Consolas", 8)
        ).pack(side="right")

        list_frame = tk.Frame(self, bg=COLORS["bg"])
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        scrollbar = tk.Scrollbar(list_frame, bg=COLORS["surface"], troughcolor=COLORS["bg"])
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            bg=COLORS["surface"], fg=COLORS["text"],
            selectbackground=COLORS["selected"],
            selectforeground=COLORS["accent"],
            relief="flat", bd=0,
            font=("Consolas", 10),
            activestyle="none",
            yscrollcommand=scrollbar.set,
        )
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        detail_frame = tk.Frame(self, bg=COLORS["surface"], padx=12, pady=8)
        detail_frame.pack(fill="x", padx=12, pady=(0, 4))

        self.detail_label = tk.Label(
            detail_frame,
            text="Selecione um item para ver o conteúdo completo",
            bg=COLORS["surface"], fg=COLORS["text_dim"],
            font=("Consolas", 9), anchor="w", justify="left", wraplength=680,
        )
        self.detail_label.pack(fill="x")

        action_bar = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=6)
        action_bar.pack(fill="x")

        for label, bg, cmd in [
            ("📋 Copiar  [C]",    COLORS["accent"],  self._copy_selected),
            ("🗂 Arquivar  [A]",  COLORS["accent2"], self._archive_selected),
            ("🗑 Deletar  [Del]", COLORS["danger"],  self._delete_selected),
        ]:
            tk.Button(
                action_bar, text=label,
                bg=bg, fg=COLORS["bg"],
                relief="flat", bd=0, padx=10, pady=4,
                font=("Consolas", 8, "bold"), cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=(0, 4))

        self.status_label = tk.Label(
            action_bar, text="",
            bg=COLORS["bg"], fg=COLORS["text_dim"], font=("Consolas", 8)
        )
        self.status_label.pack(side="right")

        for widget in (self, self.listbox):
            widget.bind("<c>",      lambda e: self._copy_selected())
            widget.bind("<C>",      lambda e: self._copy_selected())
            widget.bind("<a>",      lambda e: self._archive_selected())
            widget.bind("<A>",      lambda e: self._archive_selected())
            widget.bind("<Delete>", lambda e: self._delete_selected())

    def refresh(self):
        self._clips = self.storage.get_by_type("clipboard")
        self._render()

    def _render(self):
        self.listbox.delete(0, "end")
        for entry in self._clips:
            ts = entry.created_at[:16].replace("T", " ")
            line = entry.content[:80].replace("\n", " ")
            self.listbox.insert("end", f"  📋  {line}  —  {ts}")
        self.status_label.config(text=f"{len(self._clips)} itens")

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._selected_idx = sel[0]
        entry = self._clips[self._selected_idx]
        self.detail_label.config(text=entry.content[:500], fg=COLORS["text"])

    def _get_selected(self) -> Entry | None:
        if 0 <= self._selected_idx < len(self._clips):
            return self._clips[self._selected_idx]
        return None

    def _copy_selected(self):
        entry = self._get_selected()
        if not entry:
            return
        self.clipboard_clear()
        self.clipboard_append(entry.content)
        self.status_label.config(text="✓ Copiado!")
        self.after(2000, lambda: self.status_label.config(text=f"{len(self._clips)} itens"))

    def _archive_selected(self):
        entry = self._get_selected()
        if not entry:
            return
        self.storage.archive(entry.id)
        self._selected_idx = -1
        self.detail_label.config(
            text="Selecione um item para ver o conteúdo completo",
            fg=COLORS["text_dim"]
        )
        self.refresh()

    def _delete_selected(self):
        entry = self._get_selected()
        if not entry:
            return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(entry.id)
            self._selected_idx = -1
            self.detail_label.config(
                text="Selecione um item para ver o conteúdo completo",
                fg=COLORS["text_dim"]
            )
            self.refresh()
