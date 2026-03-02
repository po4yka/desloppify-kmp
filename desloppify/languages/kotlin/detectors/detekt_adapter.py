"""Detekt JSON output adapter — parse detekt reports into findings."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_SEVERITY_TO_TIER = {
    "error": 1,
    "warning": 2,
    "info": 3,
    "style": 3,
}


def run_detekt(scan_root: str | Path) -> list[dict]:
    """Run detekt and parse findings from JSON report.

    Gracefully returns [] if detekt is not installed or fails.
    """
    root = Path(scan_root)
    try:
        result = subprocess.run(
            [
                "detekt",
                "--input", str(root),
                "--report", "json:/dev/stdout",
                "--all-rules",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(root),
        )
    except FileNotFoundError:
        logger.debug("detekt not found on PATH — skipping")
        return []
    except subprocess.TimeoutExpired:
        logger.warning("detekt timed out after 120s")
        return []

    output = result.stdout.strip()
    if not output:
        return []

    return parse_detekt_json(output, scan_root=str(root))


def parse_detekt_json(
    raw_json: str,
    *,
    scan_root: str = "",
) -> list[dict]:
    """Parse detekt JSON output into normalized findings."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        logger.debug("detekt produced invalid JSON")
        return []

    findings: list[dict] = []

    # detekt JSON structure: list of rule-set objects with issues
    issues = []
    if isinstance(data, list):
        issues = data
    elif isinstance(data, dict):
        # Some detekt versions nest under "issues" or rule sets
        for _rule_set, entries in data.items():
            if isinstance(entries, list):
                issues.extend(entries)

    for issue in issues:
        if not isinstance(issue, dict):
            continue

        rule_id = issue.get("ruleId") or issue.get("rule") or "detekt"
        message = issue.get("message", "")
        severity = issue.get("severity", "warning").lower()
        tier = _SEVERITY_TO_TIER.get(severity, 3)

        location = issue.get("location", {})
        filepath = location.get("file", "")
        line = 1
        pos = location.get("position", {}) or location.get("source", {})
        if isinstance(pos, dict):
            line = pos.get("line", 1)

        # Make path relative if possible
        if scan_root and filepath.startswith(scan_root):
            filepath = filepath[len(scan_root):].lstrip("/")

        findings.append({
            "file": filepath,
            "line": line,
            "summary": f"[{rule_id}] {message}" if message else rule_id,
            "detail": {"kind": "detekt", "rule": rule_id, "severity": severity},
            "tier": tier,
            "confidence": "high",
        })

    return findings
