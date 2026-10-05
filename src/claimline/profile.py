"""Load the evidence locker.

The note field is instructions for the human editor. It is not indexed and it
cannot support a claim.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from claimline.models import EvidenceCard, Profile
from claimline.skills import known_skill


class ProfileError(ValueError):
    pass


_ID = __import__("re").compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _as_tuple(value, card_id: str, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProfileError(f"{card_id}: {field} must be a list of strings")
    return tuple(item.strip() for item in value if item.strip())


def card_from_dict(raw: dict) -> EvidenceCard:
    if not isinstance(raw, dict):
        raise ProfileError("each evidence entry must be a mapping")
    card_id = str(raw.get("id", "")).strip()
    if not _ID.match(card_id):
        raise ProfileError(f"invalid card id: {card_id!r}")
    title = str(raw.get("title", "")).strip()
    summary = str(raw.get("summary", "")).strip()
    if not title or not summary:
        raise ProfileError(f"{card_id}: title and summary are required")
    skills = _as_tuple(raw.get("skills"), card_id, "skills")
    if not skills:
        raise ProfileError(f"{card_id}: list at least one skill")
    unknown = [skill for skill in skills if not known_skill(skill)]
    if unknown:
        raise ProfileError(f"{card_id}: unknown skills {unknown}")
    metrics_raw = raw.get("metrics") or {}
    if not isinstance(metrics_raw, dict):
        raise ProfileError(f"{card_id}: metrics must be a mapping")
    metrics = tuple((str(key), str(value)) for key, value in metrics_raw.items())
    return EvidenceCard(
        id=card_id,
        title=title,
        url=str(raw.get("url", "")).strip(),
        skills=skills,
        summary=" ".join(summary.split()),
        metrics=metrics,
        does_not_prove=_as_tuple(raw.get("does_not_prove"), card_id, "does_not_prove"),
    )


def profile_from_dict(raw: dict) -> Profile:
    if not isinstance(raw, dict):
        raise ProfileError("profile must be a mapping")
    candidate = str(raw.get("candidate", "")).strip()
    if not candidate:
        raise ProfileError("candidate name is required")
    entries = raw.get("evidence")
    if not isinstance(entries, list) or not entries:
        raise ProfileError("evidence must be a non-empty list")
    cards = tuple(card_from_dict(entry) for entry in entries)
    ids = [card.id for card in cards]
    if len(ids) != len(set(ids)):
        raise ProfileError("evidence card ids must be unique")
    return Profile(
        candidate=candidate,
        github=str(raw.get("github", "")).strip(),
        note=" ".join(str(raw.get("note", "")).split()),
        cards=cards,
    )


def profile_from_cards(candidate: str, cards: list[dict], github: str = "") -> Profile:
    return profile_from_dict(
        {"candidate": candidate, "github": github, "evidence": cards}
    )


def load_profile(path: Path) -> Profile:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProfileError(f"cannot read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ProfileError(f"invalid YAML in {path}: {exc}") from exc
    return profile_from_dict(raw)
