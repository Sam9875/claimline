"""Hiring-oriented skill lexicon.

Tags on an evidence card are an opt-in. The lexicon does not grant a skill
the candidate never recorded. Single-word aliases use word boundaries so
"storage" cannot match "rag" and "sqlite" cannot match "sql".
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    id: str
    label: str
    aliases: tuple[str, ...]


SKILLS: tuple[Skill, ...] = (
    Skill("python", "Python", ("python",)),
    Skill("sql", "SQL", ("sql",)),
    Skill("typescript", "TypeScript", ("typescript",)),
    Skill(
        "rag",
        "retrieval-augmented generation",
        ("retrieval-augmented", "retrieval augmented", "hybrid search", "vector search", "rag"),
    ),
    Skill(
        "agents",
        "agent orchestration",
        (
            "langgraph",
            "agentic",
            "agent loop",
            "tool use",
            "tool-use",
            "function calling",
            "multi-agent",
            "coding agent",
            "agent",
        ),
    ),
    Skill(
        "evals",
        "evaluation",
        ("evaluation", "evals", "eval", "promptfoo", "ragas", "faithfulness"),
    ),
    Skill(
        "guardrails",
        "guardrails",
        ("guardrails", "guardrail", "prompt injection", "jailbreak"),
    ),
    Skill("mcp", "Model Context Protocol", ("model context protocol", "mcp")),
    Skill(
        "fine_tuning",
        "fine-tuning",
        ("fine-tuning", "fine tuning", "lora", "qlora", "peft", "unsloth"),
    ),
    Skill(
        "vector_db",
        "vector databases",
        ("qdrant", "vector database", "vector db"),
    ),
    Skill(
        "recommender",
        "recommendation models",
        ("two-tower", "two tower", "recommender", "mind dataset"),
    ),
    Skill(
        "multimodal",
        "multimodal models",
        ("multimodal", "vision-language", "ego4d"),
    ),
    Skill(
        "fairness",
        "fairness evaluation",
        ("fairness", "bias audit", "demographic"),
    ),
    Skill(
        "llmops",
        "LLMOps",
        ("llmops", "mlops", "model registry", "observability"),
    ),
    Skill("docker", "Docker", ("docker",)),
    Skill("kubernetes", "Kubernetes", ("kubernetes", "k8s")),
    Skill(
        "production_ops",
        "production ownership",
        ("on-call", "production model", "production traffic"),
    ),
    Skill(
        "cloud",
        "cloud deployment",
        ("aws", "gcp", "azure", "cloud deployment"),
    ),
    Skill(
        "structured_output",
        "structured output",
        ("structured output", "json schema"),
    ),
)

_BY_ID = {skill.id: skill for skill in SKILLS}


def label_for(skill_id: str) -> str:
    skill = _BY_ID.get(skill_id)
    if skill is None:
        return skill_id.replace("_", " ")
    return skill.label


def known_skill(skill_id: str) -> bool:
    return skill_id in _BY_ID


def alias_hit_count(skill_id: str, text: str) -> int:
    skill = _BY_ID.get(skill_id)
    if skill is None:
        return 0
    return sum(1 for alias in skill.aliases if _alias_in(alias, text))


def _alias_in(alias: str, text: str) -> bool:
    if " " in alias or "-" in alias or "/" in alias:
        return alias.casefold() in text.casefold()
    return re.search(rf"\b{re.escape(alias)}\b", text, flags=re.IGNORECASE) is not None


def detect_skills(text: str) -> list[str]:
    found: list[str] = []
    for skill in SKILLS:
        if any(_alias_in(alias, text) for alias in skill.aliases):
            found.append(skill.id)
    return found
