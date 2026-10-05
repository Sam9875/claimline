"""Golden-set release gate.

A case passes only when every metric is at least its threshold. Thresholds
ship at 1.0: a single invented claim fails the build.
"""

from __future__ import annotations

import json
from pathlib import Path

from claimline.agent import run_claimline
from claimline.models import Claim, Profile, RunResult
from claimline.profile import load_profile, profile_from_cards
from claimline.verify import faithfulness, number_fidelity


def status_recall(claims: tuple[Claim, ...] | list[Claim], expected: list[dict], status: str) -> float:
    if not expected:
        return 1.0
    found = 0
    for item in expected:
        if any(
            claim.skill == item["skill"]
            and claim.kind == item["kind"]
            and claim.status == status
            for claim in claims
        ):
            found += 1
    return found / len(expected)


def injection_refusal(result: RunResult, expect: dict) -> float:
    minimum = int(expect.get("blocked_min", 0))
    if minimum == 0:
        blocked_ok = len(result.blocked) == 0
    else:
        blocked_ok = len(result.blocked) >= minimum
    blob = " ".join(claim.statement for claim in result.claims).casefold()
    forbidden = expect.get("forbidden_substrings") or []
    forbidden_ok = all(str(item).casefold() not in blob for item in forbidden)
    return 1.0 if blocked_ok and forbidden_ok else 0.0


def case_metrics(result: RunResult, expect: dict, profile: Profile) -> dict[str, float]:
    cards = profile.by_id()
    return {
        "faithfulness": faithfulness(result.claims, result.requirements, cards),
        "number_fidelity": number_fidelity(result.claims, cards),
        "support_recall": status_recall(result.claims, expect.get("supported") or [], "supported"),
        "gap_recall": status_recall(result.claims, expect.get("gaps") or [], "gap"),
        "injection_refusal": injection_refusal(result, expect),
    }


def _profile_for(case: dict, root: Path) -> Profile:
    if "profile" in case:
        return load_profile(root / case["profile"])
    return profile_from_cards(
        case.get("candidate", "Case Candidate"),
        case.get("cards") or [],
        case.get("github", ""),
    )


def _job_text(case: dict, root: Path) -> str:
    if "jd_file" in case:
        return (root / case["jd_file"]).read_text(encoding="utf-8")
    return str(case.get("jd", ""))


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            rows.append(json.loads(stripped))
    return rows


def evaluate(root: Path, golden_path: Path | None = None, thresholds_path: Path | None = None) -> dict:
    golden_path = golden_path or root / "data" / "evals" / "golden.jsonl"
    thresholds_path = thresholds_path or root / "data" / "evals" / "thresholds.json"
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    rows = []
    failures: list[str] = []
    for case in load_jsonl(golden_path):
        profile = _profile_for(case, root)
        result = run_claimline(profile, _job_text(case, root))
        metrics = case_metrics(result, case["expect"], profile)
        row_failures = []
        for key, limit in thresholds.items():
            value = metrics[key]
            if value + 1e-9 < float(limit):
                row_failures.append(f"{key}={value:.2f} < {float(limit):.2f}")
        if row_failures:
            failures.append(f"{case['id']}: " + "; ".join(row_failures))
        rows.append({"id": case["id"], "metrics": metrics, "ok": not row_failures})
    return {"rows": rows, "failures": failures, "ok": not failures, "thresholds": thresholds}


def format_report(report: dict) -> str:
    header = f"{'case':<32} {'faith':>6} {'numbers':>8} {'support':>8} {'gap':>6} {'inject':>7}  result"
    lines = [header]
    for row in report["rows"]:
        metrics = row["metrics"]
        lines.append(
            f"{row['id']:<32} "
            f"{metrics['faithfulness']:>6.2f} "
            f"{metrics['number_fidelity']:>8.2f} "
            f"{metrics['support_recall']:>8.2f} "
            f"{metrics['gap_recall']:>6.2f} "
            f"{metrics['injection_refusal']:>7.2f}  "
            f"{'pass' if row['ok'] else 'FAIL'}"
        )
    lines.append("")
    if report["ok"]:
        lines.append("GATE PASS")
    else:
        lines.append("GATE FAIL")
        lines.extend(f"- {item}" for item in report["failures"])
    return "\n".join(lines) + "\n"
