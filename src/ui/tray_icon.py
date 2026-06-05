"""
ui/tray_icon.py
Ícone da bandeja do sistema (system tray).
Usa `pystray` para rodar no Windows/Linux/Mac.
"""

from typing import Callable
import pystray
from PIL import Image, ImageDraw


def _create_icon_image() -> Image.Image:
    """
    Gera um ícone simples programaticamente — sem dependência de arquivo de imagem.
    Um círculo verde com letra 'F' (FlowPad).
    """
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo circular verde
    draw.ellipse([4, 4, size - 4, size - 4], fill="#5CE07A")

    # Letra F centralizada (sem dependência de fonte externa)
    draw.rectangle([20, 16, 28, 48], fill="white")   # Haste vertical
    draw.rectangle([20, 16, 44, 24], fill="white")   # Barra do topo
    draw.rectangle([20, 30, 38, 38], fill="white")   # Barra do meio

    return img


class TrayIcon:
    """
    Ícone na bandeja do sistema com menu de contexto.
    Corre em thread separada via `pystray`.
    """

    def __init__(
        self,
        on_open_dashboard: Callable,
        on_quick_capture: Callable,
        on_quit: Callable,
    ):
        self._on_open_dashboard = on_open_dashboard
        self._on_quick_capture = on_quick_capture
        self._on_quit = on_quit
        self._icon = self._build_icon()

    def _build_icon(self) -> pystray.Icon:
        menu = pystray.Menu(
            pystray.MenuItem("✏️  Captura Rápida", self._quick_capture, default=True),
            pystray.MenuItem("📋  Dashboard", self._open_dashboard),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️  Configurações", self._open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌  Sair", self._quit),
        )
        return pystray.Icon(
            name="FlowPad",
            icon=_create_icon_image(),
            title="FlowPad — Captura Rápida de Ideias",
            menu=menu,
        )

    # ------------------------------------------------------------------
    # Callbacks do menu
    # ------------------------------------------------------------------

    def _quick_capture(self, icon, item):
        self._on_quick_capture()

    def _open_dashboard(self, icon, item):
        self._on_open_dashboard()

    def _open_settings(self, icon, item):
        # Sprint 2: tela de configurações
        pass

    def _quit(self, icon, item):
        self._on_quit()

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def run(self):
        """Inicia o ícone (bloqueia a thread atual — rode em daemon thread)."""
        self._icon.run()

    def stop(self):
        self._icon.stop()
