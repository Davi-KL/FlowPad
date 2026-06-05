"""
ui/view_notes.py
Visão de Notas — lista de títulos à esquerda, conteúdo completo à direita.
Suporta busca fuzzy e edição inline no painel direito.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from core.storage import Storage, Entry
from ui.colors import COLORS as C
from utils.fuzzy import fuzzy_match

_NOTE_ACCENT = ("#6B3FA0", "#A07AE0")


class NotesView(ctk.CTkFrame):
    """Lista de títulos (esquerda) + painel de conteúdo/edição (direita)."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self.storage = storage
        self.on_new = on_new
        self._notes: list[Entry] = []
        self._filtered: list[Entry] = []
        self._search_text: str = ""
        self._selected_id: str | None = None
        self._rows: dict[str, ctk.CTkFrame] = {}
        self._editing: bool = False

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        header.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            header, text="📝  Notas",
            font=("Consolas", 13, "bold"), text_color=_NOTE_ACCENT,
        ).pack(side="left")

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

        # Main area: title list (left) + content/edit (right)
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

        # Right: content/edit panel
        self._right = ctk.CTkFrame(main, fg_color=C["surface"], corner_radius=8)
        self._right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self._build_view_panel()

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

    # ── Painel direito: modo leitura vs edição ────────────────────────────

    def _build_view_panel(self):
        """Reconstrói o painel direito em modo leitura."""
        for w in self._right.winfo_children():
            w.destroy()
        self._editing = False

        self.title_label = ctk.CTkLabel(
            self._right, text="",
            font=("Consolas", 12, "bold"), text_color=_NOTE_ACCENT,
            anchor="w",
        )
        self.title_label.pack(fill="x", padx=12, pady=(10, 4))

        self.content_text = ctk.CTkTextbox(
            self._right,
            font=("Consolas", 10), wrap="word",
            fg_color=C["surface"], text_color=C["text"],
            state="disabled",
        )
        self.content_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _build_edit_panel(self, note: Entry):
        """Reconstrói o painel direito em modo edição."""
        for w in self._right.winfo_children():
            w.destroy()
        self._editing = True

        ctk.CTkLabel(
            self._right, text="Título:",
            font=("Consolas", 9), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 2))

        self._edit_title = ctk.CTkEntry(
            self._right, font=("Consolas", 11), height=32,
            fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], border_width=1,
        )
        self._edit_title.pack(fill="x", padx=12, pady=(0, 8))
        self._edit_title.insert(0, note.title or "")
        self._edit_title.focus_set()

        ctk.CTkLabel(
            self._right, text="Conteúdo:",
            font=("Consolas", 9), text_color=C["text_dim"], anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 2))

        self._edit_content = ctk.CTkTextbox(
            self._right, font=("Consolas", 10), wrap="word",
            fg_color=C["surface"], text_color=C["text"],
        )
        self._edit_content.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self._edit_content.insert("0.0", note.content)

        btns = ctk.CTkFrame(self._right, fg_color=C["surface"], corner_radius=0)
        btns.pack(fill="x", padx=12, pady=(0, 10))

        def do_save():
            new_title = self._edit_title.get().strip()
            new_content = self._edit_content.get("0.0", "end").strip()
            self.storage.update_entry(note.id, title=new_title, content=new_content)
            nid = note.id
            self._build_view_panel()
            self.refresh()
            if nid in self._rows:
                self._select(nid)

        def do_cancel():
            nid = note.id
            self._build_view_panel()
            self.refresh()
            if nid in self._rows:
                self._select(nid)

        self._edit_title.bind("<Control-Return>",   lambda e: do_save())
        self._edit_title.bind("<Escape>",           lambda e: do_cancel())
        self._edit_content.bind("<Control-Return>", lambda e: do_save())
        self._edit_content.bind("<Escape>",         lambda e: do_cancel())

        ctk.CTkButton(
            btns, text="Salvar  Ctrl+↵", command=do_save,
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color=C["bg"], font=("Consolas", 11, "bold"),
            width=130, height=30, corner_radius=6,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btns, text="Cancelar  Esc", command=do_cancel,
            fg_color=C["surface"], hover_color=C["border"],
            text_color=C["text_dim"], font=("Consolas", 11),
            width=120, height=30, corner_radius=6,
        ).pack(side="left")

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
        self._notes = self.storage.get_by_type("note")
        self._apply_filter()

    def _apply_filter(self):
        q = self._search_text.strip()
        if q:
            self._filtered = [
                n for n in self._notes
                if fuzzy_match(q, f"{n.title} {n.content}")
            ]
        else:
            self._filtered = list(self._notes)
        self._render()

    def _render(self):
        for w in self.title_scroll.winfo_children():
            w.destroy()
        self._rows.clear()

        for note in self._filtered:
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

        n = len(self._filtered)
        total = len(self._notes)
        self.status_label.configure(
            text=f"{n} de {total} notas" if self._search_text else f"{total} notas"
        )

    def _select(self, note_id: str):
        if self._editing:
            return  # não interrompe edição em andamento

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

        note = next((n for n in self._filtered if n.id == note_id), None)
        if note:
            self.title_label.configure(text=note.title or "Sem título")
            self.content_text.configure(state="normal")
            self.content_text.delete("0.0", "end")
            self.content_text.insert("0.0", note.content)
            self.content_text.configure(state="disabled")
        self.focus_set()

    def _get_selected(self) -> Entry | None:
        if not self._selected_id: return None
        return next((n for n in self._filtered if n.id == self._selected_id), None)

    # ── Navegação por teclado ─────────────────────────────────────────────

    def select_first(self):
        if self._filtered:
            self._select(self._filtered[0].id)

    def _nav(self, direction: int):
        if not self._filtered:
            return
        ids = [n.id for n in self._filtered]
        try:
            current = ids.index(self._selected_id) if self._selected_id else -1
        except ValueError:
            current = -1
        idx = (current + direction) % len(self._filtered)
        self._select(self._filtered[idx].id)

    # ── Edição inline ─────────────────────────────────────────────────────

    def _edit_selected(self):
        if self._editing:
            return
        note = self._get_selected()
        if not note:
            return
        self._build_edit_panel(note)

    # ── Actions ───────────────────────────────────────────────────────────

    def _copy_selected(self):
        note = self._get_selected()
        if not note: return
        self.clipboard_clear()
        self.clipboard_append(note.content)
        self.status_label.configure(text="✓ Copiado!")
        self.after(2000, lambda: self.status_label.configure(
            text=f"{len(self._filtered)} notas"
        ))

    def _clear_content_panel(self):
        if not self._editing:
            self.title_label.configure(text="")
            self.content_text.configure(state="normal")
            self.content_text.delete("0.0", "end")
            self.content_text.configure(state="disabled")

    def _archive_selected(self):
        note = self._get_selected()
        if not note: return
        self.storage.archive(note.id)
        self._selected_id = None
        if self._editing:
            self._build_view_panel()
        else:
            self._clear_content_panel()
        self.refresh()

    def _delete_selected(self):
        note = self._get_selected()
        if not note: return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(note.id)
            self._selected_id = None
            if self._editing:
                self._build_view_panel()
            else:
                self._clear_content_panel()
            self.refresh()
