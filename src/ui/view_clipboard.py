"""
ui/view_clipboard.py
Visão de Clipboard — cards FILO clicáveis com botão de cópia.
Suporta captura automática via Ctrl+Shift+C (tratado em app.py).
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from core.storage import Storage, Entry
from ui.colors import COLORS as C


class ClipboardView(ctk.CTkFrame):
    """Cards de clipboard em ordem FILO com ação de cópia por item."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self.storage = storage
        self.on_new = on_new
        self._clips: list[Entry] = []
        self._selected_id: str | None = None
        self._rows: dict[str, ctk.CTkFrame] = {}

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header, text="📋  Clipboard",
            font=("Consolas", 13, "bold"), text_color=("#1A6B8A", "#5CB8E0"),
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Ctrl+Shift+C captura a área de transferência",
            font=("Consolas", 9), text_color=C["text_dim"],
        ).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=C["surface"], corner_radius=8,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=("#1A6B8A", "#5CB8E0"),
        )
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        detail_frame = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=8)
        detail_frame.pack(fill="x", padx=12, pady=(0, 4))
        self.detail_label = ctk.CTkLabel(
            detail_frame,
            text="Selecione um item para ver o conteúdo completo",
            font=("Consolas", 10), text_color=C["text_dim"],
            anchor="w", justify="left", wraplength=660,
        )
        self.detail_label.pack(fill="x", padx=12, pady=10)

        action_bar = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        action_bar.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkButton(
            action_bar, text="📋 Copiar  [C]", command=self._copy_selected,
            fg_color=("#1A6B8A", "#5CB8E0"), hover_color=("#145580", "#3A90B8"),
            text_color=("#FFFFFF", "#1A1A2E"), font=("Consolas", 11, "bold"),
            width=140, height=32, corner_radius=6,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            action_bar, text="🗂 Arquivar  [A]", command=self._archive_selected,
            fg_color=C["accent2"], hover_color=("#7A5800", "#C8A020"),
            text_color=C["bg"], font=("Consolas", 11, "bold"),
            width=140, height=32, corner_radius=6,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            action_bar, text="🗑 Deletar  [Del]", command=self._delete_selected,
            fg_color=C["danger"], hover_color=C["danger_hover"],
            text_color=("#FFFFFF", "#FFFFFF"), font=("Consolas", 11, "bold"),
            width=140, height=32, corner_radius=6,
        ).pack(side="left")

        self.status_label = ctk.CTkLabel(
            action_bar, text="", font=("Consolas", 9), text_color=C["text_dim"],
        )
        self.status_label.pack(side="right")

        self.bind("<c>",      lambda e: self._copy_selected())
        self.bind("<C>",      lambda e: self._copy_selected())
        self.bind("<a>",      lambda e: self._archive_selected())
        self.bind("<A>",      lambda e: self._archive_selected())
        self.bind("<Delete>", lambda e: self._delete_selected())

    def refresh(self):
        self._clips = self.storage.get_by_type("clipboard")
        self._render()

    def _render(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._rows.clear()

        for entry in self._clips:
            ts = entry.created_at[:16].replace("T", " ")
            line = entry.content[:80].replace("\n", " ")

            row = ctk.CTkFrame(self.scroll, fg_color=C["row"], corner_radius=6, cursor="hand2")
            row.pack(fill="x", padx=4, pady=2)

            ctk.CTkLabel(
                row, text=f"📋  {line}",
                anchor="w", text_color=C["text"], font=("Consolas", 10),
            ).pack(side="left", fill="x", expand=True, padx=10, pady=8)

            ctk.CTkLabel(
                row, text=ts,
                anchor="e", text_color=C["text_dim"], font=("Consolas", 9),
            ).pack(side="right", padx=8)

            handler = lambda e, eid=entry.id: self._select(eid)
            row.bind("<Button-1>", handler)
            for child in row.winfo_children():
                child.bind("<Button-1>", handler)

            self._rows[entry.id] = row

        self.status_label.configure(text=f"{len(self._clips)} itens")

    def _select(self, entry_id: str):
        prev = self._rows.get(self._selected_id or "")
        if prev:
            prev.configure(fg_color=C["row"])
            for c in prev.winfo_children():
                try: c.configure(fg_color=C["row"])
                except Exception: pass

        self._selected_id = entry_id
        row = self._rows.get(entry_id)
        if row:
            row.configure(fg_color=C["selected"])
            for c in row.winfo_children():
                try: c.configure(fg_color=C["selected"])
                except Exception: pass

        entry = next((e for e in self._clips if e.id == entry_id), None)
        if entry:
            self.detail_label.configure(text=entry.content[:500], text_color=C["text"])
        self.focus_set()

    def _get_selected(self) -> Entry | None:
        if not self._selected_id: return None
        return next((e for e in self._clips if e.id == self._selected_id), None)

    # ── Navegação por teclado ─────────────────────────────────────────────

    def select_first(self):
        if self._clips:
            self._select(self._clips[0].id)

    def _nav(self, direction: int):
        if not self._clips:
            return
        ids = [e.id for e in self._clips]
        try:
            current = ids.index(self._selected_id) if self._selected_id else -1
        except ValueError:
            current = -1
        idx = (current + direction) % len(self._clips)
        self._select(self._clips[idx].id)

    def _copy_selected(self):
        entry = self._get_selected()
        if not entry: return
        self.clipboard_clear()
        self.clipboard_append(entry.content)
        self.status_label.configure(text="✓ Copiado!")
        self.after(2000, lambda: self.status_label.configure(text=f"{len(self._clips)} itens"))

    def _archive_selected(self):
        entry = self._get_selected()
        if not entry: return
        self.storage.archive(entry.id)
        self._selected_id = None
        self.detail_label.configure(
            text="Selecione um item para ver o conteúdo completo",
            text_color=C["text_dim"],
        )
        self.refresh()

    def _delete_selected(self):
        entry = self._get_selected()
        if not entry: return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(entry.id)
            self._selected_id = None
            self.detail_label.configure(
                text="Selecione um item para ver o conteúdo completo",
                text_color=C["text_dim"],
            )
            self.refresh()
