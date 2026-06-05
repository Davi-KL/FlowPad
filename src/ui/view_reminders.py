"""
ui/view_reminders.py
Visão de Lembretes — cards ordenados por proximidade com busca fuzzy e edição inline.
Vencidos aparecem em vermelho; próximos em verde.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from typing import Callable

import customtkinter as ctk

from core.storage import Storage, Entry
from ui.colors import COLORS as C
from utils.fuzzy import fuzzy_match

_OVERDUE  = ("#C0392B", "#FF7070")
_UPCOMING = ("#1D8A4C", "#5CE07A")


class RemindersView(ctk.CTkFrame):
    """Lembretes ordenados por proximidade — vencidos em vermelho no topo."""

    def __init__(self, master: tk.Widget, storage: Storage, on_new: Callable):
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self.storage = storage
        self.on_new = on_new
        self._reminders: list[Entry] = []
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
            header, text="⏰  Lembretes",
            font=("Consolas", 13, "bold"), text_color=C["danger"],
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
        all_r = self.storage.get_by_type("reminder")
        now = datetime.now()

        def sort_key(e: Entry) -> float:
            if not e.reminder_at: return float("inf")
            try:
                return (datetime.fromisoformat(e.reminder_at) - now).total_seconds()
            except ValueError:
                return float("inf")

        self._reminders = sorted(all_r, key=sort_key)
        self._apply_filter()

    def _apply_filter(self):
        q = self._search_text.strip()
        if q:
            self._filtered = [
                e for e in self._reminders
                if fuzzy_match(q, e.content)
            ]
        else:
            self._filtered = list(self._reminders)
        self._render()

    def _render(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        now = datetime.now()

        for entry in self._filtered:
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

        n = len(self._filtered)
        total = len(self._reminders)
        self.status_label.configure(
            text=f"{n} de {total} lembretes" if self._search_text else f"{total} lembretes"
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

        # Campo: texto do lembrete
        ctk.CTkLabel(
            row, text="Texto:", font=("Consolas", 9), text_color=C["text_dim"],
        ).pack(anchor="w", padx=8, pady=(8, 0))
        content_entry = ctk.CTkEntry(
            row, font=("Consolas", 10), height=30,
            fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], border_width=1,
        )
        content_entry.pack(fill="x", padx=8, pady=(2, 6))
        content_entry.insert(0, entry.content)
        content_entry.focus_set()

        # Campo: data/hora combinada
        current_dt = ""
        if entry.reminder_at:
            try:
                dt = datetime.fromisoformat(entry.reminder_at)
                current_dt = dt.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                pass

        ctk.CTkLabel(
            row, text="Data e hora  (DD/MM/AAAA HH:MM):",
            font=("Consolas", 9), text_color=C["text_dim"],
        ).pack(anchor="w", padx=8)
        dt_entry = ctk.CTkEntry(
            row, font=("Consolas", 10), height=30,
            fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], border_width=1,
            placeholder_text="ex: 25/12/2025 09:30",
        )
        dt_entry.pack(fill="x", padx=8, pady=(2, 6))
        if current_dt:
            dt_entry.insert(0, current_dt)

        btns = ctk.CTkFrame(row, fg_color=C["selected"], corner_radius=0)
        btns.pack(fill="x", padx=8, pady=(0, 8))

        def do_save():
            new_text = content_entry.get().strip()
            if not new_text:
                content_entry.focus_set()
                return
            new_dt_str = dt_entry.get().strip()
            new_reminder_at = _parse_datetime(new_dt_str)
            self.storage.update_entry(entry.id, content=new_text, reminder_at=new_reminder_at)
            eid = entry.id
            self.refresh()
            if eid in self._rows:
                self._select(eid)

        def do_cancel():
            eid = entry.id
            self.refresh()
            if eid in self._rows:
                self._select(eid)

        content_entry.bind("<Control-Return>", lambda e: do_save())
        content_entry.bind("<Escape>",         lambda e: do_cancel())
        dt_entry.bind("<Control-Return>",      lambda e: do_save())
        dt_entry.bind("<Escape>",              lambda e: do_cancel())

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


def _parse_datetime(value: str) -> str | None:
    """Converte 'DD/MM/AAAA HH:MM' ou 'DD/MM HH:MM' para ISO format."""
    value = value.strip()
    if not value:
        return None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m %H:%M"):
        try:
            if fmt == "%d/%m %H:%M":
                dt = datetime.strptime(f"{datetime.now().year}/{value}", f"%Y/{fmt[:-6]}%H:%M".replace("//", "/"))
                # reconstruct properly
                parts = value.split()
                day_month = parts[0]
                time_part = parts[1] if len(parts) > 1 else "00:00"
                day, month = day_month.split("/")
                h, m = time_part.split(":")
                dt = datetime(datetime.now().year, int(month), int(day), int(h), int(m))
            else:
                dt = datetime.strptime(value, fmt)
            return dt.isoformat()
        except (ValueError, IndexError):
            continue
    return None
