"""Detect missing or overused expect/actual declarations in KMP projects."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from desloppify.languages.kotlin.detectors.kmp_utils import get_source_set

if TYPE_CHECKING:
    pass

_EXPECT_RE = re.compile(r"^\s*expect\s+(fun|class|object|val|interface)\s+(\w+)")
_ACTUAL_RE = re.compile(r"^\s*actual\s+(fun|class|object|val|interface)\s+(\w+)")
_EXPECT_CLASS_BODY_RE = re.compile(
    r"^\s*expect\s+class\s+\w+[^{]*\{", re.MULTILINE
)


def detect_expect_actual(
    files: list[str],
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Cross-source-set analysis of expect/actual declarations."""
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text

    # Pass 1: collect expects and actuals
    expects: dict[tuple[str, str], str] = {}   # (kind, name) -> file
    actuals: dict[tuple[str, str], set[str]] = {}  # (kind, name) -> {source_sets}
    expect_classes_with_body: list[tuple[str, str]] = []  # (file, name)

    for filepath in files:
        if not filepath.endswith(".kt"):
            continue
        content = _read(filepath)
        if content is None:
            continue

        ss = get_source_set(filepath)

        for line in content.splitlines():
            m_expect = _EXPECT_RE.match(line)
            if m_expect:
                kind, name = m_expect.group(1), m_expect.group(2)
                expects[(kind, name)] = filepath

            m_actual = _ACTUAL_RE.match(line)
            if m_actual and ss:
                kind, name = m_actual.group(1), m_actual.group(2)
                actuals.setdefault((kind, name), set()).add(ss)

        # Check for expect class with body
        if _EXPECT_CLASS_BODY_RE.search(content):
            for m in _EXPECT_CLASS_BODY_RE.finditer(content):
                class_match = re.search(r"expect\s+class\s+(\w+)", m.group())
                if class_match:
                    expect_classes_with_body.append((filepath, class_match.group(1)))

    findings: list[dict] = []

    # Pass 2: find missing actuals
    for (kind, name), file in expects.items():
        actual_sets = actuals.get((kind, name), set())
        if not actual_sets:
            findings.append({
                "file": file,
                "line": 1,
                "summary": f"Missing actual declarations for expect {kind} {name}",
                "detail": {"kind": "missing_actual", "expect_kind": kind, "name": name},
                "tier": 1,
                "confidence": "high",
            })

    # Pass 3: expect class with body (could be interface + expect fun)
    for file, name in expect_classes_with_body:
        findings.append({
            "file": file,
            "line": 1,
            "summary": f"expect class {name} has body -- consider expect fun + interface",
            "detail": {"kind": "expect_class_body", "name": name},
            "tier": 3,
            "confidence": "medium",
        })

    return findings
