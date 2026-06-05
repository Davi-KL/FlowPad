"""
tests/test_exporter.py
Testes unitários para o módulo de exportação.
Lógica pura — sem UI, sem Storage real.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.storage import Entry
from core.exporter import Exporter


@pytest.fixture
def sample_entries():
    return [
        Entry(
            content="Ideia sobre Python",
            title="Python",
            tags=["python", "ideia"],
            entry_type="insight",
        ),
        Entry(
            content="Fazer reunião semanal",
            title="",
            tags=["trabalho"],
            entry_type="task",
        ),
        Entry(
            content="Entrada sem tags",
            title="Sem título",
            tags=[],
            entry_type="note",
        ),
    ]


class TestExporterJSON:
    def test_json_tem_todas_entradas(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.json")
        Exporter().export(sample_entries, path, "json")
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert len(data) == 3

    def test_json_preserva_conteudo(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.json")
        Exporter().export(sample_entries, path, "json")
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data[0]["content"] == "Ideia sobre Python"
        assert data[0]["tags"] == ["python", "ideia"]

    def test_json_lista_vazia(self, tmp_path):
        path = str(tmp_path / "out.json")
        Exporter().export([], path, "json")
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data == []


class TestExporterMarkdown:
    def test_md_contem_cabecalho(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.md")
        Exporter().export(sample_entries, path, "md")
        text = Path(path).read_text(encoding="utf-8")
        assert "# FlowPad" in text

    def test_md_contem_titulo(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.md")
        Exporter().export(sample_entries, path, "md")
        text = Path(path).read_text(encoding="utf-8")
        assert "Python" in text

    def test_md_contem_tags(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.md")
        Exporter().export(sample_entries, path, "md")
        text = Path(path).read_text(encoding="utf-8")
        assert "python, ideia" in text

    def test_md_omite_linha_tags_quando_vazio(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.md")
        Exporter().export([sample_entries[2]], path, "md")  # entry sem tags
        text = Path(path).read_text(encoding="utf-8")
        assert "**Tags:**" not in text

    def test_md_contem_separadores(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.md")
        Exporter().export(sample_entries, path, "md")
        text = Path(path).read_text(encoding="utf-8")
        assert text.count("---") == 3


class TestExporterTXT:
    def test_txt_contem_cabecalho(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.txt")
        Exporter().export(sample_entries, path, "txt")
        text = Path(path).read_text(encoding="utf-8")
        assert "FlowPad" in text

    def test_txt_contem_conteudo(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.txt")
        Exporter().export(sample_entries, path, "txt")
        text = Path(path).read_text(encoding="utf-8")
        assert "Fazer reunião semanal" in text

    def test_txt_contem_tags(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.txt")
        Exporter().export(sample_entries, path, "txt")
        text = Path(path).read_text(encoding="utf-8")
        assert "Tags: trabalho" in text


class TestExporterFormato:
    def test_formato_desconhecido_usa_markdown(self, sample_entries, tmp_path):
        path = str(tmp_path / "out.xyz")
        Exporter().export(sample_entries, path, "xyz")
        text = Path(path).read_text(encoding="utf-8")
        assert "# FlowPad" in text  # caiu no md como padrão
