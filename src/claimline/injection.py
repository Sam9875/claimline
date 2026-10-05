"""Line-level screen for instructions that try to override the evidence locker.

A match removes the whole line from requirement parsing. The line is kept on
the run so the brief can show what was discarded.
"""

from __future__ import annotations

import re


_PATTERNS = (
    re.compile(
        r"ignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above|your)\s+"
        r"(instructions|rules|profile|evidence)",
        re.IGNORECASE,
    ),
    re.compile(r"ignore\s+the\s+profile", re.IGNORECASE),
    re.compile(
        r"disregard\s+the\s+(profile|evidence|locker|instructions)",
        re.IGNORECASE,
    ),
    re.compile(r"\byou\s+are\s+now\b", re.IGNORECASE),
    re.compile(r"\bpretend\s+(that\s+)?(the\s+candidate|you|they)\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"\bsay\s+the\s+candidate\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+if\b", re.IGNORECASE),
    re.compile(
        r"\bdo\s+not\s+follow\s+the\s+(profile|rules|instructions)\b",
        re.IGNORECASE,
    ),
)


def is_injection(line: str) -> bool:
    return any(pattern.search(line) for pattern in _PATTERNS)
