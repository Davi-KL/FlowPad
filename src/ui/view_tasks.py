"""
ui/view_tasks.py
Visão de Tarefas — lista to-do com checkboxes e filtros Pendentes/Concluídas.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from core.storage import Storage, Entry
from ui.colors import COLORS as C


class TasksView(ctk.CTkFrame):
    """To-Do list com checkboxes e filtros Todas/Pendentes/Concluídas."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self.storage = storage
        self.on_new = on_new
        self._tasks: list[Entry] = []
        self._filtered: list[Entry] = []
        self._filter = "all"
        self._selected_id: str | None = None
        self._rows: dict[str, ctk.CTkFrame] = {}

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        top.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            top, text="✅  Tarefas",
            font=("Consolas", 13, "bold"), text_color=C["accent"],
        ).pack(side="left")

        self._filter_btns: dict[str, ctk.CTkButton] = {}
        for key, label in [("completed", "Concluídas [3]"), ("pending", "Pendentes [2]"), ("all", "Todas [1]")]:
            btn = ctk.CTkButton(
                top, text=label,
                font=("Consolas", 10),
                width=100, height=28, corner_radius=6,
                fg_color=C["selected"] if key == "all" else C["surface"],
                hover_color=C["border"],
                text_color=C["text"],
                command=lambda k=key: self._set_filter(k),
            )
            btn.pack(side="right", padx=2)
            self._filter_btns[key] = btn

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=C["surface"], corner_radius=8,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent"],
        )
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        action_bar = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        action_bar.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkButton(
            action_bar, text="☑ Toggle  [Space]", command=self._toggle_selected,
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color=C["bg"], font=("Consolas", 11, "bold"),
            width=160, height=32, corner_radius=6,
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

        self.bind("<space>",  lambda e: self._toggle_selected())
        self.bind("<Return>", lambda e: self._toggle_selected())
        self.bind("<a>",      lambda e: self._archive_selected())
        self.bind("<A>",      lambda e: self._archive_selected())
        self.bind("<Delete>", lambda e: self._delete_selected())

    def refresh(self):
        self._tasks = self.storage.get_by_type("task")
        self._apply_filter()

    def _set_filter(self, key: str):
        self._filter = key
        for k, btn in self._filter_btns.items():
            btn.configure(fg_color=C["selected"] if k == key else C["surface"])
        self._apply_filter()

    def _apply_filter(self):
        if self._filter == "pending":
            self._filtered = [t for t in self._tasks if not t.completed]
        elif self._filter == "completed":
            self._filtered = [t for t in self._tasks if t.completed]
        else:
            self._filtered = list(self._tasks)
        self._render()

    def _render(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._rows.clear()

        for task in self._filtered:
            icon = "✓" if task.completed else "○"
            line = task.content[:80].replace("\n", " ")
            text_color = C["text_dim"] if task.completed else C["text"]

            row = ctk.CTkFrame(self.scroll, fg_color=C["row"], corner_radius=6, cursor="hand2")
            row.pack(fill="x", padx=4, pady=2)

            ctk.CTkLabel(
                row, text=icon, width=28,
                font=("Consolas", 14, "bold"), text_color=C["accent"] if task.completed else C["text_dim"],
            ).pack(side="left", padx=(10, 0), pady=8)

            ctk.CTkLabel(
                row, text=line,
                anchor="w", text_color=text_color, font=("Consolas", 10),
            ).pack(side="left", fill="x", expand=True, padx=8, pady=8)

            handler = lambda e, eid=task.id: self._select(eid)
            row.bind("<Button-1>", handler)
            for child in row.winfo_children():
                child.bind("<Button-1>", handler)

            self._rows[task.id] = row

        self.status_label.configure(text=f"{len(self._filtered)} tarefas")

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
        self.focus_set()

    def _get_selected(self) -> Entry | None:
        if not self._selected_id: return None
        return next((t for t in self._filtered if t.id == self._selected_id), None)

    # ── Navegação por teclado ─────────────────────────────────────────────

    def select_first(self):
        if self._filtered:
            self._select(self._filtered[0].id)

    def _nav(self, direction: int):
        if not self._filtered:
            return
        ids = [t.id for t in self._filtered]
        try:
            current = ids.index(self._selected_id) if self._selected_id else -1
        except ValueError:
            current = -1
        idx = (current + direction) % len(self._filtered)
        self._select(self._filtered[idx].id)

    def _toggle_selected(self):
        task = self._get_selected()
        if not task: return
        self.storage.toggle_completed(task.id)
        saved_id = self._selected_id
        self.refresh()
        # Restaura seleção após refresh
        if saved_id and saved_id in self._rows:
            self._select(saved_id)

    def _archive_selected(self):
        task = self._get_selected()
        if not task: return
        self.storage.archive(task.id)
        self._selected_id = None
        self.refresh()

    def _delete_selected(self):
        task = self._get_selected()
        if not task: return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(task.id)
            self._selected_id = None
            self.refresh()
