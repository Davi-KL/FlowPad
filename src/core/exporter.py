"""
core/exporter.py
Exporta entradas do FlowPad para diferentes formatos de arquivo.
Lógica pura — sem dependência de UI ou Storage.
"""

import json
from datetime import datetime
from pathlib import Path

from core.storage import Entry, ENTRY_TYPES


class Exporter:
    """Converte uma lista de entradas para .md, .txt ou .json e grava em disco."""

    def export(self, entries: list[Entry], path: str, fmt: str) -> None:
        """
        Exporta entries para o arquivo em path, no formato fmt ('md', 'txt', 'json').
        """
        if fmt == "json":
            content = self._to_json(entries)
        elif fmt == "txt":
            content = self._to_txt(entries)
        else:
            content = self._to_markdown(entries)

        Path(path).write_text(content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Formatos
    # ------------------------------------------------------------------

    def _to_json(self, entries: list[Entry]) -> str:
        return json.dumps([e.to_dict() for e in entries], ensure_ascii=False, indent=2)

    def _to_markdown(self, entries: list[Entry]) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [f"# FlowPad — Exportação em {ts}", ""]

        for entry in entries:
            meta = ENTRY_TYPES.get(entry.entry_type, {})
            label = meta.get("label", "📝 Nota")
            titulo = entry.title or entry.content[:60].replace("\n", " ")
            data = entry.created_at[:16].replace("T", " ")

            lines.append(f"## {label} {titulo}")
            lines.append(f"**Data:** {data}")
            if entry.tags:
                lines.append(f"**Tags:** {', '.join(entry.tags)}")
            lines.append("")
            lines.append(entry.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _to_txt(self, entries: list[Entry]) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        sep = "=" * 60
        lines = [f"FlowPad — Exportação em {ts}", sep, ""]

        for entry in entries:
            meta = ENTRY_TYPES.get(entry.entry_type, {})
            label = meta.get("label", "Nota")
            titulo = entry.title or entry.content[:60].replace("\n", " ")
            data = entry.created_at[:16].replace("T", " ")

            lines.append(f"[{label}] {titulo}")
            lines.append(f"Data: {data}")
            if entry.tags:
                lines.append(f"Tags: {', '.join(entry.tags)}")
            lines.append("")
            lines.append(entry.content)
            lines.append("")
            lines.append("-" * 40)
            lines.append("")

        return "\n".join(lines)
