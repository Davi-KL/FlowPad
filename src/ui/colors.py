"""
ui/colors.py
Paleta de cores centralizada do FlowPad.
Cada cor é uma tupla (light, dark) compatível com CustomTkinter appearance_mode.
"""

# Cores gerais da interface
COLORS: dict[str, tuple[str, str]] = {
    "bg":           ("#F0F2F5", "#1A1A2E"),
    "surface":      ("#E2E8F0", "#16213E"),
    "row":          ("#D8E0EE", "#0E1C38"),
    "selected":     ("#A8C0DC", "#1A3A6E"),
    "border":       ("#9AAABB", "#1E4080"),
    "accent":       ("#1D8A4C", "#5CE07A"),   # verde
    "accent_hover": ("#166B3C", "#4AB864"),
    "accent2":      ("#9A7000", "#F4C542"),   # amarelo
    "text":         ("#1A202C", "#E8EAF0"),
    "text_dim":     ("#64748B", "#8892A4"),
    "danger":       ("#C0392B", "#E05C5C"),
    "danger_hover": ("#A02020", "#C04040"),
}

# Cores específicas por tipo de entrada
TYPE_COLORS: dict[str, tuple[str, str]] = {
    "insight":   ("#9A7000", "#F4C542"),
    "reminder":  ("#C0392B", "#E05C5C"),
    "clipboard": ("#1A6B8A", "#5CB8E0"),
    "task":      ("#1D8A4C", "#5CE07A"),
    "note":      ("#6B3FA0", "#A07AE0"),
}

# Cores de fundo das janelas de captura por tipo (usadas no quick_capture)
TYPE_BG: dict[str, str] = {
    "insight":   "#F4C542",
    "reminder":  "#E05C5C",
    "clipboard": "#5CB8E0",
    "task":      "#5CE07A",
    "note":      "#A07AE0",
}

TYPE_FG: dict[str, str] = {
    "insight":   "#1A1A2E",
    "reminder":  "#FFFFFF",
    "clipboard": "#1A1A2E",
    "task":      "#1A1A2E",
    "note":      "#FFFFFF",
}
