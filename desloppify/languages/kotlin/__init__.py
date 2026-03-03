"""Kotlin/KMP language plugin — full integration with Compose Multiplatform support."""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING

from desloppify.core.source_discovery import find_kt_files
from desloppify.engine.policy.zones import COMMON_ZONE_RULES, Zone, ZoneRule
from desloppify.languages._framework.base.types import (
    BoundaryRule,
    DetectorCoverageStatus,
    LangConfig,
)

if TYPE_CHECKING:
    from desloppify.engine.policy.zones import FileZoneMap

logger = logging.getLogger(__name__)


# ── Zone rules ───────────────────────────────────────────────

KT_ZONE_RULES: list[ZoneRule] = [
    ZoneRule(Zone.GENERATED, ["/build/", "/.gradle/", ".generated.kt"]),
    ZoneRule(Zone.TEST, [
        "/commonTest/", "/androidTest/", "/iosTest/",
        "/androidUnitTest/", "/androidInstrumentedTest/",
        "/jvmTest/", "/desktopTest/", "/nativeTest/",
        "Test.kt", "Spec.kt",
    ]),
    ZoneRule(Zone.CONFIG, [
        "build.gradle.kts", "build.gradle", "settings.gradle.kts",
        "libs.versions.toml", "gradle.properties", "proguard-rules.pro",
        "gradle-wrapper.properties", "AndroidManifest.xml",
    ]),
    ZoneRule(Zone.VENDOR, ["/build/", "/.gradle/", "/gradle/wrapper/"]),
    *COMMON_ZONE_RULES,
]


# ── Security detection ───────────────────────────────────────

def _detect_kt_security(
    files: list[str], zone_map: FileZoneMap | None
) -> tuple[list[dict], int]:
    """Language-specific security checks for Kotlin/KMP.

    Delegates to the platform leakage detector for commonMain files.
    """
    from desloppify.languages.kotlin.detectors.platform_leakage import (
        detect_platform_leakage,
    )

    raw = detect_platform_leakage(files, zone_map)
    # Only tier 1 findings count as security issues
    security_findings = [f for f in raw if f["tier"] == 1]
    return security_findings, len(files)


# ── Coverage prerequisites ───────────────────────────────────

def _scan_coverage_prerequisites() -> list[DetectorCoverageStatus]:
    """Check for ktlint and detekt availability."""
    statuses: list[DetectorCoverageStatus] = []

    if not shutil.which("ktlint"):
        statuses.append(DetectorCoverageStatus(
            detector="ktlint_violation",
            status="reduced",
            confidence=0.7,
            summary="ktlint not found on PATH",
            impact="Code style violations will not be detected",
            remediation="Install ktlint: https://pinterest.github.io/ktlint/",
            tool="ktlint",
            reason="not_installed",
        ))

    if not shutil.which("detekt"):
        statuses.append(DetectorCoverageStatus(
            detector="detekt",
            status="reduced",
            confidence=0.7,
            summary="detekt not found on PATH",
            impact="Static analysis findings will not be detected",
            remediation="Install detekt: https://detekt.dev/docs/gettingstarted/cli/",
            tool="detekt",
            reason="not_installed",
        ))

    return statuses


# ── Plugin construction ──────────────────────────────────────

def _build_kotlin_config() -> LangConfig:
    """Build the full Kotlin/KMP plugin config."""
    from desloppify.languages.kotlin.commands import get_detect_commands
    from desloppify.languages.kotlin.detectors.deps import build_kt_dep_graph
    from desloppify.languages.kotlin.extractors import extract_kt_functions
    from desloppify.languages.kotlin.phases import build_kotlin_phases
    from desloppify.languages.kotlin.review import (
        HOLISTIC_REVIEW_DIMENSIONS,
        LOW_VALUE_PATTERN,
        MIGRATION_MIXED_EXTENSIONS,
        MIGRATION_PATTERN_PAIRS,
        REVIEW_GUIDANCE,
        review_api_surface,
        review_module_patterns,
    )

    cfg = LangConfig(
        name="kotlin",
        extensions=[".kt", ".kts"],
        exclusions=["build", ".gradle", ".idea"],
        default_src=".",
        build_dep_graph=build_kt_dep_graph,
        entry_patterns=[
            "/main.kt", "/Main.kt", "/App.kt", "Application.kt",
            "MainActivity.kt", "MainViewController.kt",
        ],
        barrel_names=set(),
        phases=build_kotlin_phases(),
        fixers={},
        get_area=None,
        detect_commands=get_detect_commands(),
        extract_functions=extract_kt_functions,
        boundaries=[
            BoundaryRule("commonMain/", "androidMain/", "common->android"),
            BoundaryRule("commonMain/", "iosMain/", "common->ios"),
        ],
        typecheck_cmd="./gradlew compileKotlin",
        file_finder=find_kt_files,
        large_threshold=400,
        complexity_threshold=20,
        default_scan_profile="full",
        detect_markers=["build.gradle.kts", "settings.gradle.kts"],
        external_test_dirs=["commonTest", "androidTest", "iosTest"],
        test_file_extensions=[".kt"],
        review_module_patterns_fn=review_module_patterns,
        review_api_surface_fn=review_api_surface,
        review_guidance=REVIEW_GUIDANCE,
        review_low_value_pattern=LOW_VALUE_PATTERN,
        holistic_review_dimensions=HOLISTIC_REVIEW_DIMENSIONS,
        migration_pattern_pairs=MIGRATION_PATTERN_PAIRS,
        migration_mixed_extensions={ext for pair in MIGRATION_MIXED_EXTENSIONS for ext in pair},
        zone_rules=KT_ZONE_RULES,
        integration_depth="full",
    )

    # Override security detection
    cfg.detect_lang_security = _detect_kt_security
    cfg.scan_coverage_prerequisites = _scan_coverage_prerequisites

    return cfg


# ── KMP detector + scoring registration ──────────────────────

def _register_kmp_detectors() -> None:
    """Register KMP-specific detectors and scoring policies."""
    from desloppify.core.registry import DetectorMeta, register_detector
    from desloppify.engine._scoring.policy.core import (
        SECURITY_EXCLUDED_ZONES,
        DetectorScoringPolicy,
        register_scoring_policy,
    )

    _defs: list[tuple[DetectorMeta, DetectorScoringPolicy]] = [
        (
            DetectorMeta(
                "platform_leakage", "platform leakage", "Security", "manual_fix",
                "fix platform API usage in commonMain — use expect/actual or move to platform source set",
            ),
            DetectorScoringPolicy(
                "platform_leakage", "Security", 4,
                file_based=True,
                excluded_zones=SECURITY_EXCLUDED_ZONES,
            ),
        ),
        (
            DetectorMeta(
                "expect_actual", "expect/actual", "Code quality", "manual_fix",
                "add missing actual declarations or simplify expect class with body",
            ),
            DetectorScoringPolicy("expect_actual", "Code quality", 3),
        ),
        (
            DetectorMeta(
                "coroutines", "coroutine safety", "Code quality", "manual_fix",
                "replace GlobalScope with structured concurrency, remove runBlocking from shared code",
            ),
            DetectorScoringPolicy("coroutines", "Code quality", 3),
        ),
        (
            DetectorMeta(
                "kn_memory", "K/N memory", "Code quality", "auto_fix",
                "remove deprecated Kotlin/Native memory model patterns",
                fixers=("remove-freeze",),
            ),
            DetectorScoringPolicy("kn_memory", "Code quality", 3),
        ),
        (
            DetectorMeta(
                "compose_smells", "Compose smells", "Code quality", "manual_fix",
                "fix Compose code smells — state hoisting, remember, parameter count",
                needs_judgment=True,
            ),
            DetectorScoringPolicy("compose_smells", "Code quality", 3, file_based=True),
        ),
        (
            DetectorMeta(
                "build_config", "build config", "Code quality", "manual_fix",
                "fix build configuration issues — missing targets, version mismatches",
            ),
            DetectorScoringPolicy("build_config", "Code quality", 3),
        ),
        (
            DetectorMeta(
                "detekt", "detekt", "Code quality", "manual_fix",
                "review and fix detekt static analysis findings",
            ),
            DetectorScoringPolicy("detekt", "Code quality", 3, file_based=True),
        ),
        (
            DetectorMeta(
                "android_manifest", "Android manifest", "Security", "manual_fix",
                "fix AndroidManifest.xml security and configuration issues",
            ),
            DetectorScoringPolicy(
                "android_manifest", "Security", 4,
                excluded_zones=SECURITY_EXCLUDED_ZONES,
            ),
        ),
        (
            DetectorMeta(
                "android_deprecated", "Android deprecated APIs", "Code quality", "manual_fix",
                "replace deprecated Android APIs with modern alternatives",
            ),
            DetectorScoringPolicy("android_deprecated", "Code quality", 3, file_based=True),
        ),
        (
            DetectorMeta(
                "ktlint_violation", "ktlint", "Code quality", "auto_fix",
                "fix ktlint formatting violations",
                fixers=("ktlint-format",),
            ),
            DetectorScoringPolicy("ktlint_violation", "Code quality", 3, file_based=True),
        ),
    ]

    for meta, policy in _defs:
        register_detector(meta)
        register_scoring_policy(policy)


# ── Registration ─────────────────────────────────────────────

from desloppify.languages import register_generic_lang  # noqa: E402

_register_kmp_detectors()
_cfg = _build_kotlin_config()
register_generic_lang("kotlin", _cfg)

# Register hook so get_lang_hook("kotlin", "test_coverage") works.
from desloppify.hook_registry import register_lang_hooks  # noqa: E402
from desloppify.languages.kotlin import test_coverage as _tc  # noqa: E402

register_lang_hooks("kotlin", test_coverage=_tc)
