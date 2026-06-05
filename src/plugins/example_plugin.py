"""
plugins/example_plugin.py
Plugin de exemplo — demonstra como registrar um tipo customizado no FlowPad.

Para ativar: certifique-se de que este arquivo está em src/plugins/.
O FlowPad carrega automaticamente todos os .py desta pasta na inicialização.
"""


def register(app) -> dict:
    """
    Registra tipos e hotkeys extras.
    Retorne um dict com as chaves 'types' e/ou 'hotkeys'.
    """
    return {
        "types": {
            "bookmark": {
                "label": "🔖 Favorito",
                "color": "#FF8C00",
            }
        },
        # Descomente para ativar o atalho global Ctrl+Shift+B:
        # "hotkeys": {
        #     "ctrl+shift+b": lambda: app.open_quick_capture("bookmark")
        # },
    }
