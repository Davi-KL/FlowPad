"""
ui/view_notes.py
Visão de Notas — lista de títulos à esquerda, conteúdo completo à direita.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from core.storage import Storage, Entry

COLORS = {
    "bg":       "#1A1A2E",
    "surface":  "#16213E",
    "surface2": "#0F3460",
    "accent":   "#A07AE0",
    "accent2":  "#F4C542",
    "accent3":  "#5CE07A",
    "text":     "#E8EAF0",
    "text_dim": "#8892A4",
    "selected": "#0F3460",
    "danger":   "#E05C5C",
}


class NotesView(tk.Frame):
    """Lista de títulos (esquerda) + painel de conteúdo (direita)."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, bg=COLORS["bg"])
        self.storage = storage
        self.on_new = on_new
        self._notes: list[Entry] = []
        self._selected_idx = -1

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=8)
        header.pack(fill="x")

        tk.Label(
            header, text="📝  Notas",
            bg=COLORS["bg"], fg=COLORS["accent"],
            font=("Consolas", 11, "bold")
        ).pack(side="left")

        # Main: list (left) + content panel (right)
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        # Left panel — title list
        left = tk.Frame(main, bg=COLORS["bg"], width=220)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        scrollbar = tk.Scrollbar(left, bg=COLORS["surface"], troughcolor=COLORS["bg"])
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            left,
            bg=COLORS["surface"], fg=COLORS["text"],
            selectbackground=COLORS["selected"],
            selectforeground=COLORS["accent"],
            relief="flat", bd=0,
            font=("Consolas", 10),
            activestyle="none",
            yscrollcommand=scrollbar.set,
            width=28,
        )
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Right panel — content display
        right = tk.Frame(main, bg=COLORS["surface"], padx=12, pady=10)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self.title_label = tk.Label(
            right, text="",
            bg=COLORS["surface"], fg=COLORS["accent"],
            font=("Consolas", 11, "bold"), anchor="w",
        )
        self.title_label.pack(fill="x")

        self.content_text = tk.Text(
            right,
            bg=COLORS["surface"], fg=COLORS["text"],
            relief="flat", bd=0,
            font=("Consolas", 10), wrap="word",
            state="disabled",
        )
        self.content_text.pack(fill="both", expand=True, pady=(8, 0))

        action_bar = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=6)
        action_bar.pack(fill="x")

        for label, bg, cmd in [
            ("📋 Copiar  [C]",    COLORS["accent3"], self._copy_selected),
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
        self._notes = self.storage.get_by_type("note")
        self._render()

    def _render(self):
        self.listbox.delete(0, "end")
        for note in self._notes:
            label = note.title or note.content[:30].replace("\n", " ")
            self.listbox.insert("end", f"  {label}")
        self.status_label.config(text=f"{len(self._notes)} notas")

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._selected_idx = sel[0]
        note = self._notes[self._selected_idx]
        self.title_label.config(text=note.title or "Sem título")
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", note.content)
        self.content_text.config(state="disabled")

    def _get_selected(self) -> Entry | None:
        if 0 <= self._selected_idx < len(self._notes):
            return self._notes[self._selected_idx]
        return None

    def _copy_selected(self):
        note = self._get_selected()
        if not note:
            return
        self.clipboard_clear()
        self.clipboard_append(note.content)
        self.status_label.config(text="✓ Copiado!")
        self.after(2000, lambda: self.status_label.config(text=f"{len(self._notes)} notas"))

    def _clear_content_panel(self):
        self.title_label.config(text="")
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.config(state="disabled")

    def _archive_selected(self):
        note = self._get_selected()
        if not note:
            return
        self.storage.archive(note.id)
        self._selected_idx = -1
        self._clear_content_panel()
        self.refresh()

    def _delete_selected(self):
        note = self._get_selected()
        if not note:
            return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(note.id)
            self._selected_idx = -1
            self._clear_content_panel()
            self.refresh()
