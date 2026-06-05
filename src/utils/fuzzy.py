"""
utils/fuzzy.py
Correspondência aproximada para busca nas visões do dashboard.
"""
from difflib import SequenceMatcher


def fuzzy_match(query: str, text: str) -> bool:
    """
    Retorna True se query corresponde aproximadamente a text.
    Estratégia:
      1. Substring exata (case-insensitive).
      2. Similaridade palavra-a-palavra — útil para erros de digitação.
      3. Similaridade global query vs texto completo.
    """
    if not query:
        return True
    q, t = query.lower(), text.lower()
    if q in t:
        return True
    # Compara a query contra cada palavra do texto (bom para typos)
    for word in t.split():
        if SequenceMatcher(None, q, word).ratio() > 0.7:
            return True
    return SequenceMatcher(None, q, t).ratio() > 0.6
