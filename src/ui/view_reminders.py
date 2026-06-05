"""
ui/view_reminders.py
Visão de Lembretes — cards ordenados por proximidade do horário agendado.
Vencidos aparecem em vermelho no topo.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from typing import Callable

from core.storage import Storage, Entry

COLORS = {
    "bg":       "#1A1A2E",
    "surface":  "#16213E",
    "accent":   "#E05C5C",
    "accent2":  "#F4C542",
    "text":     "#E8EAF0",
    "text_dim": "#8892A4",
    "selected": "#0F3460",
    "danger":   "#E05C5C",
    "overdue":  "#FF7070",
    "upcoming": "#5CE07A",
}


class RemindersView(tk.Frame):
    """Lembretes ordenados por proximidade — vencidos em vermelho no topo."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, bg=COLORS["bg"])
        self.storage = storage
        self.on_new = on_new
        self._reminders: list[Entry] = []
        self._selected_idx = -1

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=8)
        header.pack(fill="x")

        tk.Label(
            header, text="⏰  Lembretes",
            bg=COLORS["bg"], fg=COLORS["accent"],
            font=("Consolas", 11, "bold")
        ).pack(side="left")

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
            text="Selecione um lembrete para ver detalhes",
            bg=COLORS["surface"], fg=COLORS["text_dim"],
            font=("Consolas", 9), anchor="w", justify="left", wraplength=680,
        )
        self.detail_label.pack(fill="x")

        action_bar = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=6)
        action_bar.pack(fill="x")

        for label, bg, cmd in [
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
            widget.bind("<a>",      lambda e: self._archive_selected())
            widget.bind("<A>",      lambda e: self._archive_selected())
            widget.bind("<Delete>", lambda e: self._delete_selected())

    def refresh(self):
        all_reminders = self.storage.get_by_type("reminder")
        now = datetime.now()

        def sort_key(e: Entry) -> float:
            if not e.reminder_at:
                return float("inf")
            try:
                dt = datetime.fromisoformat(e.reminder_at)
                return (dt - now).total_seconds()
            except ValueError:
                return float("inf")

        self._reminders = sorted(all_reminders, key=sort_key)
        self._render()

    def _render(self):
        self.listbox.delete(0, "end")
        now = datetime.now()
        for entry in self._reminders:
            color = COLORS["text"]
            if entry.reminder_at:
                try:
                    dt = datetime.fromisoformat(entry.reminder_at)
                    ts = dt.strftime("%d/%m %H:%M")
                    if dt < now:
                        status = f"⚠ {ts} (vencido)"
                        color = COLORS["overdue"]
                    else:
                        status = f"🕐 {ts}"
                        color = COLORS["upcoming"]
                except ValueError:
                    status = "⚠ data inválida"
            else:
                status = "sem horário"
            line = entry.content[:60].replace("\n", " ")
            self.listbox.insert("end", f"  {status}  —  {line}")
            self.listbox.itemconfig("end", fg=color)
        self.status_label.config(text=f"{len(self._reminders)} lembretes")

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._selected_idx = sel[0]
        entry = self._reminders[self._selected_idx]
        detail = entry.content
        if entry.reminder_at:
            try:
                dt = datetime.fromisoformat(entry.reminder_at)
                detail += f"\n\n⏰ Agendado: {dt.strftime('%d/%m/%Y %H:%M')}"
            except ValueError:
                pass
        self.detail_label.config(text=detail, fg=COLORS["text"])

    def _get_selected(self) -> Entry | None:
        if 0 <= self._selected_idx < len(self._reminders):
            return self._reminders[self._selected_idx]
        return None

    def _archive_selected(self):
        entry = self._get_selected()
        if not entry:
            return
        self.storage.archive(entry.id)
        self._selected_idx = -1
        self.detail_label.config(
            text="Selecione um lembrete para ver detalhes",
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
                text="Selecione um lembrete para ver detalhes",
                fg=COLORS["text_dim"]
            )
            self.refresh()
