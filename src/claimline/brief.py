"""Markdown brief and the JSON payload the dashboard reads."""

from __future__ import annotations

from claimline.models import Profile, RunResult
from claimline.skills import label_for


def render_brief(profile: Profile, result: RunResult) -> str:
    cards = profile.by_id()
    lines: list[str] = [
        f"# {result.job_title}",
        "",
        f"Candidate: {result.candidate}",
        "",
        "This brief cites the evidence locker only. A gap is something to learn "
        "or to leave off an application. It is not a missing sentence to invent.",
        "",
        f"Verifier: faithfulness {result.checks.get('faithfulness', 0):.2f}, "
        f"number fidelity {result.checks.get('number_fidelity', 0):.2f}. "
        f"Evidence lookups {result.tool_calls} of {result.budget}.",
        "",
    ]
    if result.prose_accepted and result.prose:
        lines.extend(["## Checked wording", "", result.prose.strip(), ""])
    elif result.prose and not result.prose_accepted:
        lines.extend(
            [
                "## Checked wording",
                "",
                "A model draft was rejected because it did not match the claim "
                "sentences exactly. The sections below are the ones to use.",
                "",
            ]
        )

    covered = [claim for claim in result.claims if claim.status == "supported"]
    gaps = [claim for claim in result.claims if claim.status != "supported"]
    lines.append("## Covered")
    lines.append("")
    if not covered:
        lines.append("No requirement was covered by the evidence locker.")
        lines.append("")
    seen_cards: list[str] = []
    for claim in covered:
        if claim.card_id not in seen_cards:
            seen_cards.append(claim.card_id or "")
    for card_id in seen_cards:
        card = cards[card_id]
        mine = [claim for claim in covered if claim.card_id == card_id]
        labels = ", ".join(label_for(claim.skill) for claim in mine)
        lines.append(f"### {card.title}")
        lines.append("")
        lines.append(f"Covers: {labels}.")
        lines.append("")
        if card.url:
            lines.append(f"Link: {card.url}")
            lines.append("")
        for claim in mine:
            lines.append(f"- `{claim.requirement_id}` {claim.statement}")
        if card.does_not_prove:
            lines.append("")
            lines.append("This card does not prove:")
            for limit in card.does_not_prove:
                lines.append(f"- {limit}")
        lines.append("")

    lines.append("## Not claimed")
    lines.append("")
    if not gaps:
        lines.append("Every parsed requirement was covered.")
        lines.append("")
    for claim in gaps:
        heading = label_for(claim.skill)
        heading = heading[:1].upper() + heading[1:]
        if claim.kind == "experience_years":
            req = next(item for item in result.requirements if item.id == claim.requirement_id)
            heading = f"{req.years} years of {heading}"
        lines.append(f"### {heading}")
        lines.append("")
        lines.append(claim.statement)
        lines.append("")

    if result.unmapped:
        lines.append("## Lines that were not mapped to a skill")
        lines.append("")
        lines.append("Read these yourself. The matcher does not guess beyond its lexicon.")
        lines.append("")
        for line in result.unmapped:
            lines.append(f"- {line}")
        lines.append("")

    if result.blocked:
        lines.append("## Removed before matching")
        lines.append("")
        lines.append("These lines tried to override the evidence locker. They are not requirements.")
        lines.append("")
        for line in result.blocked:
            lines.append(f"- {line}")
        lines.append("")

    lines.append("## What the loop did")
    lines.append("")
    for event in result.trace:
        budget = "counted" if event.counted else "safety"
        lines.append(f"{event.step}. `{event.tool}` ({budget}) - {event.detail}")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_payload(profile: Profile, result: RunResult, brief: str) -> dict:
    cards = profile.by_id()
    covered = []
    gaps = []
    for claim in result.claims:
        card = cards.get(claim.card_id) if claim.card_id else None
        row = {
            "requirement_id": claim.requirement_id,
            "skill": claim.skill,
            "skill_label": label_for(claim.skill),
            "kind": claim.kind,
            "status": claim.status,
            "statement": claim.statement,
            "card_id": claim.card_id,
            "card_title": card.title if card else "",
            "url": card.url if card else "",
            "limits": list(card.does_not_prove) if card and claim.status == "supported" else [],
        }
        if claim.status == "supported":
            covered.append(row)
        else:
            gaps.append(row)
    return {
        "candidate": result.candidate,
        "github": profile.github,
        "job_title": result.job_title,
        "checks": result.checks,
        "tool_calls": result.tool_calls,
        "budget": result.budget,
        "blocked": list(result.blocked),
        "unmapped": list(result.unmapped),
        "covered": covered,
        "gaps": gaps,
        "trace": [
            {
                "step": event.step,
                "tool": event.tool,
                "detail": event.detail,
                "counted": event.counted,
            }
            for event in result.trace
        ],
        "prose_accepted": result.prose_accepted,
        "brief_markdown": brief,
    }
