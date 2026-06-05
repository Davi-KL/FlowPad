"""
ui/quick_capture.py
Janela de captura rápida — o coração do FlowPad.
Abre instantaneamente, permite navegar 100% pelo teclado e fecha sozinha após salvar.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

from core.storage import Storage, Entry, ENTRY_TYPES
from utils.config import Config


# ──────────────────────────────────────────────
# Paleta de cores (Dark Theme)
# ──────────────────────────────────────────────
COLORS = {
    "bg":          "#1A1A2E",
    "surface":     "#16213E",
    "border":      "#0F3460",
    "accent":      "#5CE07A",
    "accent2":     "#F4C542",
    "text":        "#E8EAF0",
    "text_dim":    "#8892A4",
    "insight":     "#F4C542",
    "reminder":    "#E05C5C",
    "clipboard":   "#5CB8E0",
    "task":        "#5CE07A",
    "note":        "#A07AE0",
}

TYPE_KEYS = list(ENTRY_TYPES.keys())  # ["insight", "reminder", "clipboard", "task", "note"]


class QuickCaptureWindow(tk.Toplevel):
    """
    Janela popup de captura rápida.
    Atalhos internos:
      Tab / Shift+Tab  — navega entre campos
      Ctrl+1..5        — muda o tipo de entrada
      Ctrl+Enter       — salva
      Escape           — fecha sem salvar
    """

    def __init__(
        self,
        master: tk.Tk,
        storage: Storage,
        config: Config,
        default_type: str = "insight",
    ):
        super().__init__(master)
        self.storage = storage
        self.config = config
        self.selected_type = tk.StringVar(value=default_type)

        self._configure_window()
        self._build_ui()
        self._bind_keys()
        self._center_on_screen()

        self.content_text.focus_set()

    # ------------------------------------------------------------------
    # Configuração da janela
    # ------------------------------------------------------------------

    def _configure_window(self):
        self.title("FlowPad — Captura Rápida")
        w = self.config.get("window", {}).get("capture_width", 480)
        h = self.config.get("window", {}).get("capture_height", 320)
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.attributes("-topmost", True)  # Sempre à frente
        self.overrideredirect(False)

    def _center_on_screen(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (sw - w) // 2
        y = (sh - h) // 3  # Levemente acima do centro
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["surface"], pady=8, padx=12)
        header.pack(fill="x")

        tk.Label(
            header, text="✏️  FlowPad", bg=COLORS["surface"],
            fg=COLORS["accent"], font=("Consolas", 11, "bold")
        ).pack(side="left")

        hint = tk.Label(
            header, text="Ctrl+Enter salva  •  Esc fecha",
            bg=COLORS["surface"], fg=COLORS["text_dim"], font=("Consolas", 8)
        )
        hint.pack(side="right")

        # ── Seletor de tipo (botões de tecla) ────────────────────────────
        type_frame = tk.Frame(self, bg=COLORS["bg"], pady=6, padx=12)
        type_frame.pack(fill="x")

        tk.Label(
            type_frame, text="Tipo:", bg=COLORS["bg"],
            fg=COLORS["text_dim"], font=("Consolas", 9)
        ).pack(side="left", padx=(0, 8))

        self._type_buttons: dict[str, tk.Button] = {}
        for i, (key, meta) in enumerate(ENTRY_TYPES.items(), start=1):
            btn = tk.Button(
                type_frame,
                text=f"{meta['label']} [{i}]",
                bg=COLORS["surface"],
                fg=COLORS["text_dim"],
                activebackground=meta["color"],
                relief="flat",
                bd=0,
                padx=8, pady=4,
                font=("Consolas", 8),
                cursor="hand2",
                command=lambda k=key: self._select_type(k),
            )
            btn.pack(side="left", padx=2)
            self._type_buttons[key] = btn

        self._select_type(self.selected_type.get())

        # ── Campo título (opcional) ──────────────────────────────────────
        title_frame = tk.Frame(self, bg=COLORS["bg"], padx=12)
        title_frame.pack(fill="x", pady=(4, 0))

        self.title_entry = tk.Entry(
            title_frame,
            bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat", bd=0,
            font=("Consolas", 10),
        )
        self.title_entry.insert(0, "")
        self.title_entry.pack(fill="x", ipady=6, padx=1)
        self._placeholder(self.title_entry, "Título (opcional)...")

        tk.Frame(title_frame, bg=COLORS["border"], height=1).pack(fill="x")

        # ── Campo conteúdo (principal) ───────────────────────────────────
        content_frame = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=4)
        content_frame.pack(fill="both", expand=True)

        self.content_text = tk.Text(
            content_frame,
            bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat", bd=0,
            font=("Consolas", 10),
            wrap="word",
            height=5,
        )
        self.content_text.pack(fill="both", expand=True, ipady=6, padx=1)

        scrollbar = tk.Scrollbar(content_frame, command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=scrollbar.set)

        tk.Frame(content_frame, bg=COLORS["border"], height=1).pack(fill="x")

        # ── Rodapé: lembrete + botões ────────────────────────────────────
        footer = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=8)
        footer.pack(fill="x")

        # Opção de lembrete (só aparece para tipo "reminder")
        self.reminder_frame = tk.Frame(footer, bg=COLORS["bg"])
        tk.Label(
            self.reminder_frame, text="⏰ Em quantos min?",
            bg=COLORS["bg"], fg=COLORS["text_dim"], font=("Consolas", 8)
        ).pack(side="left")
        self.reminder_minutes = tk.Entry(
            self.reminder_frame, width=5,
            bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat", font=("Consolas", 9)
        )
        self.reminder_minutes.insert(0, "30")
        self.reminder_minutes.pack(side="left", padx=4, ipady=3)

        # Botões
        btn_frame = tk.Frame(footer, bg=COLORS["bg"])
        btn_frame.pack(side="right")

        tk.Button(
            btn_frame, text="Cancelar [Esc]",
            bg=COLORS["surface"], fg=COLORS["text_dim"],
            relief="flat", bd=0, padx=10, pady=5,
            font=("Consolas", 9), cursor="hand2",
            command=self.destroy,
        ).pack(side="left", padx=4)

        self.save_btn = tk.Button(
            btn_frame, text="Salvar [Ctrl+↵]",
            bg=COLORS["accent"], fg=COLORS["bg"],
            relief="flat", bd=0, padx=10, pady=5,
            font=("Consolas", 9, "bold"), cursor="hand2",
            command=self._save,
        )
        self.save_btn.pack(side="left")

    # ------------------------------------------------------------------
    # Helpers de UI
    # ------------------------------------------------------------------

    def _placeholder(self, widget: tk.Entry, text: str):
        """Implementa placeholder text para Entry."""
        widget.insert(0, text)
        widget.config(fg=COLORS["text_dim"])

        def on_focus_in(e):
            if widget.get() == text:
                widget.delete(0, "end")
                widget.config(fg=COLORS["text"])

        def on_focus_out(e):
            if not widget.get():
                widget.insert(0, text)
                widget.config(fg=COLORS["text_dim"])

        widget.bind("<FocusIn>", on_focus_in)
        widget.bind("<FocusOut>", on_focus_out)

    def _select_type(self, entry_type: str):
        """Atualiza visualmente o botão de tipo selecionado."""
        self.selected_type.set(entry_type)
        color = ENTRY_TYPES[entry_type]["color"]

        for key, btn in self._type_buttons.items():
            if key == entry_type:
                btn.config(bg=color, fg=COLORS["bg"])
            else:
                btn.config(bg=COLORS["surface"], fg=COLORS["text_dim"])

        # Mostra/oculta campo de minutos para lembretes
        if entry_type == "reminder":
            self.reminder_frame.pack(side="left")
        else:
            self.reminder_frame.pack_forget()

    # ------------------------------------------------------------------
    # Atalhos de teclado
    # ------------------------------------------------------------------

    def _bind_keys(self):
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-Return>", lambda e: self._save())

        # Ctrl+1..5 para tipos
        for i, key in enumerate(TYPE_KEYS, start=1):
            self.bind(f"<Control-Key-{i}>", lambda e, k=key: self._select_type(k))

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------

    def _save(self):
        content = self.content_text.get("1.0", "end").strip()
        if not content:
            self.content_text.focus_set()
            return

        title_raw = self.title_entry.get().strip()
        title = "" if title_raw == "Título (opcional)..." else title_raw

        entry_type = self.selected_type.get()

        # Configura lembrete se aplicável
        reminder_at = None
        reminder_interval = None
        if entry_type == "reminder":
            try:
                mins = int(self.reminder_minutes.get())
                reminder_at = (datetime.now() + timedelta(minutes=mins)).isoformat()
                reminder_interval = mins
            except ValueError:
                pass

        entry = Entry(
            content=content,
            title=title,
            entry_type=entry_type,
            reminder_at=reminder_at,
            reminder_interval_min=reminder_interval,
        )
        self.storage.save(entry)
        self._flash_and_close()

    def _flash_and_close(self):
        """Feedback visual rápido antes de fechar."""
        self.save_btn.config(text="✓ Salvo!", bg="#5CE07A")
        self.after(300, self.destroy)
