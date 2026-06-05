"""
core/app.py
Controlador principal do FlowPad.
Gerencia o ciclo de vida: system tray, hotkeys globais e janelas.
"""

import threading
import tkinter as tk
from tkinter import messagebox

from core.storage import Storage
from core.hotkey_manager import HotkeyManager
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
        # Tkinter root oculta — necessária para as janelas filhas e notificações
        self.root = tk.Tk()
        self.root.withdraw()  # Esconde a janela raiz — só as filhas aparecem
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
        capture_key = hotkeys.get("quick_capture", "ctrl+shift+space")
        dashboard_key = hotkeys.get("dashboard", "ctrl+shift+f")

        self.hotkey_manager.register(capture_key, self._on_hotkey_capture)
        self.hotkey_manager.register(dashboard_key, self._on_hotkey_dashboard)

    # ------------------------------------------------------------------
    # Hotkey callbacks (chamados de thread separada — usa `after` p/ thread safety)
    # ------------------------------------------------------------------

    def _on_hotkey_capture(self):
        self.root.after(0, self.open_quick_capture)

    def _on_hotkey_dashboard(self):
        self.root.after(0, self.open_dashboard)

    def _open_settings_from_tray(self):
        """Wrapper com after() para chamar de dentro da thread do pystray com segurança."""
        self.root.after(0, self.open_settings)

    # ------------------------------------------------------------------
    # Ações públicas
    # ------------------------------------------------------------------

    def open_quick_capture(self, entry_type: str = "insight"):
        """Abre (ou foca) a janela de captura rápida."""
        if self._capture_window is None or not self._capture_window.winfo_exists():
            self._capture_window = QuickCaptureWindow(
                master=self.root,
                storage=self.storage,
                config=self.config,
                default_type=entry_type,
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
