"""Command line for briefs, the study list, the eval gate, and the MCP server."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from claimline.agent import run_claimline
from claimline.brief import export_payload, render_brief
from claimline.evals import evaluate, format_report
from claimline.market import practice_for, render_market
from claimline.mcp_server import serve
from claimline.models import RunResult, TraceEvent
from claimline.profile import ProfileError, load_profile
from claimline.prose import rewrite
from claimline.skills import label_for


def _root_and_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    root = Path.cwd()
    profile_path = Path(args.profile) if getattr(args, "profile", None) else root / "data" / "profile.yaml"
    return root, profile_path


def _read_jd(args: argparse.Namespace) -> str:
    if getattr(args, "jd", None):
        return Path(args.jd).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("pass --jd PATH, or pipe a job description on stdin")


def _run(args: argparse.Namespace):
    _root, profile_path = _root_and_paths(args)
    try:
        profile = load_profile(profile_path)
    except ProfileError as exc:
        raise SystemExit(str(exc)) from exc
    jd_text = _read_jd(args)
    result = run_claimline(profile, jd_text, max_tool_calls=args.budget)
    if args.live:
        prose, accepted, meta = rewrite(result.claims)
        result.prose = prose
        result.prose_accepted = accepted
        detail = "accepted" if accepted else "rejected"
        if "error" in meta:
            detail = str(meta["error"])
        elif meta.get("estimated_usd") is not None:
            detail = f"{detail} usd={meta['estimated_usd']} model={meta.get('model', '')}"
        result.trace = result.trace + (TraceEvent(len(result.trace) + 1, "prose", detail, False),)
    return profile, result


def _verifier_failed(result: RunResult) -> bool:
    return result.checks.get("faithfulness", 0) < 1 or result.checks.get("number_fidelity", 0) < 1


def cmd_brief(args: argparse.Namespace) -> int:
    profile, result = _run(args)
    brief = render_brief(profile, result)
    payload = export_payload(profile, result, brief)
    out = Path(args.out) if args.out else Path("runs") / "brief.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(brief, encoding="utf-8")
    json_path = out.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    sys.stdout.write(brief)
    if _verifier_failed(result):
        sys.stderr.write("Verifier failed. Do not send this brief.\n")
        return 2
    return 0


def render_study(profile, result: RunResult) -> str:
    cards = profile.by_id()
    lines = [f"Study notes for {result.job_title}", ""]
    for claim in result.claims:
        label = label_for(claim.skill)
        label = label[:1].upper() + label[1:]
        if claim.status == "supported":
            card = cards[claim.card_id]
            limit = card.does_not_prove[0] if card.does_not_prove else "the limits written on the card"
            lines.append(f"COVERED  {label}")
            lines.append(f"  {card.title}. Be ready to explain this limit: {limit}")
        else:
            lines.append(f"GAP      {label}")
            lines.append(f"  {practice_for(claim.skill)}")
        lines.append("")
    if result.unmapped:
        lines.append("Read these lines yourself. They were not mapped to a skill:")
        for line in result.unmapped:
            lines.append(f"  - {line}")
        lines.append("")
    if result.blocked:
        lines.append("Do not treat these lines as requirements:")
        for line in result.blocked:
            lines.append(f"  - {line}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_study(args: argparse.Namespace) -> int:
    profile, result = _run(args)
    sys.stdout.write(render_study(profile, result))
    return 2 if _verifier_failed(result) else 0


def cmd_eval(args: argparse.Namespace) -> int:
    root = Path.cwd()
    golden = Path(args.golden) if args.golden else None
    report = evaluate(root, golden)
    sys.stdout.write(format_report(report))
    return 0 if report["ok"] else 1


def cmd_market(_args: argparse.Namespace) -> int:
    sys.stdout.write(render_market())
    return 0


def cmd_mcp(_args: argparse.Namespace) -> int:
    return serve()


def cmd_export(args: argparse.Namespace) -> int:
    profile, result = _run(args)
    brief = render_brief(profile, result)
    if _verifier_failed(result):
        sys.stderr.write("Verifier failed. Dashboard export withheld.\n")
        return 2
    payload = export_payload(profile, result, brief)
    dashboard = Path(args.dashboard)
    examples = Path(args.examples)
    dashboard.parent.mkdir(parents=True, exist_ok=True)
    examples.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2)
    dashboard.write_text("window.CLAIMLINE_SAMPLE = " + encoded + ";\n", encoding="utf-8")
    examples.joinpath("applied-ai-engineer.md").write_text(brief, encoding="utf-8")
    examples.joinpath("applied-ai-engineer.json").write_text(encoded + "\n", encoding="utf-8")
    sys.stdout.write(f"wrote {dashboard}\n")
    sys.stdout.write(f"wrote {examples}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claimline", description="Evidence-locked job briefs.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_job_flags(command: argparse.ArgumentParser) -> None:
        command.add_argument("--jd", help="Path to a job description text file.")
        command.add_argument("--profile", help="Evidence locker YAML. Defaults to data/profile.yaml.")
        command.add_argument("--budget", type=int, default=64, help="Maximum evidence-tool calls.")
        command.add_argument(
            "--live",
            action="store_true",
            help="Ask grok-4.7 to echo the claim lines. Reject the draft if any word changes.",
        )

    brief = sub.add_parser("brief", help="Write a markdown brief and a JSON payload.")
    add_job_flags(brief)
    brief.add_argument("--out", help="Markdown output path. Defaults to runs/brief.md.")
    brief.set_defaults(func=cmd_brief)

    study = sub.add_parser("study", help="Turn gaps into practice tasks.")
    add_job_flags(study)
    study.set_defaults(func=cmd_study)

    gate = sub.add_parser("eval", help="Run the golden set. Exit 1 when the gate fails.")
    gate.add_argument("--golden", help="Override data/evals/golden.jsonl.")
    gate.set_defaults(func=cmd_eval)

    market = sub.add_parser("market", help="Print the hiring notes behind the project.")
    market.set_defaults(func=cmd_market)

    mcp = sub.add_parser("mcp", help="Serve read-only tools over stdio MCP.")
    mcp.set_defaults(func=cmd_mcp)

    export = sub.add_parser("export", help="Refresh the dashboard sample and examples/.")
    add_job_flags(export)
    export.add_argument("--dashboard", default="dashboard/sample-run.js")
    export.add_argument("--examples", default="examples")
    export.set_defaults(func=cmd_export)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
