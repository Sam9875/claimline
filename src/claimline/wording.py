"""Claim sentences.

Every sentence is a template filled from one card, or a fixed gap sentence.
Nothing in this module is allowed to introduce a number that did not arrive
on the card or, for a duration gap, on the job line.
"""

from __future__ import annotations

from claimline.models import EvidenceCard, Requirement
from claimline.skills import label_for


def _squash(text: str) -> str:
    return " ".join(text.split())


def _summary(card: EvidenceCard) -> str:
    summary = card.summary.strip()
    if summary and not summary.endswith((".", "!", "?")):
        summary += "."
    return summary


def supported_statement(req: Requirement, card: EvidenceCard) -> str:
    extra = ""
    if card.metrics:
        rendered = "; ".join(f"{key}={value}" for key, value in card.metrics)
        extra = f" Recorded figures: {rendered}."
    return _squash(
        f"{card.title} [{card.id}] is evidence for {label_for(req.skill)}. "
        f"{_summary(card)}{extra}"
    )


def years_statement(req: Requirement, card: EvidenceCard | None, skill_count: int = 0) -> str:
    label = label_for(req.skill)
    if card is None or skill_count <= 0:
        return _squash(
            f"No evidence card lists {label}. "
            f"The request of {req.years} years is not claimed."
        )
    if skill_count == 1:
        return _squash(
            f"{card.title} [{card.id}] shows {label} work. "
            f"No evidence card records {req.years} years, so that duration is not claimed."
        )
    return _squash(
        f"{skill_count} evidence cards list {label}, including {card.title} [{card.id}]. "
        f"No evidence card records {req.years} years, so that duration is not claimed."
    )


def gap_statement(req: Requirement) -> str:
    return (
        f"No evidence card lists {label_for(req.skill)}. "
        "This requirement stays a gap."
    )


def unreviewed_statement(req: Requirement) -> str:
    return _squash(
        f"{label_for(req.skill)} was not reviewed because the tool-call budget "
        "was exhausted. It is not claimed."
    )


def statement_for(
    req: Requirement,
    status: str,
    card: EvidenceCard | None,
    skill_count: int = 0,
) -> str:
    if status == "unreviewed":
        return unreviewed_statement(req)
    if req.kind == "experience_years":
        return years_statement(req, card, skill_count)
    if status == "supported":
        if card is None:
            raise ValueError("a supported claim needs a card")
        return supported_statement(req, card)
    return gap_statement(req)
