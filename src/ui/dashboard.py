"""
ui/dashboard.py
Dashboard principal — lista todas as entradas, permite busca, filtro e ações.
Navegação 100% possível pelo teclado.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from core.storage import Storage, Entry, ENTRY_TYPES
from utils.config import Config


COLORS = {
    "bg":        "#1A1A2E",
    "surface":   "#16213E",
    "surface2":  "#0F3460",
    "border":    "#1E4080",
    "accent":    "#5CE07A",
    "accent2":   "#F4C542",
    "text":      "#E8EAF0",
    "text_dim":  "#8892A4",
    "hover":     "#1E3A6E",
    "selected":  "#0F3460",
}


class DashboardWindow(tk.Toplevel):
    """
    Dashboard completo com:
    - Lista scrollável de entradas
    - Busca em tempo real
    - Filtro por tipo
    - Ações: copiar, arquivar, deletar
    - Atalhos de teclado para tudo
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

        self._entries: list[Entry] = []
        self._filtered: list[Entry] = []
        self._selected_idx: int = -1

        self._configure_window()
        self._build_ui()
        self._bind_keys()
        self._refresh()

    # ------------------------------------------------------------------
    # Configuração
    # ------------------------------------------------------------------

    def _configure_window(self):
        self.title("FlowPad — Dashboard")
        w = self.config.get("window", {}).get("dashboard_width", 800)
        h = self.config.get("window", {}).get("dashboard_height", 600)
        self.geometry(f"{w}x{h}")
        self.configure(bg=COLORS["bg"])
        self.minsize(600, 400)

        # Centraliza
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Cabeçalho ───────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["surface"], padx=16, pady=10)
        header.pack(fill="x")

        tk.Label(
            header, text="📋  FlowPad Dashboard",
            bg=COLORS["surface"], fg=COLORS["accent"],
            font=("Consolas", 13, "bold")
        ).pack(side="left")

        tk.Button(
            header, text="+ Nova Captura  [N]",
            bg=COLORS["accent"], fg=COLORS["bg"],
            relief="flat", bd=0, padx=10, pady=4,
            font=("Consolas", 9, "bold"), cursor="hand2",
            command=self.on_open_capture,
        ).pack(side="right")

        # ── Barra de busca + filtros ────────────────────────────────────
        toolbar = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=8)
        toolbar.pack(fill="x")

        # Busca
        search_frame = tk.Frame(toolbar, bg=COLORS["surface"])
        search_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            search_frame, text="🔍",
            bg=COLORS["surface"], fg=COLORS["text_dim"],
            font=("Consolas", 10)
        ).pack(side="left", padx=6)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search())
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat", bd=0,
            font=("Consolas", 10),
        )
        search_entry.pack(fill="x", ipady=6, padx=4)
        self.search_entry = search_entry

        # Filtro por tipo
        filter_frame = tk.Frame(toolbar, bg=COLORS["bg"])
        filter_frame.pack(side="right", padx=(12, 0))

        self.filter_var = tk.StringVar(value="all")
        all_btn = tk.Button(
            filter_frame, text="Todos",
            bg=COLORS["accent2"], fg=COLORS["bg"],
            relief="flat", bd=0, padx=8, pady=4,
            font=("Consolas", 8, "bold"), cursor="hand2",
            command=lambda: self._set_filter("all"),
        )
        all_btn.pack(side="left", padx=2)
        self._filter_buttons = {"all": all_btn}

        for key, meta in ENTRY_TYPES.items():
            btn = tk.Button(
                filter_frame,
                text=meta["label"],
                bg=COLORS["surface"], fg=COLORS["text_dim"],
                relief="flat", bd=0, padx=8, pady=4,
                font=("Consolas", 8), cursor="hand2",
                command=lambda k=key: self._set_filter(k),
            )
            btn.pack(side="left", padx=2)
            self._filter_buttons[key] = btn

        # ── Lista de entradas ────────────────────────────────────────────
        list_frame = tk.Frame(self, bg=COLORS["bg"])
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        scrollbar = tk.Scrollbar(list_frame, bg=COLORS["surface"])
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            bg=COLORS["surface"],
            fg=COLORS["text"],
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
        self.listbox.bind("<Double-Button-1>", lambda e: self._copy_selected())

        # ── Painel de detalhe ────────────────────────────────────────────
        detail_frame = tk.Frame(self, bg=COLORS["surface"], padx=16, pady=10)
        detail_frame.pack(fill="x")

        self.detail_label = tk.Label(
            detail_frame,
            text="Selecione uma entrada para ver o conteúdo",
            bg=COLORS["surface"], fg=COLORS["text_dim"],
            font=("Consolas", 9), anchor="w", justify="left", wraplength=700,
        )
        self.detail_label.pack(fill="x")

        # ── Rodapé: ações ───────────────────────────────────────────────
        action_bar = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=8)
        action_bar.pack(fill="x")

        actions = [
            ("📋 Copiar  [C]",   COLORS["accent"],   self._copy_selected),
            ("🗂 Arquivar  [A]", COLORS["accent2"],  self._archive_selected),
            ("🗑 Deletar  [Del]", COLORS["reminder"], self._delete_selected),
        ]
        for label, color, cmd in actions:
            tk.Button(
                action_bar, text=label,
                bg=color, fg=COLORS["bg"],
                relief="flat", bd=0, padx=10, pady=5,
                font=("Consolas", 9, "bold"), cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=4)

        self.status_label = tk.Label(
            action_bar, text="",
            bg=COLORS["bg"], fg=COLORS["text_dim"],
            font=("Consolas", 8)
        )
        self.status_label.pack(side="right")

    # ------------------------------------------------------------------
    # Lógica de lista
    # ------------------------------------------------------------------

    def _refresh(self):
        """Recarrega entradas do storage e aplica filtro/busca atual."""
        self._entries = self.storage.get_all()
        self._apply_filter()

    def _apply_filter(self):
        ftype = self.filter_var.get()
        query = self.search_var.get().strip()

        filtered = self._entries
        if ftype != "all":
            filtered = [e for e in filtered if e.entry_type == ftype]
        if query:
            q = query.lower()
            filtered = [
                e for e in filtered
                if q in e.content.lower() or q in e.title.lower()
            ]

        self._filtered = filtered
        self._render_list()

    def _render_list(self):
        self.listbox.delete(0, "end")
        for entry in self._filtered:
            meta = ENTRY_TYPES.get(entry.entry_type, {})
            icon = meta.get("label", "")[:2]
            title = entry.title or entry.content[:60].replace("\n", " ")
            ts = entry.created_at[:16].replace("T", " ")
            self.listbox.insert("end", f"  {icon}  {title}  —  {ts}")

        self.status_label.config(text=f"{len(self._filtered)} entradas")

    def _on_search(self):
        self._apply_filter()

    def _set_filter(self, ftype: str):
        self.filter_var.set(ftype)
        # Destaca botão ativo
        for key, btn in self._filter_buttons.items():
            if key == ftype:
                color = ENTRY_TYPES[key]["color"] if key != "all" else COLORS["accent2"]
                btn.config(bg=color, fg=COLORS["bg"])
            else:
                btn.config(bg=COLORS["surface"], fg=COLORS["text_dim"])
        self._apply_filter()

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._selected_idx = sel[0]
        if self._selected_idx < len(self._filtered):
            entry = self._filtered[self._selected_idx]
            self.detail_label.config(
                text=entry.content[:400],
                fg=COLORS["text"],
            )

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _get_selected_entry(self) -> Entry | None:
        if self._selected_idx < 0 or self._selected_idx >= len(self._filtered):
            return None
        return self._filtered[self._selected_idx]

    def _copy_selected(self):
        entry = self._get_selected_entry()
        if not entry:
            return
        self.clipboard_clear()
        self.clipboard_append(entry.content)
        self.status_label.config(text="✓ Copiado para a área de transferência!")
        self.after(2000, lambda: self.status_label.config(text=f"{len(self._filtered)} entradas"))

    def _archive_selected(self):
        entry = self._get_selected_entry()
        if not entry:
            return
        self.storage.archive(entry.id)
        self._selected_idx = -1
        self.detail_label.config(text="Selecione uma entrada para ver o conteúdo", fg=COLORS["text_dim"])
        self._refresh()

    def _delete_selected(self):
        entry = self._get_selected_entry()
        if not entry:
            return
        if messagebox.askyesno("Deletar", "Tem certeza? Esta ação é permanente."):
            self.storage.delete(entry.id)
            self._selected_idx = -1
            self.detail_label.config(text="Selecione uma entrada para ver o conteúdo", fg=COLORS["text_dim"])
            self._refresh()

    # ------------------------------------------------------------------
    # Atalhos de teclado
    # ------------------------------------------------------------------

    def _bind_keys(self):
        self.bind("<n>", lambda e: self.on_open_capture())
        self.bind("<N>", lambda e: self.on_open_capture())
        self.bind("<c>", lambda e: self._copy_selected())
        self.bind("<C>", lambda e: self._copy_selected())
        self.bind("<a>", lambda e: self._archive_selected())
        self.bind("<A>", lambda e: self._archive_selected())
        self.bind("<Delete>", lambda e: self._delete_selected())
        self.bind("<F5>", lambda e: self._refresh())
        self.bind("<Control-f>", lambda e: self.search_entry.focus_set())

        # Navegar lista com setas quando o foco está na lista
        self.listbox.bind("<Up>", self._on_list_nav)
        self.listbox.bind("<Down>", self._on_list_nav)

    def _on_list_nav(self, event):
        """Atualiza painel de detalhe ao navegar com teclado."""
        self.after(10, self._on_select)
