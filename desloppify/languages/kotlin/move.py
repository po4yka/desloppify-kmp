"""Kotlin move helpers — package-based file organization."""

from __future__ import annotations

import re
from pathlib import Path


def suggest_move(filepath: str, scan_root: str | Path) -> str | None:
    """Suggest a target path for a Kotlin file based on its package declaration.

    Returns None if the file is already in the correct location or
    if no package declaration is found.
    """
    root = Path(scan_root)
    source = Path(filepath)

    try:
        content = source.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    pkg_match = re.search(r"^package\s+([\w.]+)", content, re.MULTILINE)
    if not pkg_match:
        return None

    package = pkg_match.group(1)
    expected_dir = package.replace(".", "/")

    # Check if the file is already under the expected package directory
    rel = str(source.relative_to(root))
    if expected_dir in rel:
        return None

    # Suggest the canonical location
    filename = source.name
    return f"{expected_dir}/{filename}"
