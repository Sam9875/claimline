"""Optional wording pass through the xAI Responses API.

The model is allowed to echo claim sentences with a Covered or Gap prefix.
It is not allowed to write a new sentence. If the echo is imperfect, the
brief keeps the templates and records the rejection.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from claimline.models import Claim


# Short-context rates for grok-4.7, under 200k prompt tokens.
# https://docs.x.ai/developers/models
INPUT_USD_PER_MILLION = 2.0
OUTPUT_USD_PER_MILLION = 6.0
DEFAULT_MODEL = "grok-4.7"
API_URL = "https://api.x.ai/v1/responses"


def _squash(text: str) -> str:
    return " ".join(text.split())


def expected_lines(claims: tuple[Claim, ...] | list[Claim]) -> set[str]:
    lines = set()
    for claim in claims:
        prefix = "Covered: " if claim.status == "supported" else "Gap: "
        lines.add(prefix + _squash(claim.statement))
    return lines


def verify_prose(prose: str, claims: tuple[Claim, ...] | list[Claim]) -> bool:
    got = {_squash(line) for line in prose.splitlines() if line.strip()}
    return bool(got) and got == expected_lines(claims)


def prompt_for(claims: tuple[Claim, ...] | list[Claim]) -> str:
    lines = sorted(expected_lines(claims))
    body = "\n".join(lines)
    return (
        "Copy the following lines exactly, one per line, in any order. "
        "Do not add, delete, or reword anything.\n\n"
        f"{body}\n"
    )


def extract_output_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if isinstance(content, str):
            chunks.append(content)
            continue
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                chunks.append(str(part.get("text") or ""))
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def usage_cost(usage: dict | None) -> dict:
    if not isinstance(usage, dict):
        return {}
    incoming = usage.get("input_tokens", usage.get("prompt_tokens"))
    outgoing = usage.get("output_tokens", usage.get("completion_tokens"))
    if not isinstance(incoming, int) or not isinstance(outgoing, int):
        return {"usage": usage}
    cost = (incoming * INPUT_USD_PER_MILLION + outgoing * OUTPUT_USD_PER_MILLION) / 1_000_000
    return {
        "input_tokens": incoming,
        "output_tokens": outgoing,
        "estimated_usd": round(cost, 6),
        "rate": "grok-4.7 short-context",
    }


def rewrite(claims: tuple[Claim, ...] | list[Claim], timeout: float = 60.0) -> tuple[str | None, bool, dict]:
    key = os.environ.get("XAI_API_KEY", "").strip()
    if not key:
        return None, False, {"error": "XAI_API_KEY is not set"}
    model = os.environ.get("CLAIMLINE_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    body = json.dumps({"model": model, "input": prompt_for(claims)}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return None, False, {"error": str(exc), "model": model}
    text = extract_output_text(payload)
    accepted = verify_prose(text, claims)
    meta = usage_cost(payload.get("usage") if isinstance(payload, dict) else None)
    meta["model"] = model
    if not accepted:
        meta["rejected"] = True
    return (text if accepted else None), accepted, meta
