"""
ui/view_reminders.py
Visão de Lembretes — cards ordenados por proximidade do horário.
Vencidos aparecem em vermelho; próximos em verde.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from typing import Callable

import customtkinter as ctk

from core.storage import Storage, Entry
from ui.colors import COLORS as C

_OVERDUE  = ("#C0392B", "#FF7070")
_UPCOMING = ("#1D8A4C", "#5CE07A")


class RemindersView(ctk.CTkFrame):
    """Lembretes ordenados por proximidade — vencidos em vermelho no topo."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self.storage = storage
        self.on_new = on_new
        self._reminders: list[Entry] = []
        self._selected_id: str | None = None
        self._rows: dict[str, ctk.CTkFrame] = {}

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        header.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            header, text="⏰  Lembretes",
            font=("Consolas", 13, "bold"), text_color=C["danger"],
        ).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=C["surface"], corner_radius=8,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["danger"],
        )
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        detail_frame = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=8)
        detail_frame.pack(fill="x", padx=12, pady=(0, 4))
        self.detail_label = ctk.CTkLabel(
            detail_frame,
            text="Selecione um lembrete para ver detalhes",
            font=("Consolas", 10), text_color=C["text_dim"],
            anchor="w", justify="left", wraplength=660,
        )
        self.detail_label.pack(fill="x", padx=12, pady=10)

        action_bar = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        action_bar.pack(fill="x", padx=12, pady=(0, 8))

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

        self.bind("<a>", lambda e: self._archive_selected())
        self.bind("<A>", lambda e: self._archive_selected())
        self.bind("<Delete>", lambda e: self._delete_selected())

    def refresh(self):
        all_r = self.storage.get_by_type("reminder")
        now = datetime.now()

        def sort_key(e: Entry) -> float:
            if not e.reminder_at: return float("inf")
            try:
                return (datetime.fromisoformat(e.reminder_at) - now).total_seconds()
            except ValueError:
                return float("inf")

        self._reminders = sorted(all_r, key=sort_key)
        self._render()

    def _render(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        now = datetime.now()

        for entry in self._reminders:
            status = "sem horário"
            text_color = C["text_dim"]
            if entry.reminder_at:
                try:
                    dt = datetime.fromisoformat(entry.reminder_at)
                    ts = dt.strftime("%d/%m %H:%M")
                    if dt < now:
                        status = f"⚠ {ts} (vencido)"
                        text_color = _OVERDUE
                    else:
                        status = f"🕐 {ts}"
                        text_color = _UPCOMING
                except ValueError:
                    status = "⚠ data inválida"

            line = entry.content[:60].replace("\n", " ")
            row = ctk.CTkFrame(self.scroll, fg_color=C["row"], corner_radius=6, cursor="hand2")
            row.pack(fill="x", padx=4, pady=2)

            ctk.CTkLabel(
                row, text=status,
                anchor="w", text_color=text_color, font=("Consolas", 10, "bold"),
                width=160,
            ).pack(side="left", padx=(10, 4), pady=8)

            ctk.CTkLabel(
                row, text=f"—  {line}",
                anchor="w", text_color=C["text"], font=("Consolas", 10),
            ).pack(side="left", fill="x", expand=True, padx=4, pady=8)

            handler = lambda e, eid=entry.id: self._select(eid)
            row.bind("<Button-1>", handler)
            for child in row.winfo_children():
                child.bind("<Button-1>", handler)

            self._rows[entry.id] = row

        self.status_label.configure(text=f"{len(self._reminders)} lembretes")

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

        entry = next((e for e in self._reminders if e.id == entry_id), None)
        if entry:
            detail = entry.content
            if entry.reminder_at:
                try:
                    dt = datetime.fromisoformat(entry.reminder_at)
                    detail += f"\n\n⏰ Agendado: {dt.strftime('%d/%m/%Y %H:%M')}"
                except ValueError:
                    pass
            self.detail_label.configure(text=detail, text_color=C["text"])
        self.focus_set()

    def _get_selected(self) -> Entry | None:
        if not self._selected_id: return None
        return next((e for e in self._reminders if e.id == self._selected_id), None)

    def _archive_selected(self):
        entry = self._get_selected()
        if not entry: return
        self.storage.archive(entry.id)
        self._selected_id = None
        self.detail_label.configure(
            text="Selecione um lembrete para ver detalhes", text_color=C["text_dim"],
        )
        self.refresh()

    def _delete_selected(self):
        entry = self._get_selected()
        if not entry: return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(entry.id)
            self._selected_id = None
            self.detail_label.configure(
                text="Selecione um lembrete para ver detalhes", text_color=C["text_dim"],
            )
            self.refresh()
