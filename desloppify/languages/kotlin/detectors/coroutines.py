"""Detect unsafe coroutine patterns in KMP code."""

from __future__ import annotations

import re

from desloppify.languages.kotlin.detectors.kmp_utils import (
    get_source_set,
    is_test_source_set,
)

_GLOBAL_SCOPE_RE = re.compile(r"\bGlobalScope\s*\.\s*(launch|async)\b")
_RUN_BLOCKING_RE = re.compile(r"\brunBlocking\b")
_DISPATCHERS_IO_RE = re.compile(r"\bDispatchers\s*\.\s*IO\b")


def detect_coroutine_issues(
    files: list[str],
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []

    for filepath in files:
        if not filepath.endswith(".kt"):
            continue
        content = _read(filepath)
        if content is None:
            continue

        is_test = is_test_source_set(filepath)
        ss = get_source_set(filepath)

        for lineno, line in enumerate(content.splitlines(), 1):
            # GlobalScope.launch / GlobalScope.async (tier 2 everywhere)
            if _GLOBAL_SCOPE_RE.search(line):
                findings.append({
                    "file": filepath,
                    "line": lineno,
                    "summary": "GlobalScope usage -- prefer structured concurrency",
                    "detail": {"kind": "global_scope", "snippet": line.strip()[:200]},
                    "tier": 2,
                    "confidence": "high",
                })

            # runBlocking in non-test code
            if _RUN_BLOCKING_RE.search(line) and not is_test:
                tier = 2 if ss == "commonMain" else 3
                findings.append({
                    "file": filepath,
                    "line": lineno,
                    "summary": "runBlocking in non-test code",
                    "detail": {"kind": "run_blocking", "snippet": line.strip()[:200]},
                    "tier": tier,
                    "confidence": "high",
                })

            # Dispatchers.IO in commonMain (may not be available on all platforms)
            if _DISPATCHERS_IO_RE.search(line) and ss == "commonMain":
                findings.append({
                    "file": filepath,
                    "line": lineno,
                    "summary": "Dispatchers.IO in commonMain -- not available on all platforms",
                    "detail": {"kind": "dispatchers_io", "snippet": line.strip()[:200]},
                    "tier": 3,
                    "confidence": "medium",
                })

    return findings
