"""Kotlin function and class extraction using tree-sitter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from desloppify.engine.detectors.base import FunctionInfo


def extract_kt_functions(path: Path) -> list[FunctionInfo]:
    """Extract Kotlin functions via tree-sitter KOTLIN_SPEC.

    Falls back to empty list if tree-sitter is not available.
    """
    try:
        from desloppify.core.source_discovery import find_kt_files
        from desloppify.languages._framework.treesitter import (
            KOTLIN_SPEC,
            is_available,
        )

        if not is_available():
            return []

        from desloppify.languages._framework.treesitter._extractors import (
            make_ts_extractor,
        )

        extractor = make_ts_extractor(KOTLIN_SPEC, find_kt_files)
        return extractor(path)
    except Exception:  # noqa: BLE001
        return []
