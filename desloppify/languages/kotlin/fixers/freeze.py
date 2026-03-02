"""Remove deprecated Kotlin/Native memory model patterns.

Handles: .freeze(), @SharedImmutable, @ThreadLocal, ensureNeverFrozen()
"""

from __future__ import annotations

import re
from pathlib import Path


def fix_freeze_patterns(
    filepath: str | Path,
    *,
    dry_run: bool = True,
) -> list[dict]:
    """Remove deprecated K/N freeze patterns from a Kotlin file.

    Returns a list of changes made (or that would be made in dry_run mode).
    """
    path = Path(filepath)
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []

    changes: list[dict] = []
    new_content = content

    # Remove .freeze() calls
    freeze_re = re.compile(r"\.\s*freeze\s*\(\s*\)")
    for m in freeze_re.finditer(content):
        line = content[:m.start()].count("\n") + 1
        changes.append({
            "line": line,
            "action": "remove",
            "pattern": ".freeze()",
            "file": str(filepath),
        })
    new_content = freeze_re.sub("", new_content)

    # Remove @SharedImmutable annotations (and the line if it's alone)
    shared_re = re.compile(r"^\s*@SharedImmutable\s*\n?", re.MULTILINE)
    for m in shared_re.finditer(content):
        line = content[:m.start()].count("\n") + 1
        changes.append({
            "line": line,
            "action": "remove",
            "pattern": "@SharedImmutable",
            "file": str(filepath),
        })
    new_content = shared_re.sub("", new_content)

    # Remove @ThreadLocal annotations
    threadlocal_re = re.compile(r"^\s*@ThreadLocal\s*\n?", re.MULTILINE)
    for m in threadlocal_re.finditer(content):
        line = content[:m.start()].count("\n") + 1
        changes.append({
            "line": line,
            "action": "remove",
            "pattern": "@ThreadLocal",
            "file": str(filepath),
        })
    new_content = threadlocal_re.sub("", new_content)

    # Remove ensureNeverFrozen() calls (full statement)
    ensure_re = re.compile(r"^\s*\w*\.?ensureNeverFrozen\s*\(\s*\)\s*\n?", re.MULTILINE)
    for m in ensure_re.finditer(content):
        line = content[:m.start()].count("\n") + 1
        changes.append({
            "line": line,
            "action": "remove",
            "pattern": "ensureNeverFrozen()",
            "file": str(filepath),
        })
    new_content = ensure_re.sub("", new_content)

    if not dry_run and changes and new_content != content:
        path.write_text(new_content, encoding="utf-8")

    return changes
