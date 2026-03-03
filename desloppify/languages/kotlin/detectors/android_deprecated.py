"""Detect deprecated and insecure Android API usage in Kotlin/Java source files."""

from __future__ import annotations

import re

_CHECKS: list[tuple[re.Pattern, str, str, int, str]] = [
    # (pattern, kind, summary, tier, confidence)
    (
        re.compile(r"\bMODE_WORLD_READABLE\b|\bMODE_WORLD_WRITABLE\b"),
        "world_readable_writable",
        "MODE_WORLD_READABLE/WRITABLE is insecure -- use FileProvider or encrypted storage",
        1,
        "high",
    ),
    (
        re.compile(r"\brawQuery\s*\([^)]*\+"),
        "sql_injection_risk",
        "rawQuery() with string concatenation -- use parameterized queries",
        1,
        "medium",
    ),
    (
        re.compile(r"\bimport\s+android\.os\.AsyncTask\b|\bAsyncTask\s*[<(]"),
        "deprecated_asynctask",
        "AsyncTask is deprecated -- use coroutines or java.util.concurrent",
        2,
        "high",
    ),
    (
        re.compile(r"\bimport\s+android\.app\.IntentService\b|\bIntentService\s*\(\b"),
        "deprecated_intentservice",
        "IntentService is deprecated -- use WorkManager or coroutines",
        2,
        "high",
    ),
    (
        re.compile(r"\bLocalBroadcastManager\b"),
        "deprecated_localbroadcast",
        "LocalBroadcastManager is deprecated -- use LiveData, Flow, or an event bus",
        2,
        "high",
    ),
    (
        re.compile(r"\bimport\s+android\.support\.(v4|v7)\b"),
        "old_support_library",
        "android.support.v4/v7 is deprecated -- migrate to AndroidX",
        2,
        "high",
    ),
    (
        re.compile(r"kotlin-android-extensions|kotlinx\.android\.synthetic"),
        "deprecated_kotlin_android_ext",
        "kotlin-android-extensions / synthetic imports are deprecated -- use view binding",
        2,
        "high",
    ),
]


def detect_android_deprecated_apis(
    files: list[str],
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Scan Kotlin/Java files for deprecated Android API usage."""
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []

    for filepath in files:
        if not (filepath.endswith(".kt") or filepath.endswith(".java")):
            continue
        content = _read(filepath)
        if content is None:
            continue

        for lineno, line in enumerate(content.splitlines(), 1):
            for pattern, kind, summary, tier, confidence in _CHECKS:
                if pattern.search(line):
                    findings.append({
                        "file": filepath,
                        "line": lineno,
                        "summary": summary,
                        "detail": {"kind": kind, "snippet": line.strip()[:200]},
                        "tier": tier,
                        "confidence": confidence,
                    })

    return findings
