"""Analyze build.gradle.kts and libs.versions.toml for KMP issues."""

from __future__ import annotations

import re
from pathlib import Path


def detect_build_issues(
    scan_root: str | Path,
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []
    root = Path(scan_root)

    # Scan all build.gradle.kts files
    for gradle_file in _find_gradle_files(root):
        rel = str(gradle_file.relative_to(root))
        content = _read(str(gradle_file))
        if content is None:
            continue
        findings.extend(_check_gradle(rel, content))

    # Scan libs.versions.toml
    toml_path = root / "gradle" / "libs.versions.toml"
    if toml_path.exists():
        content = _read(str(toml_path))
        if content:
            findings.extend(_check_version_catalog(
                str(toml_path.relative_to(root)), content
            ))

    return findings


def _find_gradle_files(root: Path) -> list[Path]:
    result = []
    for p in root.rglob("build.gradle.kts"):
        if "build/" not in str(p) and ".gradle/" not in str(p):
            result.append(p)
    return result


def _check_gradle(filepath: str, content: str) -> list[dict]:
    findings = []

    # Missing iosSimulatorArm64 target
    if "iosArm64()" in content and "iosSimulatorArm64()" not in content:
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "Missing iosSimulatorArm64() target (needed for simulator)",
            "detail": {"kind": "missing_simulator_target"},
            "tier": 2,
            "confidence": "high",
        })

    # Missing -Xexpect-actual-classes
    if re.search(r"\bexpect\b", content) or "expect " in content:
        if "-Xexpect-actual-classes" not in content:
            # Only flag if this is likely a KMP module
            if "kotlin {" in content or "multiplatform" in content:
                findings.append({
                    "file": filepath,
                    "line": 1,
                    "summary": "Missing -Xexpect-actual-classes compiler arg",
                    "detail": {"kind": "missing_expect_actual_flag"},
                    "tier": 2,
                    "confidence": "medium",
                })

    return findings


def _check_version_catalog(filepath: str, content: str) -> list[dict]:
    findings = []

    # Extract versions
    versions: dict[str, str] = {}
    for m in re.finditer(r'^(\w[\w-]*)\s*=\s*"([^"]+)"', content, re.MULTILINE):
        versions[m.group(1)] = m.group(2)

    # Check Kotlin/Compose version compatibility
    kotlin_ver = versions.get("kotlin")
    compose_ver = versions.get("compose-multiplatform") or versions.get("compose-plugin")
    if kotlin_ver and compose_ver:
        # Basic major version sanity check
        kt_major = _parse_major_minor(kotlin_ver)
        if kt_major and kt_major < (1, 9):
            findings.append({
                "file": filepath,
                "line": 1,
                "summary": f"Kotlin {kotlin_ver} may not support Compose Multiplatform {compose_ver}",
                "detail": {"kind": "version_mismatch", "kotlin": kotlin_ver, "compose": compose_ver},
                "tier": 1,
                "confidence": "medium",
            })

    return findings


def _parse_major_minor(version: str) -> tuple[int, int] | None:
    m = re.match(r"(\d+)\.(\d+)", version)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return None
