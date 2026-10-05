"""Turn a job description into requirements and a list of lines we will not score.

Only lexicon skills and digit-denoted years become requirements. Everything
else that still looks like a sentence is returned as unmapped, so a custom
ask is not silently dropped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from claimline.injection import is_injection
from claimline.models import Requirement
from claimline.skills import alias_hit_count, detect_skills


_YEARS = re.compile(r"\b(\d+)\s*\+?\s*years?\b", re.IGNORECASE)
_UNMAPPED_MIN = 28


@dataclass(frozen=True)
class ParsedJob:
    title: str
    requirements: tuple[Requirement, ...]
    blocked: tuple[str, ...]
    unmapped: tuple[str, ...]


def job_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return "Job brief"


def parse_job(text: str) -> ParsedJob:
    blocked: list[str] = []
    kept: list[str] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        cleaned = raw.lstrip("-*• ").strip()
        if not cleaned:
            continue
        if is_injection(cleaned):
            blocked.append(cleaned)
            continue
        kept.append(cleaned)

    requirements: list[Requirement] = []
    unmapped: list[str] = []
    best: dict[tuple[str, str, int | None], tuple[int, int]] = {}
    for line in kept:
        skills = detect_skills(line)
        years_match = _YEARS.search(line)
        years = int(years_match.group(1)) if years_match else None
        if not skills and years is None:
            if len(line) >= _UNMAPPED_MIN and not line.endswith(":"):
                unmapped.append(line)
            continue
        if years is not None and skills:
            targets = [("experience_years", skill, years) for skill in skills]
        elif years is not None:
            targets = [("experience_years", "unspecified", years)]
        else:
            targets = [("skill", skill, None) for skill in skills]
        for kind, skill, yrs in targets:
            key = (kind, skill, yrs)
            hits = alias_hit_count(skill, line)
            if key in best:
                index, previous_hits = best[key]
                if hits > previous_hits:
                    current = requirements[index]
                    requirements[index] = Requirement(current.id, kind, skill, line, yrs)
                    best[key] = (index, hits)
                continue
            requirements.append(
                Requirement(
                    id=f"req-{len(requirements) + 1:02d}",
                    kind=kind,
                    skill=skill,
                    text=line,
                    years=yrs,
                )
            )
            best[key] = (len(requirements) - 1, hits)
    return ParsedJob(
        title=job_title(text),
        requirements=tuple(requirements),
        blocked=tuple(blocked),
        unmapped=tuple(unmapped),
    )
