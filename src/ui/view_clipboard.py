"""
ui/view_clipboard.py
Visão de Clipboard — cards FILO com busca fuzzy, edição inline e captura automática.
Suporta captura automática via Ctrl+Alt+C (tratado em app.py).
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from core.storage import Storage, Entry
from ui.colors import COLORS as C
from utils.fuzzy import fuzzy_match


class ClipboardView(ctk.CTkFrame):
    """Cards de clipboard em ordem FILO com ação de cópia por item."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self.storage = storage
        self.on_new = on_new
        self._clips: list[Entry] = []
        self._filtered: list[Entry] = []
        self._search_text: str = ""
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
            header, text="Histórico automático de tudo que você copiar",
            font=("Consolas", 9), text_color=C["text_dim"],
        ).pack(side="right")

        # Busca
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_changed())
        self.search_entry = ctk.CTkEntry(
            self, textvariable=self._search_var,
            placeholder_text="🔍  Buscar...  [Ctrl+F]",
            font=("Consolas", 10), height=30,
            fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], border_width=1,
        )
        self.search_entry.pack(fill="x", padx=12, pady=(0, 4))
        self.search_entry.bind("<Escape>", self._on_search_escape)

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
            action_bar, text="✏ Editar  [E]", command=self._edit_selected,
            fg_color=C["surface"], hover_color=C["border"],
            text_color=C["text"], font=("Consolas", 11, "bold"),
            width=120, height=32, corner_radius=6,
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
        self.bind("<e>",      lambda e: self._edit_selected())
        self.bind("<E>",      lambda e: self._edit_selected())
        self.bind("<Delete>", lambda e: self._delete_selected())

    # ── Busca ─────────────────────────────────────────────────────────────

    def focus_search(self):
        self.search_entry.focus_set()
        self.search_entry._entry.select_range(0, "end")

    def _clear_search(self):
        self._search_var.set("")
        self._search_text = ""
        self.focus_set()

    def _on_search_escape(self, event):
        self._clear_search()
        self._apply_filter()
        return "break"

    def _on_search_changed(self):
        self._search_text = self._search_var.get()
        self._apply_filter()

    # ── Data ──────────────────────────────────────────────────────────────

    def refresh(self):
        self._clips = self.storage.get_by_type("clipboard")
        self._apply_filter()

    def _apply_filter(self):
        q = self._search_text.strip()
        if q:
            self._filtered = [
                e for e in self._clips
                if fuzzy_match(q, e.content)
            ]
        else:
            self._filtered = list(self._clips)
        self._render()

    def _render(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._rows.clear()

        for entry in self._filtered:
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

        n = len(self._filtered)
        total = len(self._clips)
        self.status_label.configure(
            text=f"{n} de {total} itens" if self._search_text else f"{total} itens"
        )

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

        entry = next((e for e in self._filtered if e.id == entry_id), None)
        if entry:
            self.detail_label.configure(text=entry.content[:500], text_color=C["text"])
        self.focus_set()

    def _get_selected(self) -> Entry | None:
        if not self._selected_id: return None
        return next((e for e in self._filtered if e.id == self._selected_id), None)

    # ── Navegação por teclado ─────────────────────────────────────────────

    def select_first(self):
        if self._filtered:
            self._select(self._filtered[0].id)

    def _nav(self, direction: int):
        if not self._filtered:
            return
        ids = [e.id for e in self._filtered]
        try:
            current = ids.index(self._selected_id) if self._selected_id else -1
        except ValueError:
            current = -1
        idx = (current + direction) % len(self._filtered)
        self._select(self._filtered[idx].id)

    # ── Edição inline ─────────────────────────────────────────────────────

    def _edit_selected(self):
        entry = self._get_selected()
        if not entry:
            return
        row = self._rows.get(entry.id)
        if not row:
            return
        for w in row.winfo_children():
            w.destroy()
        row.configure(fg_color=C["selected"], cursor="arrow")

        box = ctk.CTkTextbox(
            row, font=("Consolas", 10), height=70, wrap="word",
            fg_color=C["surface"], text_color=C["text"],
        )
        box.pack(fill="x", padx=8, pady=(8, 4))
        box.insert("0.0", entry.content)
        box.focus_set()

        btns = ctk.CTkFrame(row, fg_color=C["selected"], corner_radius=0)
        btns.pack(fill="x", padx=8, pady=(0, 8))

        def do_save():
            new_text = box.get("0.0", "end").strip()
            if new_text:
                self.storage.update_entry(entry.id, content=new_text)
            eid = entry.id
            self.refresh()
            if eid in self._rows:
                self._select(eid)

        def do_cancel():
            eid = entry.id
            self.refresh()
            if eid in self._rows:
                self._select(eid)

        box.bind("<Escape>",         lambda e: do_cancel())
        box.bind("<Control-Return>", lambda e: do_save())

        ctk.CTkButton(
            btns, text="Salvar  Ctrl+↵", command=do_save,
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color=C["bg"], font=("Consolas", 10, "bold"),
            width=120, height=26, corner_radius=4,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btns, text="Cancelar  Esc", command=do_cancel,
            fg_color=C["surface"], hover_color=C["border"],
            text_color=C["text_dim"], font=("Consolas", 10),
            width=110, height=26, corner_radius=4,
        ).pack(side="left")

    # ── Actions ───────────────────────────────────────────────────────────

    def _copy_selected(self):
        entry = self._get_selected()
        if not entry: return
        self.clipboard_clear()
        self.clipboard_append(entry.content)
        self.status_label.configure(text="✓ Copiado!")
        self.after(2000, lambda: self.status_label.configure(
            text=f"{len(self._filtered)} itens"
        ))

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
