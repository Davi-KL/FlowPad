"""
core/app.py
Controlador principal do FlowPad.
Gerencia o ciclo de vida: system tray, hotkeys globais e janelas.
"""

import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from core.storage import Storage, register_extra_types
from core.hotkey_manager import HotkeyManager
from core.plugin_manager import PluginManager
from core.reminder_scheduler import ReminderScheduler
from ui.tray_icon import TrayIcon
from ui.quick_capture import QuickCaptureWindow
from ui.dashboard import DashboardWindow
from ui.settings import SettingsWindow
from utils.config import Config


class FlowPadApp:
    """
    Classe central que inicializa e coordena todos os módulos do FlowPad.
    """

    def __init__(self):
        # Janela root oculta — necessária para as janelas filhas e notificações
        self.root = ctk.CTk()
        self.root.withdraw()
        self.root.title("FlowPad")

        # Módulos principais
        self.config = Config()
        self.storage = Storage(self.config.data_path)
        self.hotkey_manager = HotkeyManager()
        self.reminder_scheduler = ReminderScheduler(self.root, self.storage)

        # Janelas (lazy — só criadas quando abertas pela 1ª vez)
        self._capture_window: QuickCaptureWindow | None = None
        self._dashboard_window: DashboardWindow | None = None
        self._settings_window: SettingsWindow | None = None

        self._setup_tray()
        self._register_hotkeys()
        self.reminder_scheduler.start()
        self._load_plugins()
        self._start_clipboard_monitor()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_tray(self):
        """Cria o ícone na bandeja do sistema."""
        self.tray = TrayIcon(
            on_open_dashboard=self.open_dashboard,
            on_quick_capture=self.open_quick_capture,
            on_open_settings=self._open_settings_from_tray,
            on_quit=self.quit,
        )

    def _register_hotkeys(self):
        """Registra os atalhos globais conforme configuração do usuário."""
        hotkeys = self.config.get("hotkeys", {})
        capture_key   = hotkeys.get("quick_capture",          "ctrl+shift+space")
        dashboard_key = hotkeys.get("dashboard",              "ctrl+shift+f")
        reminder_key  = hotkeys.get("quick_capture_reminder", "ctrl+alt+r")

        self.hotkey_manager.register(capture_key,   self._on_hotkey_capture)
        self.hotkey_manager.register(dashboard_key, self._on_hotkey_dashboard)
        self.hotkey_manager.register(reminder_key,  self._on_hotkey_type_reminder)

    def _load_plugins(self):
        """Carrega plugins de src/plugins/ e registra tipos/hotkeys extras."""
        from pathlib import Path
        plugin_dir = Path(__file__).parent.parent / "plugins"
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins(str(plugin_dir), self)
        extra = self.plugin_manager.get_extra_types()
        if extra:
            register_extra_types(extra)

    # ------------------------------------------------------------------
    # Hotkey callbacks (chamados de thread separada — usa `after` p/ thread safety)
    # ------------------------------------------------------------------

    def _on_hotkey_capture(self):
        self.root.after(0, self.open_quick_capture)

    def _on_hotkey_dashboard(self):
        self.root.after(0, self.open_dashboard)

    def _on_hotkey_type_reminder(self):
        self.root.after(0, lambda: self.open_quick_capture("reminder", start_editing=True))

    def _open_settings_from_tray(self):
        """Wrapper com after() para chamar de dentro da thread do pystray com segurança."""
        self.root.after(0, self.open_settings)

    # ------------------------------------------------------------------
    # Ações públicas
    # ------------------------------------------------------------------

    def _start_clipboard_monitor(self):
        """Inicializa o monitor de clipboard com o conteúdo atual como baseline."""
        try:
            self._last_clipboard = self.root.clipboard_get()
        except tk.TclError:
            self._last_clipboard = ""
        self._poll_clipboard()

    def _poll_clipboard(self):
        """Verifica mudanças no clipboard a cada 1s e salva automaticamente."""
        try:
            current = self.root.clipboard_get()
            if current != self._last_clipboard:
                if current.strip() and self.config.get("clipboard_monitor", True):
                    from core.storage import Entry
                    self.storage.save(Entry(content=current, entry_type="clipboard"))
                self._last_clipboard = current
        except tk.TclError:
            pass  # clipboard vazio ou conteúdo não-texto (imagem, arquivo)
        self.root.after(1000, self._poll_clipboard)

    def open_quick_capture(self, entry_type: str = "insight", start_editing: bool = False):
        """Abre (ou foca) a janela de captura rápida."""
        if self._capture_window is None or not self._capture_window.winfo_exists():
            self._capture_window = QuickCaptureWindow(
                master=self.root,
                storage=self.storage,
                config=self.config,
                default_type=entry_type,
                start_editing=start_editing,
            )
        else:
            self._capture_window.lift()
            self._capture_window.focus_force()

    def open_dashboard(self):
        """Abre (ou foca) o dashboard de entradas."""
        if self._dashboard_window is None or not self._dashboard_window.winfo_exists():
            self._dashboard_window = DashboardWindow(
                master=self.root,
                storage=self.storage,
                config=self.config,
                on_open_capture=self.open_quick_capture,
            )
        else:
            self._dashboard_window.lift()
            self._dashboard_window.focus_force()

    def open_settings(self):
        """Abre (ou foca) a tela de configurações."""
        if self._settings_window is None or not self._settings_window.winfo_exists():
            self._settings_window = SettingsWindow(
                master=self.root,
                config=self.config,
                on_hotkeys_changed=self.reload_hotkeys,
            )
        else:
            self._settings_window.lift()
            self._settings_window.focus_force()

    def reload_hotkeys(self, new_hotkeys: dict):
        """Para o listener atual e registra os novos atalhos do config."""
        self.hotkey_manager.unregister_all()
        self._register_hotkeys()

    def quit(self):
        """Encerra o aplicativo de forma limpa."""
        self.hotkey_manager.unregister_all()
        self.reminder_scheduler.stop()
        self.tray.stop()
        self.root.quit()

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def run(self):
        """Inicia o loop principal do Tkinter e o thread do tray."""
        tray_thread = threading.Thread(target=self.tray.run, daemon=True)
        tray_thread.start()

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit()
