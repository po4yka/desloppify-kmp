"""Ktlint --format wrapper fixer."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_ktlint_format(
    target: str | Path,
    *,
    dry_run: bool = True,
) -> dict:
    """Run ktlint --format on a file or directory.

    Returns a result dict with status and output.
    """
    path = Path(target)
    cmd = ["ktlint", "--format"]

    if path.is_file():
        cmd.append(str(path))
    elif path.is_dir():
        cmd.append(str(path / "**/*.kt"))

    if dry_run:
        return {
            "status": "dry_run",
            "command": " ".join(cmd),
            "target": str(target),
        }

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {
            "status": "not_installed",
            "command": " ".join(cmd),
            "error": "ktlint not found on PATH",
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "command": " ".join(cmd),
            "error": "ktlint timed out after 120s",
        }
