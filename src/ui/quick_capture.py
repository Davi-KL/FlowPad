"""
ui/quick_capture.py
Janela de captura rápida — minimalista e focada.

Fluxo:
  1. Abre em modo seleção: 1–5 trocam o tipo, Enter confirma e abre os campos.
  2. Qualquer tecla imprimível (exceto 1–5) também confirma e insere o char no 1º campo.
  3. Tipos de campo único (insight, clipboard, tarefa): Enter salva, Shift+Enter nova linha.
  4. Lembrete: 3 campos simultâneos (texto, hora HH:MM com máscara, data DD/MM com máscara).
     Tab ou Enter avança entre campos; Ctrl+Enter salva de qualquer campo.
  5. Nota: título (Entry) + conteúdo (Text). Enter no título move ao conteúdo.
     Ctrl+Enter salva de qualquer campo.
  6. Esc fecha sem salvar. grab_set() bloqueia outras janelas.
"""

import tkinter as tk
from datetime import datetime, date as date_type

import customtkinter as ctk

from core.storage import Storage, Entry
from utils.config import Config
from ui.colors import TYPE_BG, TYPE_FG


TYPE_CONFIG = {
    "insight":   {"label": "💡  INSIGHT",   "cursor": "#C9A020"},
    "reminder":  {"label": "⏰  LEMBRETE",  "cursor": "#B03840"},
    "clipboard": {"label": "📋  CLIPBOARD", "cursor": "#3A90B8"},
    "task":      {"label": "✅  TAREFA",    "cursor": "#38B058"},
    "note":      {"label": "📝  NOTA",      "cursor": "#7A50B8"},
}

TYPES = list(TYPE_CONFIG.keys())
SINGLE_TYPES = {"insight", "clipboard", "task"}

TEXT_BG = "#FAFAFA"
TEXT_FG = "#1A1A2E"
ENTRY_FONT = ("Consolas", 11)
LABEL_FONT = ("Consolas", 8)


class QuickCaptureWindow(ctk.CTkToplevel):
    """
    Popup de captura rápida com fundo colorido por tipo e fade-in.
    Modal: bloqueia interação com outras janelas enquanto aberta.
    """

    def __init__(
        self,
        master: ctk.CTk,
        storage: Storage,
        config: Config,
        default_type: str = "insight",
        start_editing: bool = False,
    ):
        super().__init__(master)
        self.storage = storage
        self.config = config
        self._current_type = default_type if default_type in TYPE_CONFIG else "insight"
        self._editing = False   # False = modo seleção, True = campos visíveis
        self._start_editing = start_editing

        self._configure_window()
        self._build_static_ui()
        self._apply_type(self._current_type)
        self._bind_global_keys()
        self._center()
        self.after(50, self._activate)

    # ------------------------------------------------------------------
    # Janela
    # ------------------------------------------------------------------

    def _activate(self):
        self.lift()
        self.focus_force()
        self.grab_set()
        self._fade_in()
        if self._start_editing:
            self.after(50, self._enter_edit_mode)

    def _fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 1.0:
            self.attributes("-alpha", min(1.0, alpha + 0.1))
            self.after(16, self._fade_in)

    def _configure_window(self):
        self.title("FlowPad")
        self.geometry("460x300")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - self.winfo_width()) // 2
        y = (sh - self.winfo_height()) // 3
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Estrutura estática da UI
    # ------------------------------------------------------------------

    def _build_static_ui(self):
        self.type_label = tk.Label(
            self, text="",
            font=("Consolas", 14, "bold"), pady=8,
        )
        self.type_label.pack(fill="x")

        # Área de conteúdo dinâmico — reconstruída ao trocar de tipo
        self._content_area = tk.Frame(self)
        self._content_area.pack(fill="both", expand=True, padx=14)

        self.hint_label = tk.Label(
            self, text="", font=("Consolas", 7), pady=6,
        )
        self.hint_label.pack(fill="x")

    # ------------------------------------------------------------------
    # Troca de tipo — reconstrói os campos
    # ------------------------------------------------------------------

    def _apply_type(self, entry_type: str):
        cfg = TYPE_CONFIG[entry_type]
        bg  = TYPE_BG[entry_type]
        fg  = TYPE_FG[entry_type]
        self._current_type = entry_type

        self.configure(fg_color=bg)
        self.type_label.configure(bg=bg, fg=fg, text=cfg["label"])
        self._content_area.configure(bg=bg)
        self.hint_label.configure(bg=bg, fg=fg)

        if self._editing:
            self._build_fields()
        else:
            # Modo seleção: mostra só o placeholder
            for w in self._content_area.winfo_children():
                w.destroy()
            tk.Label(
                self._content_area,
                text="pressione Enter para começar",
                font=("Consolas", 9), bg=bg, fg=fg,
            ).pack(expand=True)
            self.hint_label.configure(
                text="1:💡  2:⏰  3:📋  4:✅  5:📝    Enter confirma  •  Esc cancela"
            )

    def _enter_edit_mode(self, initial_char: str = ""):
        """Confirma o tipo e exibe os campos de entrada."""
        if self._editing:
            return
        self._editing = True
        self._build_fields()

        # Insere o caractere inicial no primeiro campo, se houver
        if initial_char:
            if self._current_type in SINGLE_TYPES:
                try: self.text_widget.insert("end", initial_char)
                except AttributeError: pass
            elif self._current_type == "reminder":
                try: self.rem_content.insert("end", initial_char)
                except AttributeError: pass
            elif self._current_type == "note":
                try: self.note_title.insert("end", initial_char)
                except AttributeError: pass

    def _build_fields(self):
        """Reconstrói os campos na content_area para o tipo atual."""
        for w in self._content_area.winfo_children():
            w.destroy()

        bg     = TYPE_BG[self._current_type]
        fg     = TYPE_FG[self._current_type]
        cursor = TYPE_CONFIG[self._current_type]["cursor"]

        if self._current_type == "reminder":
            self._build_reminder_fields(bg, fg, cursor)
            self.hint_label.configure(
                text="Tab/Enter avança entre campos  •  Ctrl+Enter salva  •  Esc cancela"
            )
        elif self._current_type == "note":
            self._build_note_fields(bg, fg, cursor)
            self.hint_label.configure(
                text="Enter no título vai ao conteúdo  •  Ctrl+Enter salva  •  Esc cancela"
            )
        else:
            self._build_single_field(bg, fg, cursor)
            self.hint_label.configure(
                text="Enter salva  •  Shift+Enter nova linha  •  Esc cancela"
            )

    # ------------------------------------------------------------------
    # Layouts por tipo
    # ------------------------------------------------------------------

    def _build_single_field(self, bg: str, fg: str, cursor: str):
        self.text_widget = tk.Text(
            self._content_area,
            font=("Consolas", 12), relief="flat", bd=0,
            wrap="word", height=5, padx=16, pady=8,
            bg=TEXT_BG, fg=TEXT_FG, insertbackground=cursor,
        )
        self.text_widget.pack(fill="both", expand=True)
        self.text_widget.focus_set()
        self.text_widget.bind("<Escape>",      lambda e: self.destroy())
        self.text_widget.bind("<Shift-Return>", self._on_shift_return)
        self.text_widget.bind("<Return>",       self._on_single_return)

    def _build_reminder_fields(self, bg: str, fg: str, cursor: str):
        # Campo: texto do lembrete
        tk.Label(
            self._content_area, text="  Lembrete",
            font=LABEL_FONT, bg=bg, fg=fg, anchor="w",
        ).pack(fill="x")

        self.rem_content = tk.Entry(
            self._content_area,
            font=ENTRY_FONT, relief="flat", bd=0,
            bg=TEXT_BG, fg=TEXT_FG, insertbackground=cursor,
        )
        self.rem_content.pack(fill="x", ipady=7, pady=(0, 10))
        self.rem_content.focus_set()
        self.rem_content.bind("<Return>",         lambda e: (self.rem_time.focus_set(), "break")[1])
        self.rem_content.bind("<Escape>",         lambda e: self.destroy())
        self.rem_content.bind("<Control-Return>", lambda e: self._save())

        # Linha: Horário + Data lado a lado
        row = tk.Frame(self._content_area, bg=bg)
        row.pack(fill="x")

        # Horário
        time_col = tk.Frame(row, bg=bg)
        time_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Label(
            time_col, text="  Horário  (HH:MM)",
            font=LABEL_FONT, bg=bg, fg=fg, anchor="w",
        ).pack(fill="x")

        self.rem_time = tk.Entry(
            time_col,
            font=("Consolas", 13), relief="flat", bd=0,
            bg=TEXT_BG, fg=TEXT_FG, insertbackground=cursor,
        )
        self.rem_time.pack(fill="x", ipady=7)
        self.rem_time.bind("<KeyPress>",       lambda e: self._masked_keypress(e, self.rem_time, ":", self.rem_date))
        self.rem_time.bind("<Return>",         lambda e: (self.rem_date.focus_set(), "break")[1])
        self.rem_time.bind("<Escape>",         lambda e: self.destroy())
        self.rem_time.bind("<Control-Return>", lambda e: self._save())

        # Data
        date_col = tk.Frame(row, bg=bg)
        date_col.pack(side="left", fill="x", expand=True)

        tk.Label(
            date_col, text="  Data  (DD/MM — vazio = hoje)",
            font=LABEL_FONT, bg=bg, fg=fg, anchor="w",
        ).pack(fill="x")

        self.rem_date = tk.Entry(
            date_col,
            font=("Consolas", 13), relief="flat", bd=0,
            bg=TEXT_BG, fg=TEXT_FG, insertbackground=cursor,
        )
        self.rem_date.pack(fill="x", ipady=7)
        self.rem_date.bind("<KeyPress>",       lambda e: self._masked_keypress(e, self.rem_date, "/", None))
        self.rem_date.bind("<Return>",         lambda e: self._save())
        self.rem_date.bind("<Escape>",         lambda e: self.destroy())
        self.rem_date.bind("<Control-Return>", lambda e: self._save())

    def _build_note_fields(self, bg: str, fg: str, cursor: str):
        # Título
        tk.Label(
            self._content_area, text="  Título",
            font=LABEL_FONT, bg=bg, fg=fg, anchor="w",
        ).pack(fill="x")

        self.note_title = tk.Entry(
            self._content_area,
            font=ENTRY_FONT, relief="flat", bd=0,
            bg=TEXT_BG, fg=TEXT_FG, insertbackground=cursor,
        )
        self.note_title.pack(fill="x", ipady=7, pady=(0, 8))
        self.note_title.focus_set()
        self.note_title.bind("<Return>",         lambda e: (self.note_content.focus_set(), "break")[1])
        self.note_title.bind("<Escape>",         lambda e: self.destroy())
        self.note_title.bind("<Control-Return>", lambda e: self._save())

        # Conteúdo
        tk.Label(
            self._content_area, text="  Conteúdo",
            font=LABEL_FONT, bg=bg, fg=fg, anchor="w",
        ).pack(fill="x")

        self.note_content = tk.Text(
            self._content_area,
            font=("Consolas", 11), relief="flat", bd=0,
            wrap="word", height=4, padx=8, pady=6,
            bg=TEXT_BG, fg=TEXT_FG, insertbackground=cursor,
        )
        self.note_content.pack(fill="both", expand=True)
        self.note_content.bind("<Escape>",         lambda e: self.destroy())
        self.note_content.bind("<Control-Return>", lambda e: self._save())

    # ------------------------------------------------------------------
    # Máscara para horário e data
    # ------------------------------------------------------------------

    def _masked_keypress(self, event, entry: tk.Entry, sep: str, next_widget) -> str:
        sym = event.keysym

        # Deixa Tab, Esc e Ctrl+qualquer coisa passarem normalmente
        if sym in ("Tab", "Escape") or (event.state & 0x4):
            return

        if sym == "BackSpace":
            current = entry.get()
            if current:
                # Se o último char é o separador, remove os dois últimos
                if current.endswith(sep):
                    entry.delete(len(current) - 1, "end")
                else:
                    entry.delete(len(current) - 1, "end")
            return "break"

        char = event.char
        if not char or not char.isdigit():
            return "break"

        current = entry.get()
        digits  = current.replace(sep, "")

        if len(digits) >= 4:
            return "break"

        # Após 2 dígitos, insere o separador automaticamente
        if len(digits) == 2:
            entry.insert("end", sep + char)
        else:
            entry.insert("end", char)

        # Avança ao próximo campo após preencher os 4 dígitos
        if len(entry.get().replace(sep, "")) == 4 and next_widget:
            next_widget.focus_set()

        return "break"

    # ------------------------------------------------------------------
    # Atalhos globais da janela
    # ------------------------------------------------------------------

    def _bind_global_keys(self):
        self.bind("<Escape>",         lambda e: self.destroy())
        self.bind("<Return>",         self._on_window_enter)
        self.bind("<Control-Return>", lambda e: self._save())
        self.bind("<KeyPress>",       self._on_any_key)

        for i, tipo in enumerate(TYPES, start=1):
            self.bind(
                f"<Key-{i}>",
                lambda e, t=tipo: self._apply_type(t)
                if not isinstance(e.widget, (tk.Entry, tk.Text))
                else None,
            )

    def _on_window_enter(self, event):
        """Enter em modo seleção confirma o tipo; no modo edição, os campos tratam o evento."""
        if not self._editing:
            self._enter_edit_mode()
        return "break"

    def _on_any_key(self, event):
        """Qualquer tecla imprimível (exceto 1–5) em modo seleção entra no modo edição."""
        if self._editing:
            return
        char = event.char
        if not char or not char.isprintable():
            return
        if char in "12345":
            return
        self._enter_edit_mode(initial_char=char)
        return "break"

    # ------------------------------------------------------------------
    # Handlers de tecla para campo único
    # ------------------------------------------------------------------

    def _on_single_return(self, event):
        if event.state & 0x1:   # Shift+Enter → nova linha (handled by _on_shift_return)
            return
        self._save()
        return "break"

    def _on_shift_return(self, event):
        self.text_widget.insert("insert", "\n")
        return "break"

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------

    def _save(self):
        entry_type = self._current_type

        if entry_type == "reminder":
            content = self.rem_content.get().strip()
            if not content:
                self.rem_content.focus_set()
                return
            reminder_at = self._build_reminder_at(
                self.rem_time.get().strip(),
                self.rem_date.get().strip(),
            )
            entry = Entry(content=content, entry_type="reminder", reminder_at=reminder_at)

        elif entry_type == "note":
            title   = self.note_title.get().strip()
            content = self.note_content.get("1.0", "end").strip()
            if not title and not content:
                self.note_title.focus_set()
                return
            entry = Entry(content=content, entry_type="note", title=title)

        else:
            content = self.text_widget.get("1.0", "end").strip()
            if not content:
                return
            entry = Entry(content=content, entry_type=entry_type)

        self.storage.save(entry)
        self.type_label.configure(text="✓  Salvo!")
        self.after(280, self.destroy)

    @staticmethod
    def _build_reminder_at(time_str: str, date_str: str) -> str | None:
        try:
            digits = time_str.replace(":", "").strip()
            h, m   = int(digits[:2]), int(digits[2:4])
            if date_str.strip():
                ddigits = date_str.replace("/", "").strip()
                d, mo   = int(ddigits[:2]), int(ddigits[2:4])
                dt = datetime(datetime.now().year, mo, d, h, m)
            else:
                today = date_type.today()
                dt    = datetime(today.year, today.month, today.day, h, m)
            return dt.isoformat()
        except (ValueError, IndexError):
            return None
