"""Aggregated Kotlin smells runner — orchestrates all KMP-specific detectors."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from desloppify.engine.policy.zones import FileZoneMap


def detect_kt_smells(
    files: list[str],
    zone_map: FileZoneMap | None = None,
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Run all Kotlin-specific smell detectors and aggregate results."""
    from desloppify.languages.kotlin.detectors.compose_smells import (
        detect_compose_smells,
    )
    from desloppify.languages.kotlin.detectors.coroutines import (
        detect_coroutine_issues,
    )
    from desloppify.languages.kotlin.detectors.kn_memory import detect_kn_memory

    findings: list[dict] = []
    findings.extend(detect_compose_smells(files, read_fn=read_fn))
    findings.extend(detect_coroutine_issues(files, read_fn=read_fn))
    findings.extend(detect_kn_memory(files, read_fn=read_fn))
    return findings
