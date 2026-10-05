"""Rank evidence cards that already carry a required skill.

Skill membership decides whether a card may be cited. BM25 only orders that
pool. Ties break on card id so a run is repeatable.
"""

from __future__ import annotations

import math
import re

from claimline.models import EvidenceCard


_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.casefold())


def card_text(card: EvidenceCard) -> str:
    metrics = " ".join(f"{key} {value}" for key, value in card.metrics)
    skills = " ".join(card.skills)
    return f"{card.title} {skills} {card.summary} {metrics}"


def search_cards(
    cards: tuple[EvidenceCard, ...] | list[EvidenceCard],
    query: str,
    skill: str | None,
    limit: int = 3,
) -> list[tuple[EvidenceCard, float]]:
    pool = [card for card in cards if skill is None or skill in card.skills]
    if not pool:
        return []
    docs = [tokenize(card_text(card)) for card in pool]
    query_tokens = tokenize(query)
    average = sum(len(doc) for doc in docs) / len(docs)
    document_frequency: dict[str, int] = {}
    for doc in docs:
        for token in set(doc):
            document_frequency[token] = document_frequency.get(token, 0) + 1
    k1 = 1.5
    b = 0.75
    ranked: list[tuple[float, str, EvidenceCard]] = []
    total = len(docs)
    for card, doc in zip(pool, docs):
        counts: dict[str, int] = {}
        for token in doc:
            counts[token] = counts.get(token, 0) + 1
        score = 0.0
        for token in query_tokens:
            if token not in counts:
                continue
            df = document_frequency[token]
            idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
            freq = counts[token]
            denom = freq + k1 * (1 - b + b * (len(doc) / average if average else 1))
            score += idf * (freq * (k1 + 1)) / denom
        ranked.append((score, card.id, card))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    return [(card, score) for score, _card_id, card in ranked[:limit]]
