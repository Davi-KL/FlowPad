"""
ui/dashboard.py
Dashboard principal — menu de 5 cards por tipo com navegação por teclado.

Fluxo:
  - Menu principal: 5 cards estilizados por tipo de entrada.
  - ↑↓ navega entre cards; Enter ou letra-atalho abre a visão do tipo.
  - Dentro da visão: Esc volta ao menu principal.
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
from ui.colors import COLORS as C, TYPE_COLORS


# (icon, label, storage_key, shortcut_key)
MENU_ITEMS = [
    ("💡", "Insights",  "insight",   "I"),
    ("⏰", "Lembretes", "reminder",  "L"),
    ("📋", "Clipboard", "clipboard", "C"),
    ("✅", "Tarefas",   "task",      "T"),
    ("📝", "Notas",     "note",      "N"),
]

VIEW_CLASSES = {
    "insight":   InsightsView,
    "reminder":  RemindersView,
    "clipboard": ClipboardView,
    "task":      TasksView,
    "note":      NotesView,
}


class DashboardWindow(ctk.CTkToplevel):
    """
    Dashboard com menu principal de cards e navegação por teclado.
    Esc dentro de qualquer visão retorna ao menu.
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

        self._state = "menu"          # "menu" | "view"
        self._selected_idx = 0        # card destacado no menu
        self._active_key: str | None = None
        self._views: dict[str, ctk.CTkFrame] = {}
        self._cards: list[ctk.CTkFrame] = []
        self._count_labels: dict[str, ctk.CTkLabel] = {}

        self._configure_window()
        self._build_ui()
        self._show_menu()

    # ------------------------------------------------------------------
    # Janela
    # ------------------------------------------------------------------

    def _configure_window(self):
        self.title("FlowPad")
        self.geometry("660x520")
        self.configure(fg_color=C["bg"])
        self.minsize(560, 420)
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw - 660) // 2}+{(sh - 520) // 2}")

    # ------------------------------------------------------------------
    # Construção da UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Menu frame ────────────────────────────────────────────────
        self.menu_frame = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)

        # Header do menu
        menu_header = ctk.CTkFrame(self.menu_frame, fg_color=C["surface"], corner_radius=0, height=54)
        menu_header.pack(fill="x")
        menu_header.pack_propagate(False)

        ctk.CTkLabel(
            menu_header, text="FlowPad",
            font=("Consolas", 15, "bold"), text_color=C["accent"],
        ).pack(side="left", padx=20)

        # Toggle de tema
        self._theme_var = ctk.StringVar(value=self.config.get("theme", "dark").capitalize())
        ctk.CTkSegmentedButton(
            menu_header, values=["Dark", "Light"],
            variable=self._theme_var,
            command=self._on_theme_change,
            font=("Consolas", 10), width=130, height=28,
        ).pack(side="right", padx=16)

        # Cards
        cards_area = ctk.CTkFrame(self.menu_frame, fg_color=C["bg"], corner_radius=0)
        cards_area.pack(fill="both", expand=True, padx=48, pady=20)

        self._cards.clear()
        self._count_labels.clear()

        for i, (icon, label, key, shortcut) in enumerate(MENU_ITEMS):
            color = TYPE_COLORS[key]
            card = self._build_card(cards_area, icon, label, key, color, shortcut)
            card.pack(fill="x", pady=5)
            self._cards.append(card)

        # Hint de navegação
        ctk.CTkLabel(
            self.menu_frame,
            text="↑↓ navegar  •  Enter abrir  •  I L C T N atalhos diretos",
            font=("Consolas", 9), text_color=C["text_dim"],
        ).pack(pady=(0, 16))

        # ── View frame ────────────────────────────────────────────────
        self.view_frame = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)

        # Header da visão (← Voltar + título + Nova)
        view_header = ctk.CTkFrame(self.view_frame, fg_color=C["surface"], corner_radius=0, height=54)
        view_header.pack(fill="x")
        view_header.pack_propagate(False)

        ctk.CTkButton(
            view_header, text="← Voltar  [Esc]",
            command=self._show_menu,
            fg_color="transparent", hover_color=C["border"],
            text_color=C["text_dim"], font=("Consolas", 10),
            width=130, height=34, corner_radius=6,
        ).pack(side="left", padx=12)

        self.view_title_label = ctk.CTkLabel(
            view_header, text="",
            font=("Consolas", 13, "bold"), text_color=C["accent"],
        )
        self.view_title_label.pack(side="left", padx=8)

        ctk.CTkButton(
            view_header, text="+ Nova  [N]",
            command=self._new_in_active_view,
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color=C["bg"], font=("Consolas", 11, "bold"),
            width=110, height=34, corner_radius=6,
        ).pack(side="right", padx=16)

        # Área de conteúdo das visões
        self.view_content = ctk.CTkFrame(self.view_frame, fg_color=C["bg"], corner_radius=0)
        self.view_content.pack(fill="both", expand=True)

        for _, _, key, _ in MENU_ITEMS:
            view = VIEW_CLASSES[key](
                self.view_content,
                storage=self.storage,
                on_new=lambda k=key: self.on_open_capture(k),
            )
            self._views[key] = view

    def _build_card(
        self,
        parent: ctk.CTkFrame,
        icon: str,
        label: str,
        key: str,
        color: tuple,
        shortcut: str,
    ) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=C["surface"], corner_radius=10, height=68)
        card.pack_propagate(False)

        # Barra colorida à esquerda
        accent_bar = ctk.CTkFrame(card, fg_color=color, corner_radius=6, width=7)
        accent_bar.pack(side="left", fill="y", padx=(12, 14), pady=10)
        accent_bar.pack_propagate(False)
        accent_bar.is_accent = True  # marca para não sobrescrever na seleção

        # Ícone + nome
        ctk.CTkLabel(
            card, text=f"{icon}  {label}",
            font=("Consolas", 14, "bold"), text_color=color,
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        # Contagem
        count_lbl = ctk.CTkLabel(
            card, text="",
            font=("Consolas", 10), text_color=C["text_dim"],
        )
        count_lbl.pack(side="left")
        self._count_labels[key] = count_lbl

        # Atalho + seta
        ctk.CTkLabel(
            card, text=f"[{shortcut}]  →",
            font=("Consolas", 11, "bold"), text_color=C["text_dim"],
        ).pack(side="right", padx=20)

        # Click em qualquer parte do card
        handler = lambda e, k=key: self._open_view(k)
        for w in [card] + list(card.winfo_children()):
            if not getattr(w, "is_accent", False):
                w.bind("<Button-1>", handler)

        return card

    # ------------------------------------------------------------------
    # Navegação de estado
    # ------------------------------------------------------------------

    def _show_menu(self):
        self._state = "menu"

        # Esconde visão ativa
        if self._active_key:
            self._views[self._active_key].pack_forget()
            self._active_key = None

        self.view_frame.pack_forget()
        self.menu_frame.pack(fill="both", expand=True)

        self._refresh_counts()
        self._highlight(self._selected_idx)
        self._bind_menu_keys()

    def _open_view(self, key: str):
        self._state = "view"
        self._active_key = key

        # Atualiza título do header
        item = next(x for x in MENU_ITEMS if x[2] == key)
        icon, label, _, _ = item
        color = TYPE_COLORS[key]
        self.view_title_label.configure(text=f"{icon}  {label}", text_color=color)

        self.menu_frame.pack_forget()
        self.view_frame.pack(fill="both", expand=True)

        view = self._views[key]
        view.pack(fill="both", expand=True)
        view.refresh()
        view.select_first()

        self._bind_view_keys()

    # ------------------------------------------------------------------
    # Counts e highlight
    # ------------------------------------------------------------------

    def _refresh_counts(self):
        for _, _, key, _ in MENU_ITEMS:
            n = len(self.storage.get_by_type(key))
            lbl = self._count_labels.get(key)
            if lbl:
                lbl.configure(text=f"{n} entradas")

    def _highlight(self, idx: int):
        for i, card in enumerate(self._cards):
            is_sel = (i == idx)
            new_color = C["selected"] if is_sel else C["surface"]
            card.configure(fg_color=new_color)
            for child in card.winfo_children():
                if not getattr(child, "is_accent", False):
                    try:
                        child.configure(fg_color=new_color)
                    except Exception:
                        pass

    # ------------------------------------------------------------------
    # Key bindings
    # ------------------------------------------------------------------

    def _bind_menu_keys(self):
        # Limpa bindings exclusivos de visão
        for key in ("<space>", "<a>", "<A>", "<Delete>", "<Key-1>", "<Key-2>", "<Key-3>"):
            self.unbind(key)

        self.bind("<Up>",     self._on_up)
        self.bind("<Down>",   self._on_down)
        self.bind("<Return>", self._on_enter_menu)
        self.bind("<Escape>", lambda e: self.destroy())

        for _, _, key, shortcut in MENU_ITEMS:
            self.bind(shortcut.lower(), lambda e, k=key: self._open_view(k))
            self.bind(shortcut.upper(), lambda e, k=key: self._open_view(k))

    def _bind_view_keys(self):
        # Remove atalhos de menu; rebinda teclas de ação para a visão ativa
        for _, _, _, shortcut in MENU_ITEMS:
            self.unbind(shortcut.lower())
            self.unbind(shortcut.upper())

        self.bind("<Escape>", lambda e: self._show_menu())
        self.bind("<F5>",     lambda e: self._refresh_active())
        self.bind("<n>",      lambda e: self._new_in_active_view())
        self.bind("<N>",      lambda e: self._new_in_active_view())
        self.bind("<Up>",     lambda e: self._view_nav(-1))
        self.bind("<Down>",   lambda e: self._view_nav(1))
        self.bind("<Return>", lambda e: self._view_enter())
        self.bind("<space>",  lambda e: self._view_space())
        self.bind("<c>",      lambda e: self._view_copy())
        self.bind("<C>",      lambda e: self._view_copy())
        self.bind("<a>",      lambda e: self._view_archive())
        self.bind("<A>",      lambda e: self._view_archive())
        self.bind("<Delete>", lambda e: self._view_delete())
        self.bind("<Key-1>",  lambda e: self._view_filter(1))
        self.bind("<Key-2>",  lambda e: self._view_filter(2))
        self.bind("<Key-3>",  lambda e: self._view_filter(3))

    def _on_up(self, event):
        self._selected_idx = (self._selected_idx - 1) % len(MENU_ITEMS)
        self._highlight(self._selected_idx)

    def _on_down(self, event):
        self._selected_idx = (self._selected_idx + 1) % len(MENU_ITEMS)
        self._highlight(self._selected_idx)

    def _on_enter_menu(self, event):
        self._open_view(MENU_ITEMS[self._selected_idx][2])

    # ------------------------------------------------------------------
    # Delegação de ações para a visão ativa
    # ------------------------------------------------------------------

    def _view_nav(self, direction: int):
        if self._active_key:
            self._views[self._active_key]._nav(direction)

    def _view_enter(self):
        key = self._active_key
        if not key:
            return
        view = self._views[key]
        if key == "task":
            view._toggle_selected()
        elif hasattr(view, "_copy_selected"):
            view._copy_selected()

    def _view_space(self):
        if self._active_key == "task":
            self._views["task"]._toggle_selected()

    def _view_copy(self):
        key = self._active_key
        if key and hasattr(self._views[key], "_copy_selected"):
            self._views[key]._copy_selected()

    def _view_archive(self):
        key = self._active_key
        if key and hasattr(self._views[key], "_archive_selected"):
            self._views[key]._archive_selected()

    def _view_delete(self):
        key = self._active_key
        if key and hasattr(self._views[key], "_delete_selected"):
            self._views[key]._delete_selected()

    def _view_filter(self, n: int):
        if self._active_key == "task":
            filter_map = {1: "all", 2: "pending", 3: "completed"}
            self._views["task"]._set_filter(filter_map[n])

    def _new_in_active_view(self):
        if self._active_key:
            self.on_open_capture(self._active_key)

    def _refresh_active(self):
        if self._active_key:
            self._views[self._active_key].refresh()

    def _on_theme_change(self, value: str):
        ctk.set_appearance_mode(value.lower())
        self.config.set("theme", value.lower())
