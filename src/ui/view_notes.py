"""
ui/view_notes.py
Visão de Notas — lista de títulos à esquerda, conteúdo completo à direita.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from core.storage import Storage, Entry
from ui.colors import COLORS as C

_NOTE_ACCENT = ("#6B3FA0", "#A07AE0")


class NotesView(ctk.CTkFrame):
    """Lista de títulos (esquerda) + painel de conteúdo (direita)."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self.storage = storage
        self.on_new = on_new
        self._notes: list[Entry] = []
        self._selected_id: str | None = None
        self._rows: dict[str, ctk.CTkFrame] = {}

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        header.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            header, text="📝  Notas",
            font=("Consolas", 13, "bold"), text_color=_NOTE_ACCENT,
        ).pack(side="left")

        # Main area: title list (left) + content (right)
        main = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        main.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        # Left: scrollable title list
        left = ctk.CTkFrame(main, fg_color=C["bg"], corner_radius=0, width=240)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self.title_scroll = ctk.CTkScrollableFrame(
            left, fg_color=C["surface"], corner_radius=8,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=_NOTE_ACCENT,
        )
        self.title_scroll.pack(fill="both", expand=True)

        # Right: content panel
        right = ctk.CTkFrame(main, fg_color=C["surface"], corner_radius=8)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self.title_label = ctk.CTkLabel(
            right, text="",
            font=("Consolas", 12, "bold"), text_color=_NOTE_ACCENT,
            anchor="w",
        )
        self.title_label.pack(fill="x", padx=12, pady=(10, 4))

        self.content_text = ctk.CTkTextbox(
            right,
            font=("Consolas", 10), wrap="word",
            fg_color=C["surface"], text_color=C["text"],
            state="disabled",
        )
        self.content_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Actions
        action_bar = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        action_bar.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkButton(
            action_bar, text="📋 Copiar  [C]", command=self._copy_selected,
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color=C["bg"], font=("Consolas", 11, "bold"),
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
        self._notes = self.storage.get_by_type("note")
        self._render()

    def _render(self):
        for w in self.title_scroll.winfo_children():
            w.destroy()
        self._rows.clear()

        for note in self._notes:
            label_text = note.title or note.content[:30].replace("\n", " ")

            row = ctk.CTkFrame(self.title_scroll, fg_color=C["row"], corner_radius=6, cursor="hand2")
            row.pack(fill="x", padx=4, pady=2)

            ctk.CTkLabel(
                row, text=f"📝  {label_text}",
                anchor="w", text_color=C["text"], font=("Consolas", 10),
            ).pack(fill="x", padx=10, pady=8)

            handler = lambda e, nid=note.id: self._select(nid)
            row.bind("<Button-1>", handler)
            for child in row.winfo_children():
                child.bind("<Button-1>", handler)

            self._rows[note.id] = row

        self.status_label.configure(text=f"{len(self._notes)} notas")

    def _select(self, note_id: str):
        prev = self._rows.get(self._selected_id or "")
        if prev:
            prev.configure(fg_color=C["row"])
            for c in prev.winfo_children():
                try: c.configure(fg_color=C["row"])
                except Exception: pass

        self._selected_id = note_id
        row = self._rows.get(note_id)
        if row:
            row.configure(fg_color=C["selected"])
            for c in row.winfo_children():
                try: c.configure(fg_color=C["selected"])
                except Exception: pass

        note = next((n for n in self._notes if n.id == note_id), None)
        if note:
            self.title_label.configure(text=note.title or "Sem título")
            self.content_text.configure(state="normal")
            self.content_text.delete("0.0", "end")
            self.content_text.insert("0.0", note.content)
            self.content_text.configure(state="disabled")
        self.focus_set()

    def _get_selected(self) -> Entry | None:
        if not self._selected_id: return None
        return next((n for n in self._notes if n.id == self._selected_id), None)

    # ── Navegação por teclado ─────────────────────────────────────────────

    def select_first(self):
        if self._notes:
            self._select(self._notes[0].id)

    def _nav(self, direction: int):
        if not self._notes:
            return
        ids = [n.id for n in self._notes]
        try:
            current = ids.index(self._selected_id) if self._selected_id else -1
        except ValueError:
            current = -1
        idx = (current + direction) % len(self._notes)
        self._select(self._notes[idx].id)

    def _copy_selected(self):
        note = self._get_selected()
        if not note: return
        self.clipboard_clear()
        self.clipboard_append(note.content)
        self.status_label.configure(text="✓ Copiado!")
        self.after(2000, lambda: self.status_label.configure(text=f"{len(self._notes)} notas"))

    def _clear_content_panel(self):
        self.title_label.configure(text="")
        self.content_text.configure(state="normal")
        self.content_text.delete("0.0", "end")
        self.content_text.configure(state="disabled")

    def _archive_selected(self):
        note = self._get_selected()
        if not note: return
        self.storage.archive(note.id)
        self._selected_id = None
        self._clear_content_panel()
        self.refresh()

    def _delete_selected(self):
        note = self._get_selected()
        if not note: return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(note.id)
            self._selected_id = None
            self._clear_content_panel()
            self.refresh()
