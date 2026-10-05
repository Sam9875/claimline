"""Data the rest of Claimline passes around.

Claims are the only sentences that may describe the candidate. A supported
claim points at one evidence card. A gap claim points at nothing, even when a
related card is mentioned as context.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceCard:
    id: str
    title: str
    url: str
    skills: tuple[str, ...]
    summary: str
    metrics: tuple[tuple[str, str], ...] = ()
    does_not_prove: tuple[str, ...] = ()


@dataclass(frozen=True)
class Profile:
    candidate: str
    cards: tuple[EvidenceCard, ...]
    github: str = ""
    note: str = ""

    def by_id(self) -> dict[str, EvidenceCard]:
        return {card.id: card for card in self.cards}


@dataclass(frozen=True)
class Requirement:
    id: str
    kind: str  # "skill" or "experience_years"
    skill: str
    text: str
    years: int | None = None


@dataclass(frozen=True)
class Claim:
    requirement_id: str
    kind: str
    skill: str
    status: str  # "supported", "gap", "unreviewed"
    statement: str
    card_id: str | None = None


@dataclass(frozen=True)
class TraceEvent:
    step: int
    tool: str
    detail: str
    counted: bool


@dataclass
class RunResult:
    candidate: str
    job_title: str
    requirements: tuple[Requirement, ...]
    claims: tuple[Claim, ...]
    blocked: tuple[str, ...]
    unmapped: tuple[str, ...]
    trace: tuple[TraceEvent, ...]
    tool_calls: int
    budget: int
    checks: dict[str, float] = field(default_factory=dict)
    prose: str | None = None
    prose_accepted: bool = False
