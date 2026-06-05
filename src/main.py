"""
FlowPad - Quick Capture Tool
Entry point da aplicação.
"""

import sys
import os

import customtkinter as ctk

# Garante que o diretório src está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import FlowPadApp

# Aparência global — pode ser "dark", "light" ou "system"
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def main():
    app = FlowPadApp()
    app.run()


if __name__ == "__main__":
    main()
