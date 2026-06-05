"""
tests/test_storage.py
Testes unitários para a camada de persistência.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Ajusta o path para importar os módulos do src
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.storage import Storage, Entry, ENTRY_TYPES


@pytest.fixture
def storage(tmp_path):
    """Storage usando arquivo temporário para cada teste."""
    return Storage(str(tmp_path / "test_entries.json"))


class TestEntry:
    def test_create_entry_defaults(self):
        e = Entry(content="Minha ideia")
        assert e.content == "Minha ideia"
        assert e.entry_type == "insight"
        assert e.archived is False
        assert e.id is not None

    def test_invalid_type_falls_back_to_insight(self):
        e = Entry(content="Teste", entry_type="invalido")
        assert e.entry_type == "insight"

    def test_serialization_roundtrip(self):
        e = Entry(content="Teste", title="Título", tags=["python", "ideia"])
        d = e.to_dict()
        e2 = Entry.from_dict(d)
        assert e2.content == e.content
        assert e2.title == e.title
        assert e2.tags == e.tags
        assert e2.id == e.id


class TestStorage:
    def test_save_and_retrieve(self, storage):
        entry = Entry(content="Primeira ideia", entry_type="insight")
        storage.save(entry)
        all_entries = storage.get_all()
        assert len(all_entries) == 1
        assert all_entries[0].content == "Primeira ideia"

    def test_get_recent_returns_newest_first(self, storage):
        for i in range(5):
            storage.save(Entry(content=f"Entrada {i}"))
        recent = storage.get_recent(3)
        assert len(recent) == 3
        assert recent[0].content == "Entrada 4"  # Mais recente

    def test_archive_hides_entry(self, storage):
        entry = storage.save(Entry(content="Para arquivar"))
        storage.archive(entry.id)
        assert len(storage.get_all()) == 0
        assert len(storage.get_all(include_archived=True)) == 1

    def test_delete_removes_entry(self, storage):
        entry = storage.save(Entry(content="Para deletar"))
        result = storage.delete(entry.id)
        assert result is True
        assert len(storage.get_all()) == 0

    def test_search_finds_by_content(self, storage):
        storage.save(Entry(content="Python é incrível"))
        storage.save(Entry(content="JavaScript também"))
        results = storage.search("python")
        assert len(results) == 1
        assert "Python" in results[0].content

    def test_update_modifies_entry(self, storage):
        entry = storage.save(Entry(content="Original"))
        entry.content = "Modificado"
        storage.update(entry)
        found = storage.get_all()[0]
        assert found.content == "Modificado"

    def test_get_by_type(self, storage):
        storage.save(Entry(content="Insight 1", entry_type="insight"))
        storage.save(Entry(content="Lembrete 1", entry_type="reminder"))
        insights = storage.get_by_type("insight")
        assert len(insights) == 1

    def test_empty_storage_returns_empty_list(self, storage):
        assert storage.get_all() == []

    def test_completed_defaults_to_false(self, storage):
        entry = storage.save(Entry(content="Tarefa nova", entry_type="task"))
        assert entry.completed is False

    def test_toggle_completed_marks_done(self, storage):
        entry = storage.save(Entry(content="Tarefa", entry_type="task"))
        result = storage.toggle_completed(entry.id)
        assert result is True
        updated = storage.get_all()[0]
        assert updated.completed is True

    def test_toggle_completed_twice_returns_false(self, storage):
        entry = storage.save(Entry(content="Tarefa", entry_type="task"))
        storage.toggle_completed(entry.id)
        storage.toggle_completed(entry.id)
        updated = storage.get_all()[0]
        assert updated.completed is False

    def test_completed_roundtrip(self):
        e = Entry(content="Done", entry_type="task", completed=True)
        e2 = Entry.from_dict(e.to_dict())
        assert e2.completed is True
