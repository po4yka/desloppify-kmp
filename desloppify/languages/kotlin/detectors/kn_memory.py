"""Detect deprecated Kotlin/Native memory model patterns."""

from __future__ import annotations

import re

_FREEZE_RE = re.compile(r"\.\s*freeze\s*\(\s*\)")
_SHARED_IMMUTABLE_RE = re.compile(r"@SharedImmutable\b")
_THREAD_LOCAL_RE = re.compile(r"@ThreadLocal\b")
_ENSURE_NEVER_FROZEN_RE = re.compile(r"\bensureNeverFrozen\s*\(\s*\)")
_KN_CONCURRENT_IMPORT_RE = re.compile(r"^import\s+kotlin\.native\.concurrent\.")


def detect_kn_memory(
    files: list[str],
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []

    patterns = [
        (_FREEZE_RE, ".freeze() call (deprecated K/N memory model)"),
        (_SHARED_IMMUTABLE_RE, "@SharedImmutable (deprecated K/N memory model)"),
        (_THREAD_LOCAL_RE, "@ThreadLocal (deprecated K/N memory model)"),
        (_ENSURE_NEVER_FROZEN_RE, "ensureNeverFrozen() (deprecated K/N memory model)"),
        (_KN_CONCURRENT_IMPORT_RE, "kotlin.native.concurrent import (deprecated)"),
    ]

    for filepath in files:
        if not filepath.endswith(".kt"):
            continue
        content = _read(filepath)
        if content is None:
            continue

        for lineno, line in enumerate(content.splitlines(), 1):
            for pattern, desc in patterns:
                if pattern.search(line):
                    findings.append({
                        "file": filepath,
                        "line": lineno,
                        "summary": desc,
                        "detail": {"kind": "kn_memory", "snippet": line.strip()[:200]},
                        "tier": 2,
                        "confidence": "high",
                    })

    return findings
