"""Swift language plugin — swiftlint + KMP interop awareness + iOS native detectors."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from desloppify.engine.policy.zones import COMMON_ZONE_RULES, Zone, ZoneRule
from desloppify.languages._framework.base.types import DetectorPhase
from desloppify.languages._framework.generic import generic_lang
from desloppify.languages._framework.treesitter import SWIFT_SPEC

# KMP-aware zone rules for Swift
_SWIFT_ZONE_RULES = [
    ZoneRule(Zone.GENERATED, ["/build/", "/DerivedData/", ".generated.swift"]),
    ZoneRule(Zone.TEST, [
        "/Tests/", "/UITests/",
        "Tests.swift", "Test.swift", "Spec.swift",
    ]),
    ZoneRule(Zone.CONFIG, [
        "Package.swift", "Podfile",
        "project.pbxproj", ".xcconfig",
        "Info.plist", "PrivacyInfo.xcprivacy",
    ]),
    ZoneRule(Zone.VENDOR, ["/Pods/", "/Carthage/", "/.build/"]),
    *COMMON_ZONE_RULES,
]

_cfg = generic_lang(
    name="swift",
    extensions=[".swift"],
    tools=[
        {
            "label": "swiftlint",
            "cmd": "swiftlint lint --reporter json",
            "fmt": "json",
            "id": "swiftlint_violation",
            "tier": 2,
            "fix_cmd": "swiftlint --fix",
        },
    ],
    depth="shallow",
    detect_markers=[
        "Package.swift",
        # KMP iOS entry points
        "iosApp/",
        "iosMain/",
    ],
    treesitter_spec=SWIFT_SPEC,
    zone_rules=_SWIFT_ZONE_RULES,
)


# ── iOS detector registration ────────────────────────────────


def _register_ios_detectors() -> None:
    """Register iOS-specific detectors and scoring policies."""
    from desloppify.core.registry import DetectorMeta, register_detector
    from desloppify.engine._scoring.policy.core import (
        SECURITY_EXCLUDED_ZONES,
        DetectorScoringPolicy,
        register_scoring_policy,
    )

    _defs: list[tuple[DetectorMeta, DetectorScoringPolicy]] = [
        (
            DetectorMeta(
                "info_plist", "Info.plist", "Security", "manual_fix",
                "fix Info.plist security and configuration issues",
            ),
            DetectorScoringPolicy(
                "info_plist", "Security", 4,
                excluded_zones=SECURITY_EXCLUDED_ZONES,
            ),
        ),
        (
            DetectorMeta(
                "swift_code", "Swift code quality", "Code quality", "manual_fix",
                "fix Swift code quality issues -- deprecated APIs, force unwrap, secrets",
            ),
            DetectorScoringPolicy("swift_code", "Code quality", 3, file_based=True),
        ),
        (
            DetectorMeta(
                "ios_deps", "iOS dependencies", "Code quality", "manual_fix",
                "fix iOS dependency management issues -- lockfiles, version constraints",
            ),
            DetectorScoringPolicy("ios_deps", "Code quality", 3),
        ),
    ]

    for meta, policy in _defs:
        register_detector(meta)
        register_scoring_policy(policy)


# ── Phase functions ───────────────────────────────────────────


def phase_info_plist(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Scan Info.plist files for iOS configuration issues."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.swift.detectors.info_plist import (
        detect_info_plist_issues,
    )

    raw = detect_info_plist_issues(path)
    findings = [
        make_finding(
            "info_plist",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"info_plist": 1}


def phase_swift_code(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Detect Swift code quality issues."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.swift.detectors.swift_code import (
        detect_swift_code_issues,
    )

    files = lang.file_finder(path) if lang.file_finder else []
    raw = detect_swift_code_issues(files)
    findings = [
        make_finding(
            "swift_code",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"swift_code": len(files)}


def phase_ios_deps(path: Path, lang: Any) -> tuple[list[dict], dict[str, int]]:
    """Check iOS dependency management."""
    from desloppify.engine._state.filtering import make_finding
    from desloppify.languages.swift.detectors.ios_deps import (
        detect_ios_dependency_issues,
    )

    raw = detect_ios_dependency_issues(path)
    findings = [
        make_finding(
            "ios_deps",
            e["file"], "",
            tier=e["tier"],
            confidence=e["confidence"],
            summary=e["summary"],
            detail=e.get("detail"),
        )
        for e in raw
    ]
    return findings, {"ios_deps": 1}


# ── Wire phases into config ──────────────────────────────────

_register_ios_detectors()

# Insert iOS phases before the shared tail phases (Security, Subjective review, etc.)
_ios_phases = [
    DetectorPhase("Info.plist", phase_info_plist),
    DetectorPhase("Swift code quality", phase_swift_code),
    DetectorPhase("iOS dependencies", phase_ios_deps),
]

# Find insertion point: before "Security" or at the end
_insert_idx = len(_cfg.phases)
for _i, _p in enumerate(_cfg.phases):
    if _p.label == "Security":
        _insert_idx = _i
        break

for _offset, _phase in enumerate(_ios_phases):
    _cfg.phases.insert(_insert_idx + _offset, _phase)
