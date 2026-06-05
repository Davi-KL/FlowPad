"""
ui/dashboard.py
Dashboard principal — navegação por abas entre as 5 visões de tipo.
Inclui seletor de tema Dark/Light no cabeçalho.
"""

import tkinter as tk
from typing import Callable

import customtkinter as ctk

from core.storage import Storage
from utils.config import Config
from ui.view_tasks import TasksView
from ui.view_insights import InsightsView
from ui.view_clipboard import ClipboardView
from ui.view_reminders import RemindersView
from ui.view_notes import NotesView
from ui.colors import COLORS as C


TABS: list[tuple[str, str, str, tuple]] = [
    ("💡", "Insights",  "insight",   ("#9A7000", "#F4C542")),
    ("⏰", "Lembretes", "reminder",  ("#C0392B", "#E05C5C")),
    ("📋", "Clipboard", "clipboard", ("#1A6B8A", "#5CB8E0")),
    ("✅", "Tarefas",   "task",      ("#1D8A4C", "#5CE07A")),
    ("📝", "Notas",     "note",      ("#6B3FA0", "#A07AE0")),
]


class DashboardWindow(ctk.CTkToplevel):
    """
    Dashboard com 5 abas especializadas e alternador de tema Dark/Light.
    """

    def __init__(
        self,
        master: ctk.CTk,
        storage: Storage,
        config: Config,
        on_open_capture: Callable,
    ):
        super().__init__(master)
        self.storage = storage
        self.config = config
        self.on_open_capture = on_open_capture
        self._active_tab = "insight"
        self._views: dict[str, ctk.CTkFrame] = {}
        self._tab_buttons: dict[str, ctk.CTkButton] = {}

        self._configure_window()
        self._build_ui()
        self._switch_tab("insight")

    def _configure_window(self):
        self.title("FlowPad — Dashboard")
        w = self.config.get("window", {}).get("dashboard_width", 900)
        h = self.config.get("window", {}).get("dashboard_height", 620)
        self.geometry(f"{w}x{h}")
        self.configure(fg_color=C["bg"])
        self.minsize(700, 480)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="FlowPad",
            font=("Consolas", 14, "bold"), text_color=C["accent"],
        ).pack(side="left", padx=16)

        # Theme toggle
        self._theme_var = ctk.StringVar(
            value=self.config.get("theme", "dark").capitalize()
        )
        ctk.CTkSegmentedButton(
            header,
            values=["Dark", "Light"],
            variable=self._theme_var,
            command=self._on_theme_change,
            font=("Consolas", 10),
            width=130, height=28,
        ).pack(side="right", padx=16)

        ctk.CTkButton(
            header, text="+ Nova  [N]", command=self._new_for_active_tab,
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color=C["bg"], font=("Consolas", 11, "bold"),
            width=110, height=32, corner_radius=6,
        ).pack(side="right", padx=(0, 8))

        # ── Tab bar ───────────────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(self, fg_color=C["row"], corner_radius=0, height=44)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        for icon, label, key, color in TABS:
            btn = ctk.CTkButton(
                tab_bar, text=f"{icon} {label}",
                fg_color="transparent", hover_color=C["border"],
                text_color=C["text_dim"], font=("Consolas", 10),
                corner_radius=0, width=110, height=44,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left")
            self._tab_buttons[key] = btn

        # ── Content area ──────────────────────────────────────────────────
        self.content_frame = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
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
                btn.configure(
                    fg_color=C["selected"], text_color=tab_color,
                    font=("Consolas", 10, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent", text_color=C["text_dim"],
                    font=("Consolas", 10),
                )

        for k, view in self._views.items():
            if k == key:
                view.pack(fill="both", expand=True)
                view.refresh()
            else:
                view.pack_forget()

    def _on_theme_change(self, value: str):
        mode = value.lower()
        ctk.set_appearance_mode(mode)
        self.config.set("theme", mode)

    def _new_for_active_tab(self):
        self.on_open_capture(self._active_tab)

    def _refresh_active(self):
        view = self._views.get(self._active_tab)
        if view:
            view.refresh()
