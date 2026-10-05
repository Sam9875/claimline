"""Fail-closed checks for a finished run.

Faithfulness is template lock plus skill membership. A sentence that merely
mentions a real project still fails if it is not the sentence the template
would have written.
"""

from __future__ import annotations

import re

from claimline.models import Claim, EvidenceCard, Requirement
from claimline.wording import statement_for


_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def card_blob(card: EvidenceCard) -> str:
    metrics = " ".join(f"{key} {value}" for key, value in card.metrics)
    return " ".join((card.id, card.title, card.url, card.summary, metrics))


def numbers_in(text: str) -> list[str]:
    return _NUMBER.findall(text)


def faithfulness(
    claims: tuple[Claim, ...] | list[Claim],
    requirements: tuple[Requirement, ...] | list[Requirement],
    cards: dict[str, EvidenceCard],
) -> float:
    by_id = {req.id: req for req in requirements}
    supported = [claim for claim in claims if claim.status == "supported"]
    if not supported:
        return 1.0
    good = 0
    for claim in supported:
        # A duration is not a skill the locker can prove. There is no years field.
        if claim.kind == "experience_years":
            continue
        card = cards.get(claim.card_id or "")
        req = by_id.get(claim.requirement_id)
        if card is None or req is None or claim.skill not in card.skills:
            continue
        if claim.statement == statement_for(req, "supported", card):
            good += 1
    return good / len(supported)


def number_fidelity(
    claims: tuple[Claim, ...] | list[Claim],
    cards: dict[str, EvidenceCard],
) -> float:
    supported = [claim for claim in claims if claim.status == "supported"]
    if not supported:
        return 1.0
    good = 0
    for claim in supported:
        card = cards.get(claim.card_id or "")
        if card is None:
            continue
        allowed = set(numbers_in(card_blob(card)))
        if all(number in allowed for number in numbers_in(claim.statement)):
            good += 1
    return good / len(supported)


def score_claims(
    claims: tuple[Claim, ...] | list[Claim],
    requirements: tuple[Requirement, ...] | list[Requirement],
    cards: dict[str, EvidenceCard],
) -> dict[str, float]:
    return {
        "faithfulness": faithfulness(claims, requirements, cards),
        "number_fidelity": number_fidelity(claims, cards),
    }
