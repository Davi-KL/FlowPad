"""
ui/quick_capture.py
Janela de captura rápida — minimalista e focada.

Fluxo:
  1. Abre em modo seleção (janela com foco, text area vazia).
  2. Teclas 1–4 escolhem o tipo e entram no modo escrita automaticamente.
  3. Qualquer outra tecla printável também entra no modo escrita
     (o caractere já aparece digitado).
  4. Enter salva e fecha. Shift+Enter insere nova linha. Esc fecha sem salvar.
  5. grab_set() bloqueia qualquer outra janela enquanto esta estiver aberta.
"""

import tkinter as tk
from core.storage import Storage, Entry
from utils.config import Config


# ──────────────────────────────────────────────────────────────────────
# Configuração visual por tipo
# ──────────────────────────────────────────────────────────────────────
TYPE_CONFIG = {
    "insight": {
        "label":      "💡  INSIGHT",
        "bg":         "#F4C542",
        "header_fg":  "#1A1A2E",
        "cursor":     "#C9A020",
    },
    "reminder": {
        "label":      "⏰  LEMBRETE",
        "bg":         "#E05C5C",
        "header_fg":  "#FFFFFF",
        "cursor":     "#B03840",
    },
    "clipboard": {
        "label":      "📋  CLIPBOARD",
        "bg":         "#5CB8E0",
        "header_fg":  "#1A1A2E",
        "cursor":     "#3A90B8",
    },
    "task": {
        "label":      "✅  TAREFA",
        "bg":         "#5CE07A",
        "header_fg":  "#1A1A2E",
        "cursor":     "#38B058",
    },
}

TYPES = list(TYPE_CONFIG.keys())   # ordem: insight, reminder, clipboard, task
TEXT_BG = "#FAFAFA"
TEXT_FG = "#1A1A2E"


class QuickCaptureWindow(tk.Toplevel):
    """
    Popup de captura rápida com fundo colorido por tipo.
    Modal: bloqueia interação com qualquer outra janela enquanto aberta.
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
        self._writing = False   # False = modo seleção | True = modo escrita

        self._configure_window()
        self._build_ui()
        self._apply_type(self._current_type)
        self._bind_keys()
        self._center()

        # Aguarda o Tkinter terminar de renderizar antes de capturar o foco.
        # Sem esse delay, o grab_set falha silenciosamente na 2ª abertura no Windows.
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
        self.geometry("440x215")
        self.resizable(False, False)
        self.attributes("-topmost", True)

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - self.winfo_width()) // 2
        y = (sh - self.winfo_height()) // 3   # Levemente acima do centro
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Cabeçalho: nome do tipo atual
        self.type_label = tk.Label(
            self, text="",
            font=("Consolas", 14, "bold"),
            pady=12,
        )
        self.type_label.pack(fill="x")

        # Área de texto principal
        self.text_widget = tk.Text(
            self,
            font=("Consolas", 12),
            relief="flat", bd=0,
            wrap="word", height=5,
            padx=16, pady=10,
            bg=TEXT_BG, fg=TEXT_FG,
        )
        self.text_widget.pack(fill="both", expand=True, padx=12)

        # Dica de atalhos
        self.hint_label = tk.Label(
            self,
            text="1:💡  2:⏰  3:📋  4:✅    Enter salva  •  Shift+Enter nova linha  •  Esc cancela",
            font=("Consolas", 7),
            pady=7,
        )
        self.hint_label.pack(fill="x")

    def _apply_type(self, entry_type: str):
        """Atualiza fundo e label para o tipo selecionado."""
        cfg = TYPE_CONFIG[entry_type]
        self._current_type = entry_type
        self.configure(bg=cfg["bg"])
        self.type_label.configure(bg=cfg["bg"], fg=cfg["header_fg"], text=cfg["label"])
        self.text_widget.configure(insertbackground=cfg["cursor"])
        self.hint_label.configure(bg=cfg["bg"], fg=cfg["header_fg"])

    # ------------------------------------------------------------------
    # Modo seleção → modo escrita
    # ------------------------------------------------------------------

    def _enter_writing_mode(self, initial_char: str = ""):
        """
        Transita para o modo escrita: foca o text widget.
        Remove os bindings de 1–4 da janela para que possam ser digitados normalmente.
        """
        if not self._writing:
            self._writing = True
            for i in range(1, 5):
                self.unbind(f"<Key-{i}>")
        self.text_widget.focus_set()
        if initial_char:
            self.text_widget.insert("end", initial_char)

    # ------------------------------------------------------------------
    # Atalhos
    # ------------------------------------------------------------------

    def _bind_keys(self):
        # Esc fecha em qualquer estado
        self.bind("<Escape>", lambda e: self.destroy())
        self.text_widget.bind("<Escape>", lambda e: self.destroy())

        # Enter no modo seleção: confirma o tipo e entra no modo escrita.
        # Enter no modo escrita: salva (binding no text_widget tem prioridade).
        self.bind("<Return>", self._on_window_enter)
        # Shift+Enter registrado ANTES de <Return> para ter prioridade de matching.
        self.text_widget.bind("<Shift-Return>", self._on_shift_return)
        self.text_widget.bind("<Return>", self._on_return)

        # Teclas 1–4: apenas mudam o tipo (ficam em modo seleção para poder trocar)
        for i, tipo in enumerate(TYPES, start=1):
            self.bind(f"<Key-{i}>", lambda e, t=tipo: self._on_type_key(t))

        # Qualquer outra tecla printável entra direto no modo escrita
        self.bind("<KeyPress>", self._on_any_key)

    def _on_type_key(self, entry_type: str):
        """Muda o tipo visualmente — NÃO entra no modo escrita ainda."""
        self._apply_type(entry_type)
        return "break"

    def _on_window_enter(self, event):
        """Enter no modo seleção confirma o tipo e libera a escrita."""
        if not self._writing:
            self._enter_writing_mode()
        return "break"

    def _on_any_key(self, event):
        """
        Tecla printável que não é 1–4: entra no modo escrita com o
        caractere já inserido (atalho para quem não quer usar o Enter).
        """
        if self._writing:
            return
        if not event.char or not event.char.isprintable():
            return
        if event.char in "1234":
            return   # Tratado por _on_type_key
        self._enter_writing_mode(initial_char=event.char)
        return "break"

    def _on_shift_return(self, event):
        """Shift+Enter insere nova linha sem salvar."""
        self.text_widget.insert("insert", "\n")
        return "break"

    def _on_return(self, event):
        # Tkinter dispara <Return> mesmo com Shift — ignora se Shift estiver pressionado.
        if event.state & 0x1:
            return
        self._save()
        return "break"

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------

    def _save(self):
        content = self.text_widget.get("1.0", "end").strip()
        if not content:
            return

        self.storage.save(Entry(content=content, entry_type=self._current_type))

        # Feedback visual antes de fechar
        self.type_label.configure(text="✓  Salvo!")
        self.after(280, self.destroy)
