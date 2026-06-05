"""
tests/test_utils.py
Testes unitários para utilitários: busca fuzzy.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.fuzzy import fuzzy_match


class TestFuzzyMatch:
    def test_empty_query_always_matches(self):
        assert fuzzy_match("", "qualquer texto") is True
        assert fuzzy_match("", "") is True

    def test_exact_substring_match(self):
        assert fuzzy_match("python", "aprendo python hoje") is True

    def test_case_insensitive_match(self):
        assert fuzzy_match("PYTHON", "aprendo python hoje") is True
        assert fuzzy_match("python", "PYTHON É INCRÍVEL") is True

    def test_no_match(self):
        assert fuzzy_match("xyz123abc", "texto completamente diferente") is False

    def test_similar_word_matches(self):
        # "phyton" tem similaridade suficiente com "python"
        assert fuzzy_match("phyton", "aprendo python hoje") is True

    def test_full_match_same_string(self):
        assert fuzzy_match("insight", "insight") is True

    def test_multiword_query_substring(self):
        assert fuzzy_match("cache lru", "implementar cache lru no storage") is True

    def test_very_different_strings(self):
        assert fuzzy_match("abcdef", "xyz") is False
