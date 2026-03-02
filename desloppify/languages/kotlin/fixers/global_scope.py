"""Suggest structured concurrency replacements for GlobalScope usage.

This is a dry-run-only fixer — it reports what should change but
does not auto-rewrite because the replacement requires context
(which CoroutineScope to use).
"""

from __future__ import annotations

import re
from pathlib import Path


def suggest_global_scope_fixes(
    filepath: str | Path,
) -> list[dict]:
    """Identify GlobalScope usages and suggest structured concurrency replacements."""
    path = Path(filepath)
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []

    suggestions: list[dict] = []
    pattern = re.compile(r"\bGlobalScope\s*\.\s*(launch|async)\b")

    for m in pattern.finditer(content):
        line = content[:m.start()].count("\n") + 1
        coroutine_builder = m.group(1)
        suggestions.append({
            "file": str(filepath),
            "line": line,
            "action": "replace",
            "old": f"GlobalScope.{coroutine_builder}",
            "suggestion": f"coroutineScope {{ {coroutine_builder} {{ ... }} }}",
            "note": (
                "Replace GlobalScope with structured concurrency. "
                "Use the enclosing CoroutineScope (viewModelScope, lifecycleScope, "
                "or a custom scope passed as parameter)."
            ),
        })

    return suggestions
