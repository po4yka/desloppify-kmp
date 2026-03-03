"""Kotlin phase pipeline — ordered detector phases for KMP scanning."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from desloppify.languages._framework.base.types import DetectorPhase

logger = logging.getLogger(__name__)


# ── Phase runners ────────────────────────────────────────────


def phase_ktlint(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Run ktlint linting phase."""
    from desloppify.languages._framework.generic_parts.tool_factories import (
        make_tool_phase,
    )

    phase = make_tool_phase("ktlint", "ktlint --reporter=json", "json", "ktlint_violation", 2)
    return phase.run(path, lang)


def phase_detekt(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Run detekt static analysis phase."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.detekt_adapter import run_detekt

    raw = run_detekt(path)
    findings = [
        make_finding(
            "detekt",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"detekt": len(raw) + 1}


def phase_platform_leakage(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Detect platform-specific API usage in commonMain."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.platform_leakage import (
        detect_platform_leakage,
    )

    files = lang.file_finder(path) if lang.file_finder else []
    zone_map = lang.zone_map
    raw = detect_platform_leakage(files, zone_map)
    findings = [
        make_finding(
            "platform_leakage",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"platform_leakage": len(files)}


def phase_expect_actual(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Cross-source-set expect/actual analysis."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.expect_actual import (
        detect_expect_actual,
    )

    files = lang.file_finder(path) if lang.file_finder else []
    raw = detect_expect_actual(files)
    findings = [
        make_finding(
            "expect_actual",
            e["file"], e.get("detail", {}).get("name", ""),
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"expect_actual": len(files)}


def phase_coroutines(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Detect unsafe coroutine patterns."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.coroutines import (
        detect_coroutine_issues,
    )

    files = lang.file_finder(path) if lang.file_finder else []
    raw = detect_coroutine_issues(files)
    findings = [
        make_finding(
            "coroutines",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"coroutines": len(files)}


def phase_kn_memory(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Detect deprecated Kotlin/Native memory model patterns."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.kn_memory import detect_kn_memory

    files = lang.file_finder(path) if lang.file_finder else []
    raw = detect_kn_memory(files)
    findings = [
        make_finding(
            "kn_memory",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"kn_memory": len(files)}


def phase_compose_smells(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Detect Compose Multiplatform code smells."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.compose_smells import (
        detect_compose_smells,
    )

    files = lang.file_finder(path) if lang.file_finder else []
    raw = detect_compose_smells(files)
    findings = [
        make_finding(
            "compose_smells",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"compose_smells": len(files)}


def phase_build_files(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Analyze build.gradle.kts and version catalog."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.build_files import (
        detect_build_issues,
    )

    raw = detect_build_issues(path)
    findings = [
        make_finding(
            "build_config",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"build_config": 1}


def phase_android_manifest(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Scan AndroidManifest.xml for security and configuration issues."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.android_manifest import (
        detect_android_manifest_issues,
    )

    raw = detect_android_manifest_issues(path)
    findings = [
        make_finding(
            "android_manifest",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"android_manifest": 1}


def phase_android_deprecated(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Detect deprecated Android API usage."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.kotlin.detectors.android_deprecated import (
        detect_android_deprecated_apis,
    )

    files = lang.file_finder(path) if lang.file_finder else []
    raw = detect_android_deprecated_apis(files)
    findings = [
        make_finding(
            "android_deprecated",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"android_deprecated": len(files)}


# ── Tree-sitter phases ──────────────────────────────────────


def _kt_treesitter_phases() -> list[DetectorPhase]:
    """Build tree-sitter-powered AST phases for Kotlin."""
    try:
        from desloppify.languages._framework.treesitter import (
            KOTLIN_SPEC,
            is_available,
        )

        if not is_available():
            return []

        from desloppify.languages._framework.treesitter.phases import (
            make_ast_smells_phase,
            make_cohesion_phase,
            make_unused_imports_phase,
        )

        phases = [
            make_ast_smells_phase(KOTLIN_SPEC),
            make_cohesion_phase(KOTLIN_SPEC),
        ]
        if KOTLIN_SPEC.import_query:
            phases.append(make_unused_imports_phase(KOTLIN_SPEC))
        return phases
    except Exception:  # noqa: BLE001
        logger.debug("tree-sitter phases not available for Kotlin")
        return []


# ── Structural + coupling ────────────────────────────────────


def _make_structural_phase() -> DetectorPhase:
    """Create the structural analysis phase with Kotlin-specific signals."""
    from desloppify.engine.detectors.base import ComplexitySignal

    signals = [
        ComplexitySignal(
            "TODOs",
            r"(?://|/\*)\s*(?:TODO|FIXME|HACK|XXX)",
            weight=2,
            threshold=0,
        ),
    ]

    try:
        from desloppify.languages._framework.treesitter import (
            KOTLIN_SPEC,
            is_available,
        )

        if is_available():
            from desloppify.languages._framework.treesitter._complexity import (
                make_callback_depth_compute,
                make_cyclomatic_complexity_compute,
                make_long_functions_compute,
                make_max_params_compute,
                make_nesting_depth_compute,
            )

            signals.extend([
                ComplexitySignal(
                    "nesting_depth", None, weight=3, threshold=4,
                    compute=make_nesting_depth_compute(KOTLIN_SPEC),
                ),
                ComplexitySignal(
                    "long_functions", None, weight=3, threshold=80,
                    compute=make_long_functions_compute(KOTLIN_SPEC),
                ),
                ComplexitySignal(
                    "cyclomatic_complexity", None, weight=2, threshold=15,
                    compute=make_cyclomatic_complexity_compute(KOTLIN_SPEC),
                ),
                ComplexitySignal(
                    "many_params", None, weight=2, threshold=7,
                    compute=make_max_params_compute(KOTLIN_SPEC),
                ),
                ComplexitySignal(
                    "callback_depth", None, weight=2, threshold=3,
                    compute=make_callback_depth_compute(KOTLIN_SPEC),
                ),
            ])
    except Exception:  # noqa: BLE001
        pass

    def run(path, lang):
        from desloppify.core.output import log
        from desloppify.languages._framework.base.shared_phases import (
            run_structural_phase,
        )

        return run_structural_phase(
            path, lang,
            complexity_signals=signals,
            log_fn=log,
            min_loc=40,
        )

    return DetectorPhase("Structural analysis", run)


def _make_coupling_phase() -> DetectorPhase:
    """Create a coupling phase using the KMP dep graph builder."""
    from desloppify.languages.kotlin.detectors.deps import build_kt_dep_graph

    def run(path, lang):
        from desloppify.core.output import log
        from desloppify.languages._framework.base.shared_phases import (
            run_coupling_phase,
        )

        return run_coupling_phase(
            path, lang,
            build_dep_graph_fn=build_kt_dep_graph,
            log_fn=log,
        )

    return DetectorPhase("Coupling + cycles + orphaned", run)


# ── Phase pipeline assembly ──────────────────────────────────


def build_kotlin_phases() -> list[DetectorPhase]:
    """Build the complete Kotlin/KMP phase pipeline."""
    from desloppify.languages._framework.base.phase_builders import (
        detector_phase_security,
        detector_phase_signature,
        detector_phase_test_coverage,
        shared_subjective_duplicates_tail,
    )

    phases: list[DetectorPhase] = [
        # External tools
        DetectorPhase("Detekt", phase_detekt),
        DetectorPhase("Ktlint", phase_ktlint),
        # Structural analysis
        _make_structural_phase(),
        # KMP-specific detectors
        DetectorPhase("KMP platform leakage", phase_platform_leakage),
        DetectorPhase("KMP expect/actual", phase_expect_actual),
        DetectorPhase("Coroutine safety", phase_coroutines),
        DetectorPhase("Deprecated K/N patterns", phase_kn_memory),
        DetectorPhase("Compose smells", phase_compose_smells),
        DetectorPhase("Build config", phase_build_files),
        DetectorPhase("Android manifest", phase_android_manifest),
        DetectorPhase("Android deprecated APIs", phase_android_deprecated),
        # Coupling (dep graph based)
        _make_coupling_phase(),
        # Tree-sitter AST phases
        *_kt_treesitter_phases(),
        # Shared phases
        detector_phase_signature(),
        detector_phase_test_coverage(),
        detector_phase_security(),
        # Tail
        *shared_subjective_duplicates_tail(),
    ]

    return phases
