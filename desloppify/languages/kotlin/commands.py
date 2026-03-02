"""Kotlin detect subcommand handlers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def ktlint_violation(scan_path: Path, **_kwargs: Any) -> list[dict]:
    """Run ktlint and return findings."""
    from desloppify.languages._framework.generic_parts.parsers import parse_json
    from desloppify.languages._framework.generic_parts.tool_runner import run_tool

    return run_tool("ktlint --reporter=json", scan_path, parse_json)


def get_detect_commands() -> dict[str, Any]:
    """Return detect command handlers for the Kotlin plugin.

    Each key is a detector ID, value is a callable that runs the detector
    and returns raw findings.
    """
    return {
        "ktlint_violation": ktlint_violation,
    }
