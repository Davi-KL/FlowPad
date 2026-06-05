"""
FlowPad - Quick Capture Tool
Entry point da aplicação.
"""

import sys
import os

# Garante que o diretório src está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import FlowPadApp


def main():
    app = FlowPadApp()
    app.run()


if __name__ == "__main__":
    main()
