"""
core/storage.py
Camada de persistência do FlowPad.
Armazena todas as entradas em JSON local — sem dependência de banco de dados.
Escolha intencional para facilitar portabilidade e contribuição open source.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


# Tipos de entrada suportados
ENTRY_TYPES = {
    "insight": {"label": "💡 Insight", "color": "#F4C542"},
    "reminder": {"label": "⏰ Lembrete", "color": "#E05C5C"},
    "clipboard": {"label": "📋 Clipboard", "color": "#5CB8E0"},
    "task": {"label": "✅ Tarefa", "color": "#5CE07A"},
    "note": {"label": "📝 Nota", "color": "#A07AE0"},
}


class Entry:
    """Representa uma entrada salva no FlowPad."""

    def __init__(
        self,
        content: str,
        entry_type: str = "insight",
        title: str = "",
        tags: list[str] | None = None,
        reminder_at: str | None = None,
        reminder_interval_min: int | None = None,
        entry_id: str | None = None,
        created_at: str | None = None,
        archived: bool = False,
        completed: bool = False,
    ):
        self.id = entry_id or str(uuid.uuid4())
        self.content = content
        self.title = title
        self.entry_type = entry_type if entry_type in ENTRY_TYPES else "insight"
        self.tags = tags or []
        self.reminder_at = reminder_at  # ISO datetime string
        self.reminder_interval_min = reminder_interval_min  # repetição em minutos
        self.created_at = created_at or datetime.now().isoformat()
        self.archived = archived
        self.completed = completed

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "title": self.title,
            "entry_type": self.entry_type,
            "tags": self.tags,
            "reminder_at": self.reminder_at,
            "reminder_interval_min": self.reminder_interval_min,
            "created_at": self.created_at,
            "archived": self.archived,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        return cls(
            content=data.get("content", ""),
            entry_type=data.get("entry_type", "insight"),
            title=data.get("title", ""),
            tags=data.get("tags", []),
            reminder_at=data.get("reminder_at"),
            reminder_interval_min=data.get("reminder_interval_min"),
            entry_id=data.get("id"),
            created_at=data.get("created_at"),
            archived=data.get("archived", False),
            completed=data.get("completed", False),
        )


class Storage:
    """
    Gerencia leitura e escrita das entradas em arquivo JSON.
    Thread-safe para uso com hotkeys em threads separadas.
    """

    def __init__(self, data_path: str):
        self.path = Path(data_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        """Cria o arquivo de dados se não existir."""
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[dict]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write(self, entries: list[dict]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save(self, entry: Entry) -> Entry:
        """Salva uma nova entrada."""
        entries = self._read()
        entries.insert(0, entry.to_dict())  # Mais recente primeiro
        self._write(entries)
        return entry

    def get_all(self, include_archived: bool = False) -> list[Entry]:
        """Retorna todas as entradas, opcionalmente incluindo arquivadas."""
        data = self._read()
        entries = [Entry.from_dict(d) for d in data]
        if not include_archived:
            entries = [e for e in entries if not e.archived]
        return entries

    def get_by_type(self, entry_type: str) -> list[Entry]:
        return [e for e in self.get_all() if e.entry_type == entry_type]

    def get_reminders_due(self) -> list[Entry]:
        """Retorna lembretes cujo horário chegou."""
        now = datetime.now()
        due = []
        for entry in self.get_all():
            if entry.reminder_at:
                try:
                    reminder_time = datetime.fromisoformat(entry.reminder_at)
                    if reminder_time <= now:
                        due.append(entry)
                except ValueError:
                    pass
        return due

    def update(self, entry: Entry) -> bool:
        """Atualiza uma entrada existente pelo ID."""
        entries = self._read()
        for i, e in enumerate(entries):
            if e["id"] == entry.id:
                entries[i] = entry.to_dict()
                self._write(entries)
                return True
        return False

    def delete(self, entry_id: str) -> bool:
        """Remove uma entrada permanentemente."""
        entries = self._read()
        filtered = [e for e in entries if e["id"] != entry_id]
        if len(filtered) < len(entries):
            self._write(filtered)
            return True
        return False

    def archive(self, entry_id: str) -> bool:
        """Arquiva (soft delete) uma entrada."""
        entries = self._read()
        for e in entries:
            if e["id"] == entry_id:
                e["archived"] = True
                self._write(entries)
                return True
        return False

    def search(self, query: str) -> list[Entry]:
        """Busca por conteúdo ou título (case-insensitive)."""
        q = query.lower()
        return [
            e for e in self.get_all()
            if q in e.content.lower() or q in e.title.lower()
        ]

    def get_recent(self, limit: int = 10) -> list[Entry]:
        """Retorna as N entradas mais recentes."""
        return self.get_all()[:limit]

    def toggle_completed(self, entry_id: str) -> bool:
        """Alterna o estado de conclusão de uma tarefa."""
        entries = self._read()
        for e in entries:
            if e["id"] == entry_id:
                e["completed"] = not e.get("completed", False)
                self._write(entries)
                return True
        return False
