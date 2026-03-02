"""KMP-aware dependency graph builder.

Wraps the tree-sitter dep builder with KMP source-set awareness,
ensuring the dep graph respects source-set boundaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from desloppify.languages.kotlin.detectors.kmp_utils import get_source_set


def build_kt_dep_graph(path: Path) -> dict[str, dict[str, Any]]:
    """Build a Kotlin dependency graph with source-set annotations.

    Falls back to tree-sitter-based dep graph when available,
    otherwise returns an empty graph.
    """
    try:
        from desloppify.languages._framework.treesitter import (
            KOTLIN_SPEC,
            is_available,
        )

        if not is_available():
            return {}

        from desloppify.core.source_discovery import find_kt_files
        from desloppify.languages._framework.treesitter._imports import (
            make_ts_dep_builder,
        )

        builder = make_ts_dep_builder(KOTLIN_SPEC, find_kt_files)
        graph = builder(path)

        # Annotate each node with its source set
        for filepath, node in graph.items():
            node["source_set"] = get_source_set(filepath)

        return graph
    except Exception:  # noqa: BLE001
        return {}
