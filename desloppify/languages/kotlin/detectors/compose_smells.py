"""Detect Compose Multiplatform code smells."""

from __future__ import annotations

import re

# Detect @Composable function definitions with parameter lists
_COMPOSABLE_FUN_RE = re.compile(
    r"@Composable\s+(?:(?:internal|private|public)\s+)?fun\s+(\w+)\s*\(([^)]*)\)",
    re.DOTALL,
)
_STATE_WITHOUT_REMEMBER_RE = re.compile(
    r"\bmutableStateOf\s*\(", re.MULTILINE,
)
_REMEMBER_RE = re.compile(r"\bremember\s*\{", re.MULTILINE)
_VIEWMODEL_PARAM_RE = re.compile(
    r":\s*\w*ViewModel\b",
)
_LAZY_LIST_ITEMS_RE = re.compile(
    r"\b(?:LazyColumn|LazyRow)\b",
)
_ITEMS_NO_KEY_RE = re.compile(
    r"\bitems\s*\([^)]*\)\s*\{",
)
_ITEMS_WITH_KEY_RE = re.compile(
    r"\bitems\s*\([^)]*key\s*=",
)

COMPOSE_SMELL_IDS = (
    "composable_params_bloat",
    "state_without_remember",
    "viewmodel_in_composable_params",
    "lazy_list_no_key",
)


def detect_compose_smells(
    files: list[str],
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []

    for filepath in files:
        if not filepath.endswith(".kt"):
            continue
        content = _read(filepath)
        if content is None:
            continue

        # Check for @Composable functions
        for m in _COMPOSABLE_FUN_RE.finditer(content):
            func_name = m.group(1)
            params_str = m.group(2)
            params = [p.strip() for p in params_str.split(",") if p.strip()]

            # composable_params_bloat: >8 params
            if len(params) > 8:
                line = content[:m.start()].count("\n") + 1
                findings.append({
                    "file": filepath,
                    "line": line,
                    "summary": f"@Composable {func_name} has {len(params)} params (>8)",
                    "detail": {"kind": "composable_params_bloat", "count": len(params)},
                    "tier": 3,
                    "confidence": "high",
                })

            # viewmodel_in_composable_params
            if _VIEWMODEL_PARAM_RE.search(params_str):
                line = content[:m.start()].count("\n") + 1
                findings.append({
                    "file": filepath,
                    "line": line,
                    "summary": f"ViewModel in @Composable {func_name} params",
                    "detail": {"kind": "viewmodel_in_composable_params"},
                    "tier": 2,
                    "confidence": "high",
                })

        # state_without_remember: mutableStateOf() outside remember{}
        _check_state_without_remember(content, filepath, findings)

        # lazy_list_no_key
        if _LAZY_LIST_ITEMS_RE.search(content):
            for m in _ITEMS_NO_KEY_RE.finditer(content):
                # Check this specific items() call does NOT have key=
                region = content[max(0, m.start() - 5):m.end() + 50]
                if not _ITEMS_WITH_KEY_RE.search(region):
                    line = content[:m.start()].count("\n") + 1
                    findings.append({
                        "file": filepath,
                        "line": line,
                        "summary": "items() in LazyList without key parameter",
                        "detail": {"kind": "lazy_list_no_key"},
                        "tier": 3,
                        "confidence": "medium",
                    })

    return findings


def _check_state_without_remember(
    content: str, filepath: str, findings: list[dict]
) -> None:
    """Find mutableStateOf() calls not wrapped in remember{}."""
    for m in _STATE_WITHOUT_REMEMBER_RE.finditer(content):
        # Look backwards ~200 chars for a remember{ that hasn't been closed
        start = max(0, m.start() - 200)
        preceding = content[start:m.start()]
        # Simple heuristic: count unmatched remember{ vs }
        remember_opens = len(re.findall(r"\bremember\s*\{", preceding))
        closes = preceding.count("}")
        if remember_opens <= closes:
            line = content[:m.start()].count("\n") + 1
            findings.append({
                "file": filepath,
                "line": line,
                "summary": "mutableStateOf() outside remember{}",
                "detail": {"kind": "state_without_remember"},
                "tier": 2,
                "confidence": "medium",
            })
