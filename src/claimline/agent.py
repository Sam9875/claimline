"""Bounded evidence loop.

Injection screening and the citation verifier always run. The budget only
limits evidence lookups, so a short budget cannot skip the safety checks and
it cannot leave a half-cited claim marked supported.
"""

from __future__ import annotations

from claimline.index import search_cards
from claimline.jd import parse_job
from claimline.models import Claim, Profile, Requirement, RunResult, TraceEvent
from claimline.verify import score_claims
from claimline.wording import statement_for


def _claim(
    req: Requirement,
    status: str,
    card_id: str | None,
    profile: Profile,
    skill_count: int = 0,
) -> Claim:
    card = profile.by_id().get(card_id) if card_id else None
    return Claim(
        requirement_id=req.id,
        kind=req.kind,
        skill=req.skill,
        status=status,
        card_id=card_id,
        statement=statement_for(req, status, card, skill_count),
    )


def run_claimline(profile: Profile, jd_text: str, max_tool_calls: int = 64) -> RunResult:
    if max_tool_calls < 0:
        raise ValueError("max_tool_calls must be zero or greater")
    parsed = parse_job(jd_text)
    trace: list[TraceEvent] = []

    def record(tool: str, detail: str, counted: bool) -> None:
        trace.append(TraceEvent(len(trace) + 1, tool, detail, counted))

    record("screen_job", f"blocked={len(parsed.blocked)}", False)
    record(
        "parse_requirements",
        f"requirements={len(parsed.requirements)} unmapped={len(parsed.unmapped)}",
        False,
    )

    claims: list[Claim] = []
    used = 0

    def spend(tool: str, detail: str) -> bool:
        nonlocal used
        if used >= max_tool_calls:
            return False
        used += 1
        record(tool, detail, True)
        return True

    for req in parsed.requirements:
        if used >= max_tool_calls:
            claims.append(_claim(req, "unreviewed", None, profile))
            continue
        skill = None if req.skill == "unspecified" else req.skill
        if not spend("search_evidence", f"{req.id} skill={req.skill}"):
            claims.append(_claim(req, "unreviewed", None, profile))
            continue
        hits = search_cards(profile.cards, req.text, skill, limit=3)
        top = hits[0][0] if hits else None
        hit_note = top.id if top else "none"
        trace[-1] = TraceEvent(
            trace[-1].step,
            trace[-1].tool,
            f"{req.id} skill={req.skill} top={hit_note} hits={len(hits)}",
            True,
        )
        if top is not None:
            if not spend("read_card", f"{req.id} card={top.id}"):
                claims.append(_claim(req, "unreviewed", None, profile))
                continue
        if not spend("commit_claim", f"{req.id} card={top.id if top else 'none'}"):
            claims.append(_claim(req, "unreviewed", None, profile))
            continue
        if req.kind == "experience_years":
            if req.skill == "unspecified":
                claims.append(_claim(req, "gap", None, profile, 0))
            else:
                skill_count = sum(1 for card in profile.cards if req.skill in card.skills)
                claims.append(_claim(req, "gap", top.id if top else None, profile, skill_count))
            continue
        if top is None or req.skill not in top.skills:
            claims.append(_claim(req, "gap", None, profile))
            continue
        claims.append(_claim(req, "supported", top.id, profile))

    checks = score_claims(claims, parsed.requirements, profile.by_id())
    record(
        "verify_claims",
        "faithfulness={faithfulness:.2f} number_fidelity={number_fidelity:.2f}".format(
            **checks
        ),
        False,
    )
    return RunResult(
        candidate=profile.candidate,
        job_title=parsed.title,
        requirements=parsed.requirements,
        claims=tuple(claims),
        blocked=parsed.blocked,
        unmapped=parsed.unmapped,
        trace=tuple(trace),
        tool_calls=used,
        budget=max_tool_calls,
        checks=checks,
    )
