"""Detect code quality and security issues in Swift source files."""

from __future__ import annotations

import re

_SECRET_RE = re.compile(
    r"""(?:"""
    r"AIza[0-9A-Za-z_-]{35}"  # Google API key
    r"|AKIA[0-9A-Z]{16}"  # AWS access key
    r"|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"  # private key
    r"|sk-[a-zA-Z0-9]{20,}"  # OpenAI-style key
    r"|ghp_[a-zA-Z0-9]{36}"  # GitHub PAT
    r")"
)

_EMPTY_CATCH_RE = re.compile(
    r"catch\s*(?:\([^)]*\))?\s*\{\s*(?://[^\n]*)?\s*\}",
)

_CHECKS: list[tuple[re.Pattern, str, str, int, str]] = [
    (
        re.compile(r"\bUIWebView\b"),
        "uiwebview_deprecated",
        "UIWebView is deprecated and rejected by App Store -- use WKWebView",
        1,
        "high",
    ),
    (
        re.compile(r"DispatchQueue\s*\.\s*main\s*\.\s*sync\b"),
        "main_sync_deadlock",
        "DispatchQueue.main.sync risks deadlock when called from main thread",
        1,
        "high",
    ),
    (
        re.compile(r"\btry\s*!"),
        "force_try",
        "try! will crash on error -- use try/catch or try?",
        2,
        "high",
    ),
    (
        re.compile(r"\bas\s*!"),
        "force_cast",
        "as! will crash if cast fails -- use as? with guard/if-let",
        2,
        "medium",
    ),
    (
        re.compile(r"\bUIAlertView\b|\bUIActionSheet\b"),
        "deprecated_uialertview",
        "UIAlertView/UIActionSheet are deprecated -- use UIAlertController",
        2,
        "high",
    ),
    (
        re.compile(r"\bUISearchDisplayController\b"),
        "deprecated_uisearchdisplay",
        "UISearchDisplayController is deprecated -- use UISearchController",
        2,
        "high",
    ),
]


def detect_swift_code_issues(
    files: list[str],
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Scan Swift source files for code quality and security issues."""
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []

    for filepath in files:
        if not filepath.endswith(".swift"):
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

            # Hardcoded secrets
            if _SECRET_RE.search(line):
                findings.append({
                    "file": filepath,
                    "line": lineno,
                    "summary": "Possible hardcoded secret in source code",
                    "detail": {"kind": "hardcoded_secret", "snippet": line.strip()[:80] + "..."},
                    "tier": 1,
                    "confidence": "medium",
                })

        # Empty catch blocks (multi-line check)
        for m in _EMPTY_CATCH_RE.finditer(content):
            lineno = content[:m.start()].count("\n") + 1
            findings.append({
                "file": filepath,
                "line": lineno,
                "summary": "Empty catch block silently swallows errors",
                "detail": {"kind": "empty_catch"},
                "tier": 2,
                "confidence": "high",
            })

    return findings
