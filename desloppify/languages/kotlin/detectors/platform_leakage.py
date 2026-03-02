"""Detect platform-specific API usage in commonMain source sets."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from desloppify.languages.kotlin.detectors.kmp_utils import is_common_main

if TYPE_CHECKING:
    from desloppify.engine.policy.zones import ZoneMap

# Tier 1: hard platform leakage (will not compile on other platforms)
_TIER1_IMPORT_PREFIXES = (
    "import java.",
    "import javax.",
    "import android.",
    "import dalvik.",
    "import kotlinx.android.",
)

# Tier 2: soft platform leakage (compiles but non-portable patterns)
_TIER2_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"@HiltViewModel\b"), "@HiltViewModel annotation"),
    (re.compile(r"@Inject\b"), "@Inject annotation"),
    (re.compile(r"@AndroidEntryPoint\b"), "@AndroidEntryPoint annotation"),
    (re.compile(r"\bThread\s*\("), "Thread() constructor"),
    (re.compile(r"\bThread\.currentThread\b"), "Thread.currentThread()"),
    (re.compile(r"\bString\.format\b"), "String.format()"),
    (re.compile(r"\bSystem\.currentTimeMillis\b"), "System.currentTimeMillis()"),
    (re.compile(r"\bjava\.io\.File\b"), "java.io.File usage"),
]


def detect_platform_leakage(
    files: list[str],
    zone_map: "ZoneMap | None" = None,
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Scan commonMain files for platform-specific API usage.

    Returns a list of finding dicts compatible with the desloppify Finding shape.
    """
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []

    for filepath in files:
        if not is_common_main(filepath):
            continue
        if not filepath.endswith((".kt", ".kts")):
            continue

        content = _read(filepath)
        if content is None:
            continue

        for lineno, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()

            # Tier 1: hard platform imports
            for prefix in _TIER1_IMPORT_PREFIXES:
                if stripped.startswith(prefix):
                    findings.append(_finding(
                        filepath, lineno, stripped,
                        f"Platform import in commonMain: {stripped}",
                        tier=1,
                    ))

            # Tier 2: soft platform patterns
            for pattern, desc in _TIER2_PATTERNS:
                if pattern.search(stripped):
                    findings.append(_finding(
                        filepath, lineno, stripped,
                        f"Platform API in commonMain: {desc}",
                        tier=2,
                    ))

    return findings


def _finding(file: str, line: int, snippet: str, summary: str, *, tier: int) -> dict:
    return {
        "file": file,
        "line": line,
        "summary": summary,
        "detail": {"kind": "platform_leakage", "snippet": snippet[:200]},
        "tier": tier,
        "confidence": "high",
    }
