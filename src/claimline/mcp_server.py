"""Minimal Model Context Protocol server over stdio.

Tools are read-only. A client can list evidence, search it, screen a job
description, and build a brief. It cannot write a claim sentence of its own.
Newline-delimited JSON is the default framing. Content-Length framing is
accepted so older clients still connect.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import BinaryIO

from claimline.agent import run_claimline
from claimline.brief import render_brief
from claimline.index import search_cards
from claimline.injection import is_injection
from claimline.profile import ProfileError, load_profile


PROTOCOL_VERSIONS = ("2024-11-05", "2025-03-26", "2025-06-18")
SERVER_NAME = "claimline"
SERVER_VERSION = "0.1.0"


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


TOOLS = [
    _tool(
        "list_evidence",
        "List evidence cards. Does not create claims.",
        {"profile_path": {"type": "string", "description": "Path to the locker YAML."}},
        [],
    ),
    _tool(
        "search_evidence",
        "Rank cards that already list a skill. Empty when none do.",
        {
            "query": {"type": "string"},
            "skill": {"type": "string"},
            "profile_path": {"type": "string"},
        },
        ["query"],
    ),
    _tool(
        "screen_job",
        "Return job lines that try to override the evidence locker.",
        {"jd": {"type": "string"}},
        ["jd"],
    ),
    _tool(
        "build_brief",
        "Build an evidence-locked brief. Claim text comes from templates, not from the client.",
        {
            "jd": {"type": "string"},
            "profile_path": {"type": "string"},
        },
        ["jd"],
    ),
]


def _text(payload) -> dict:
    if not isinstance(payload, str):
        payload = json.dumps(payload, indent=2)
    return {"content": [{"type": "text", "text": payload}], "isError": False}


def _error(message: str) -> dict:
    return {"content": [{"type": "text", "text": message}], "isError": True}


def _profile_path(arguments: dict) -> Path:
    raw = arguments.get("profile_path") or "data/profile.yaml"
    return Path(raw)


def _call(name: str, arguments: dict) -> dict:
    try:
        if name == "screen_job":
            lines = [
                line.strip().lstrip("-*• ").strip()
                for line in str(arguments.get("jd", "")).splitlines()
            ]
            blocked = [line for line in lines if line and is_injection(line)]
            return _text({"blocked": blocked})
        if name == "list_evidence":
            profile = load_profile(_profile_path(arguments))
            cards = [
                {
                    "id": card.id,
                    "title": card.title,
                    "skills": list(card.skills),
                    "url": card.url,
                    "does_not_prove": list(card.does_not_prove),
                }
                for card in profile.cards
            ]
            return _text({"candidate": profile.candidate, "cards": cards})
        if name == "search_evidence":
            profile = load_profile(_profile_path(arguments))
            skill = arguments.get("skill")
            hits = search_cards(
                profile.cards,
                str(arguments.get("query", "")),
                str(skill) if skill else None,
                limit=3,
            )
            return _text(
                {
                    "hits": [
                        {"id": card.id, "title": card.title, "score": round(score, 4)}
                        for card, score in hits
                    ]
                }
            )
        if name == "build_brief":
            profile = load_profile(_profile_path(arguments))
            result = run_claimline(profile, str(arguments.get("jd", "")))
            brief = render_brief(profile, result)
            if result.checks.get("faithfulness", 0) < 1 or result.checks.get("number_fidelity", 0) < 1:
                return _error("verifier failed; brief withheld")
            return _text(
                {
                    "job_title": result.job_title,
                    "checks": result.checks,
                    "supported": [
                        {"skill": claim.skill, "card_id": claim.card_id}
                        for claim in result.claims
                        if claim.status == "supported"
                    ],
                    "gaps": [
                        {"skill": claim.skill, "kind": claim.kind}
                        for claim in result.claims
                        if claim.status != "supported"
                    ],
                    "brief_markdown": brief,
                }
            )
    except (ProfileError, OSError, ValueError) as exc:
        return _error(str(exc))
    return _error(f"unknown tool: {name}")


def handle_message(message: dict) -> dict | None:
    if not isinstance(message, dict):
        return None
    method = message.get("method")
    msg_id = message.get("id")
    if method == "notifications/initialized" or msg_id is None and isinstance(method, str) and method.startswith("notifications/"):
        return None
    if method == "initialize":
        params = message.get("params") or {}
        requested = str(params.get("protocolVersion") or "")
        version = requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        result = _call(str(params.get("name", "")), params.get("arguments") or {})
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    if msg_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def read_message(reader: BinaryIO) -> dict | None:
    line = reader.readline()
    if not line:
        return None
    if line.lower().startswith(b"content-length:"):
        length = int(line.split(b":", 1)[1].strip())
        while True:
            header = reader.readline()
            if header in (b"\r\n", b"\n", b""):
                break
        body = reader.read(length)
        if not body:
            return None
        return json.loads(body.decode("utf-8"))
    return json.loads(line.decode("utf-8"))


def write_message(writer: BinaryIO, payload: dict) -> None:
    writer.write(json.dumps(payload).encode("utf-8") + b"\n")
    writer.flush()


def serve(reader: BinaryIO | None = None, writer: BinaryIO | None = None) -> int:
    reader = reader if reader is not None else sys.stdin.buffer
    writer = writer if writer is not None else sys.stdout.buffer
    while True:
        try:
            message = read_message(reader)
        except json.JSONDecodeError:
            return 1
        if message is None:
            return 0
        response = handle_message(message)
        if response is not None:
            write_message(writer, response)
