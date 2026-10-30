"""Deterministic schema retrieval: the offline, explainable RAG-inspired layer."""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def _variants(value: str) -> set[str]:
    value = value.lower()
    forms = {value, value.replace("_", " ")}
    if value.endswith("s"): forms.add(value[:-1])
    else: forms.add(value + "s")
    return forms


def retrieve_columns(query: str, columns: list[dict], limit: int = 5) -> list[dict]:
    query_words = _words(query)
    ranked = []
    for column in columns:
        name = column["name"]
        variants = _variants(name)
        overlap = max((len(query_words & _words(item)) for item in variants), default=0)
        similarity = max(SequenceMatcher(None, word, name).ratio() for word in query_words) if query_words else 0
        score = overlap * 10 + round(similarity, 2)
        if score > 0.4:
            ranked.append({**column, "score": score, "reason": "keyword match" if overlap else "name similarity"})
    return sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]


def resolve_column(phrase: str, columns: list[dict]) -> str | None:
    target = phrase.strip().lower().replace(" ", "_")
    exact = {column["name"]: column["name"] for column in columns}
    if target in exact: return exact[target]
    for column in columns:
        if target in _variants(column["name"]): return column["name"]
    ranked = retrieve_columns(phrase, columns, limit=1)
    return ranked[0]["name"] if ranked and ranked[0]["score"] >= 0.72 else None
