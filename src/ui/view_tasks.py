"""
ui/view_tasks.py
Visão de Tarefas — lista to-do com toggle de conclusão e filtros.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from core.storage import Storage, Entry

COLORS = {
    "bg":       "#1A1A2E",
    "surface":  "#16213E",
    "surface2": "#0F3460",
    "accent":   "#5CE07A",
    "accent2":  "#F4C542",
    "text":     "#E8EAF0",
    "text_dim": "#8892A4",
    "selected": "#0F3460",
    "danger":   "#E05C5C",
}


class TasksView(tk.Frame):
    """To-Do list de tarefas com toggle de conclusão e filtros Pendentes/Concluídas."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, bg=COLORS["bg"])
        self.storage = storage
        self.on_new = on_new
        self._tasks: list[Entry] = []
        self._filtered: list[Entry] = []
        self._filter = "all"
        self._selected_idx = -1

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=8)
        top.pack(fill="x")

        tk.Label(
            top, text="✅  Tarefas",
            bg=COLORS["bg"], fg=COLORS["accent"],
            font=("Consolas", 11, "bold")
        ).pack(side="left")

        self._filter_btns: dict[str, tk.Button] = {}
        for key, label in [("completed", "Concluídas"), ("pending", "Pendentes"), ("all", "Todas")]:
            btn = tk.Button(
                top, text=label,
                bg=COLORS["surface2"] if key == "all" else COLORS["surface"],
                fg=COLORS["text"],
                relief="flat", bd=0, padx=10, pady=3,
                font=("Consolas", 8), cursor="hand2",
                command=lambda k=key: self._set_filter(k),
            )
            btn.pack(side="right", padx=2)
            self._filter_btns[key] = btn

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

        action_bar = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=6)
        action_bar.pack(fill="x")

        for label, bg, cmd in [
            ("☑ Toggle  [Space]", COLORS["accent"],  self._toggle_selected),
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
            widget.bind("<space>",  lambda e: self._toggle_selected())
            widget.bind("<Return>", lambda e: self._toggle_selected())
            widget.bind("<a>",      lambda e: self._archive_selected())
            widget.bind("<A>",      lambda e: self._archive_selected())
            widget.bind("<Delete>", lambda e: self._delete_selected())

    def refresh(self):
        self._tasks = self.storage.get_by_type("task")
        self._apply_filter()

    def _set_filter(self, key: str):
        self._filter = key
        for k, btn in self._filter_btns.items():
            btn.config(bg=COLORS["surface2"] if k == key else COLORS["surface"])
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
        self.listbox.delete(0, "end")
        for task in self._filtered:
            check = "✓" if task.completed else "○"
            line = task.content[:80].replace("\n", " ")
            self.listbox.insert("end", f"  {check}  {line}")
            if task.completed:
                self.listbox.itemconfig("end", fg=COLORS["text_dim"])
        self.status_label.config(text=f"{len(self._filtered)} tarefas")

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if sel:
            self._selected_idx = sel[0]

    def _get_selected(self) -> Entry | None:
        if 0 <= self._selected_idx < len(self._filtered):
            return self._filtered[self._selected_idx]
        return None

    def _toggle_selected(self):
        task = self._get_selected()
        if not task:
            return
        self.storage.toggle_completed(task.id)
        self.refresh()
        if self._selected_idx < self.listbox.size():
            self.listbox.selection_set(self._selected_idx)
            self.listbox.activate(self._selected_idx)

    def _archive_selected(self):
        task = self._get_selected()
        if not task:
            return
        self.storage.archive(task.id)
        self._selected_idx = -1
        self.refresh()

    def _delete_selected(self):
        task = self._get_selected()
        if not task:
            return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(task.id)
            self._selected_idx = -1
            self.refresh()
