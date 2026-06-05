"""
ui/quick_capture.py
Janela de captura rápida — minimalista e focada.

Fluxo:
  1. Abre em modo seleção (janela com foco, área de texto vazia).
  2. Teclas 1–5 escolhem o tipo sem entrar no modo escrita.
  3. Enter (ou qualquer tecla printável) entra no modo escrita.
  4. Tipos de fluxo único (insight, clipboard, task): Enter salva.
  5. Tipos multi-passo (reminder 3 passos, note 2 passos): Enter avança ao próximo passo.
  6. Shift+Enter insere nova linha. Esc fecha sem salvar.
  7. grab_set() bloqueia qualquer outra janela enquanto esta estiver aberta.
"""

import tkinter as tk
from datetime import datetime, date as date_type
from core.storage import Storage, Entry
from utils.config import Config


# ──────────────────────────────────────────────────────────────────────
# Configuração visual por tipo
# ──────────────────────────────────────────────────────────────────────
TYPE_CONFIG = {
    "insight": {
        "label":     "💡  INSIGHT",
        "bg":        "#F4C542",
        "header_fg": "#1A1A2E",
        "cursor":    "#C9A020",
    },
    "reminder": {
        "label":     "⏰  LEMBRETE",
        "bg":        "#E05C5C",
        "header_fg": "#FFFFFF",
        "cursor":    "#B03840",
    },
    "clipboard": {
        "label":     "📋  CLIPBOARD",
        "bg":        "#5CB8E0",
        "header_fg": "#1A1A2E",
        "cursor":    "#3A90B8",
    },
    "task": {
        "label":     "✅  TAREFA",
        "bg":        "#5CE07A",
        "header_fg": "#1A1A2E",
        "cursor":    "#38B058",
    },
    "note": {
        "label":     "📝  NOTA",
        "bg":        "#A07AE0",
        "header_fg": "#FFFFFF",
        "cursor":    "#7A50B8",
    },
}

TYPES = list(TYPE_CONFIG.keys())

# Passos de cada tipo: lista de (chave_do_dado, texto_do_prompt)
STEPS: dict[str, list[tuple[str, str]]] = {
    "insight":   [("content", "Escreva seu insight...")],
    "reminder":  [
        ("content", "Qual é o lembrete?"),
        ("time",    "Horário?  (HH:MM — ex: 14:30)"),
        ("date",    "Data?  (DD/MM — Enter = hoje)"),
    ],
    "clipboard": [("content", "Cole ou escreva o conteúdo...")],
    "task":      [("content", "O que precisa ser feito?")],
    "note":      [
        ("title",   "Título da nota:"),
        ("content", "Conteúdo da nota..."),
    ],
}

TEXT_BG = "#FAFAFA"
TEXT_FG = "#1A1A2E"


class QuickCaptureWindow(tk.Toplevel):
    """
    Popup de captura rápida com fundo colorido por tipo.
    Modal: bloqueia interação com qualquer outra janela enquanto aberta.
    Suporta fluxos multi-passo para Lembrete e Nota.
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
        self._current_type = default_type if default_type in TYPE_CONFIG else "insight"
        self._writing = False
        self._step = 0
        self._step_data: dict[str, str] = {}

        self._configure_window()
        self._build_ui()
        self._apply_type(self._current_type)
        self._bind_keys()
        self._center()

        self.after(50, self._activate)

    # ------------------------------------------------------------------
    # Janela
    # ------------------------------------------------------------------

    def _activate(self):
        """Força foco e modal após a janela estar totalmente renderizada."""
        self.lift()
        self.focus_force()
        self.grab_set()

    def _configure_window(self):
        self.title("FlowPad")
        self.geometry("440x250")
        self.resizable(False, False)
        self.attributes("-topmost", True)

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - self.winfo_width()) // 2
        y = (sh - self.winfo_height()) // 3
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.type_label = tk.Label(
            self, text="",
            font=("Consolas", 14, "bold"),
            pady=8,
        )
        self.type_label.pack(fill="x")

        self.prompt_label = tk.Label(
            self, text="",
            font=("Consolas", 9),
            pady=0,
        )
        self.prompt_label.pack(fill="x")

        self.text_widget = tk.Text(
            self,
            font=("Consolas", 12),
            relief="flat", bd=0,
            wrap="word", height=5,
            padx=16, pady=8,
            bg=TEXT_BG, fg=TEXT_FG,
        )
        self.text_widget.pack(fill="both", expand=True, padx=12)

        self.hint_label = tk.Label(
            self,
            text="1:💡  2:⏰  3:📋  4:✅  5:📝    Enter seleciona  •  Esc cancela",
            font=("Consolas", 7),
            pady=6,
        )
        self.hint_label.pack(fill="x")

    def _apply_type(self, entry_type: str):
        cfg = TYPE_CONFIG[entry_type]
        self._current_type = entry_type
        self.configure(bg=cfg["bg"])
        self.type_label.configure(bg=cfg["bg"], fg=cfg["header_fg"], text=cfg["label"])
        self.prompt_label.configure(bg=cfg["bg"], fg=cfg["header_fg"], text="")
        self.text_widget.configure(insertbackground=cfg["cursor"])
        self.hint_label.configure(bg=cfg["bg"], fg=cfg["header_fg"])

    def _update_prompt(self):
        """Atualiza o label de prompt e o hint para o passo atual."""
        steps = STEPS[self._current_type]
        total = len(steps)
        _, prompt_text = steps[self._step]
        step_info = f"  [{self._step + 1}/{total}]" if total > 1 else ""
        self.prompt_label.configure(text=f"  {prompt_text}{step_info}")

        is_last = self._step == total - 1
        action = "salvar" if is_last else "avançar"
        self.hint_label.configure(
            text=f"Enter {action}  •  Shift+Enter nova linha  •  Esc cancela"
        )

    # ------------------------------------------------------------------
    # Modo seleção → modo escrita
    # ------------------------------------------------------------------

    def _enter_writing_mode(self, initial_char: str = ""):
        if not self._writing:
            self._writing = True
            self._step = 0
            self._step_data = {}
            for i in range(1, 6):
                self.unbind(f"<Key-{i}>")
            self._update_prompt()
        self.text_widget.focus_set()
        if initial_char:
            self.text_widget.insert("end", initial_char)

    # ------------------------------------------------------------------
    # Atalhos
    # ------------------------------------------------------------------

    def _bind_keys(self):
        self.bind("<Escape>", lambda e: self.destroy())
        self.text_widget.bind("<Escape>", lambda e: self.destroy())

        self.bind("<Return>", self._on_window_enter)
        self.text_widget.bind("<Shift-Return>", self._on_shift_return)
        self.text_widget.bind("<Return>", self._on_return)

        for i, tipo in enumerate(TYPES, start=1):
            self.bind(f"<Key-{i}>", lambda e, t=tipo: self._on_type_key(t))

        self.bind("<KeyPress>", self._on_any_key)

    def _on_type_key(self, entry_type: str):
        self._apply_type(entry_type)
        return "break"

    def _on_window_enter(self, event):
        if not self._writing:
            self._enter_writing_mode()
        return "break"

    def _on_any_key(self, event):
        if self._writing:
            return
        if not event.char or not event.char.isprintable():
            return
        if event.char in "12345":
            return
        self._enter_writing_mode(initial_char=event.char)
        return "break"

    def _on_shift_return(self, event):
        self.text_widget.insert("insert", "\n")
        return "break"

    def _on_return(self, event):
        if event.state & 0x1:  # Shift pressionado
            return
        self._advance_step()
        return "break"

    # ------------------------------------------------------------------
    # Lógica de passos
    # ------------------------------------------------------------------

    def _advance_step(self):
        """Salva o campo atual e avança ao próximo passo ou salva a entrada."""
        steps = STEPS[self._current_type]
        current_key = steps[self._step][0]
        value = self.text_widget.get("1.0", "end").strip()

        # A data pode ser vazia (significa hoje); os outros campos são obrigatórios
        if not value and current_key != "date":
            return

        self._step_data[current_key] = value
        self._step += 1

        if self._step < len(steps):
            self.text_widget.delete("1.0", "end")
            self._update_prompt()
        else:
            self._save()

    def _save(self):
        """Cria a Entry com os dados coletados e fecha a janela."""
        data = self._step_data
        entry_type = self._current_type

        if entry_type == "reminder":
            reminder_at = self._build_reminder_at(
                data.get("time", ""),
                data.get("date", ""),
            )
            entry = Entry(
                content=data.get("content", ""),
                entry_type="reminder",
                reminder_at=reminder_at,
            )
        elif entry_type == "note":
            entry = Entry(
                content=data.get("content", ""),
                entry_type="note",
                title=data.get("title", ""),
            )
        else:
            entry = Entry(
                content=data.get("content", ""),
                entry_type=entry_type,
            )

        self.storage.save(entry)
        self.type_label.configure(text="✓  Salvo!")
        self.after(280, self.destroy)

    @staticmethod
    def _build_reminder_at(time_str: str, date_str: str) -> str | None:
        """Converte strings de hora e data em ISO datetime. Retorna None se inválido."""
        try:
            parts = time_str.strip().split(":")
            h, m = int(parts[0]), int(parts[1])
            if date_str.strip():
                d_parts = date_str.strip().split("/")
                d, mo = int(d_parts[0]), int(d_parts[1])
                year = datetime.now().year
                dt = datetime(year, mo, d, h, m)
            else:
                today = date_type.today()
                dt = datetime(today.year, today.month, today.day, h, m)
            return dt.isoformat()
        except (ValueError, IndexError):
            return None
