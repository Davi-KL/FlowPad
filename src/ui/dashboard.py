"""
ui/dashboard.py
Dashboard principal — navegação por abas entre as 5 visões de tipo.
Cada aba contém uma visão especializada (tasks, insights, clipboard, reminders, notes).
"""

import tkinter as tk
from typing import Callable

from core.storage import Storage
from utils.config import Config
from ui.view_tasks import TasksView
from ui.view_insights import InsightsView
from ui.view_clipboard import ClipboardView
from ui.view_reminders import RemindersView
from ui.view_notes import NotesView


COLORS = {
    "bg":       "#1A1A2E",
    "surface":  "#16213E",
    "tab_bar":  "#0D1B33",
    "tab_on":   "#0F3460",
    "text":     "#E8EAF0",
    "text_dim": "#8892A4",
    "accent":   "#5CE07A",
}

TABS: list[tuple[str, str, str, str]] = [
    ("💡", "Insights",  "insight",   "#F4C542"),
    ("⏰", "Lembretes", "reminder",  "#E05C5C"),
    ("📋", "Clipboard", "clipboard", "#5CB8E0"),
    ("✅", "Tarefas",   "task",      "#5CE07A"),
    ("📝", "Notas",     "note",      "#A07AE0"),
]


class DashboardWindow(tk.Toplevel):
    """
    Dashboard com 5 abas, uma por tipo de entrada.
    Cada aba carrega sua visão especializada.
    """

    def __init__(
        self,
        master: tk.Tk,
        storage: Storage,
        config: Config,
        on_open_capture: Callable,
    ):
        super().__init__(master)
        self.storage = storage
        self.config = config
        self.on_open_capture = on_open_capture
        self._active_tab = "insight"
        self._views: dict[str, tk.Frame] = {}
        self._tab_buttons: dict[str, tk.Button] = {}

        self._configure_window()
        self._build_ui()
        self._switch_tab("insight")

    def _configure_window(self):
        self.title("FlowPad — Dashboard")
        w = self.config.get("window", {}).get("dashboard_width", 860)
        h = self.config.get("window", {}).get("dashboard_height", 600)
        self.geometry(f"{w}x{h}")
        self.configure(bg=COLORS["bg"])
        self.minsize(700, 450)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["surface"], padx=16, pady=8)
        header.pack(fill="x")

        tk.Label(
            header, text="FlowPad",
            bg=COLORS["surface"], fg=COLORS["accent"],
            font=("Consolas", 13, "bold")
        ).pack(side="left")

        tk.Button(
            header, text="+ Nova  [N]",
            bg=COLORS["accent"], fg=COLORS["bg"],
            relief="flat", bd=0, padx=10, pady=4,
            font=("Consolas", 9, "bold"), cursor="hand2",
            command=self._new_for_active_tab,
        ).pack(side="right")

        # ── Tab bar ───────────────────────────────────────────────────────
        tab_bar = tk.Frame(self, bg=COLORS["tab_bar"], padx=4, pady=0)
        tab_bar.pack(fill="x")

        for icon, label, key, color in TABS:
            btn = tk.Button(
                tab_bar, text=f"{icon} {label}",
                bg=COLORS["tab_bar"], fg=COLORS["text_dim"],
                relief="flat", bd=0, padx=14, pady=8,
                font=("Consolas", 9), cursor="hand2",
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left")
            self._tab_buttons[key] = btn

        # ── Content frame ─────────────────────────────────────────────────
        self.content_frame = tk.Frame(self, bg=COLORS["bg"])
        self.content_frame.pack(fill="both", expand=True)

        self._views["insight"] = InsightsView(
            self.content_frame, storage=self.storage,
            on_new=lambda: self.on_open_capture("insight"),
        )
        self._views["reminder"] = RemindersView(
            self.content_frame, storage=self.storage,
            on_new=lambda: self.on_open_capture("reminder"),
        )
        self._views["clipboard"] = ClipboardView(
            self.content_frame, storage=self.storage,
            on_new=lambda: self.on_open_capture("clipboard"),
        )
        self._views["task"] = TasksView(
            self.content_frame, storage=self.storage,
            on_new=lambda: self.on_open_capture("task"),
        )
        self._views["note"] = NotesView(
            self.content_frame, storage=self.storage,
            on_new=lambda: self.on_open_capture("note"),
        )

        # ── Key bindings ──────────────────────────────────────────────────
        self.bind("<n>", lambda e: self._new_for_active_tab())
        self.bind("<N>", lambda e: self._new_for_active_tab())
        self.bind("<F5>", lambda e: self._refresh_active())
        for i, (_, _, key, _) in enumerate(TABS, start=1):
            self.bind(f"<Control-Key-{i}>", lambda e, k=key: self._switch_tab(k))

    def _switch_tab(self, key: str):
        self._active_tab = key
        tab_color = next(c for _, _, k, c in TABS if k == key)

        for k, btn in self._tab_buttons.items():
            if k == key:
                btn.config(
                    bg=COLORS["tab_on"], fg=tab_color,
                    font=("Consolas", 9, "bold"),
                )
            else:
                btn.config(
                    bg=COLORS["tab_bar"], fg=COLORS["text_dim"],
                    font=("Consolas", 9),
                )

        for k, view in self._views.items():
            if k == key:
                view.pack(fill="both", expand=True)
                view.refresh()
            else:
                view.pack_forget()

    def _new_for_active_tab(self):
        self.on_open_capture(self._active_tab)

    def _refresh_active(self):
        view = self._views.get(self._active_tab)
        if view:
            view.refresh()
