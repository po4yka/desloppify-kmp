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

    # Check if version catalog exists (used by per-file checks)
    has_version_catalog = (root / "gradle" / "libs.versions.toml").exists()

    # Scan all build.gradle.kts files
    for gradle_file in _find_gradle_files(root):
        rel = str(gradle_file.relative_to(root))
        content = _read(str(gradle_file))
        if content is None:
            continue
        findings.extend(_check_gradle(rel, content, has_version_catalog=has_version_catalog))

    # Scan libs.versions.toml
    toml_path = root / "gradle" / "libs.versions.toml"
    if toml_path.exists():
        content = _read(str(toml_path))
        if content:
            findings.extend(_check_version_catalog(
                str(toml_path.relative_to(root)), content
            ))

    # Scan settings files
    for settings_file in _find_settings_files(root):
        rel = str(settings_file.relative_to(root))
        content = _read(str(settings_file))
        if content is None:
            continue
        findings.extend(_check_settings(rel, content))

    # Filesystem-level checks
    findings.extend(_check_buildsrc(root))

    return findings


def _find_gradle_files(root: Path) -> list[Path]:
    result = []
    for p in root.rglob("build.gradle.kts"):
        if "build/" not in str(p) and ".gradle/" not in str(p):
            result.append(p)
    return result


def _check_gradle(
    filepath: str,
    content: str,
    *,
    has_version_catalog: bool = False,
) -> list[dict]:
    findings = []

    is_kmp = "multiplatform" in content or 'kotlin("multiplatform")' in content

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
            if "kotlin {" in content or is_kmp:
                findings.append({
                    "file": filepath,
                    "line": 1,
                    "summary": "Missing -Xexpect-actual-classes compiler arg",
                    "detail": {"kind": "missing_expect_actual_flag"},
                    "tier": 2,
                    "confidence": "medium",
                })

    # A1: Deprecated com.android.library with KMP
    if is_kmp and re.search(r'com\.android\.library', content):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "com.android.library is deprecated for KMP — migrate to com.android.kotlin.multiplatform.library",
            "detail": {"kind": "deprecated_agp_kmp"},
            "tier": 1,
            "confidence": "high",
        })

    # A2: allprojects/subprojects anti-pattern
    if re.search(r'(allprojects|subprojects)\s*\{', content):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "allprojects/subprojects blocks prevent Gradle optimizations — use convention plugins",
            "detail": {"kind": "allprojects_antipattern"},
            "tier": 3,
            "confidence": "medium",
        })

    # A3: Redundant java plugin with Kotlin
    has_kotlin_plugin = bool(re.search(
        r'kotlin\(\s*"(jvm|multiplatform)"\s*\)', content,
    ))
    has_java_plugin = bool(re.search(
        r'''id\(\s*["']java["']\s*\)|plugin\s*\{\s*java\s*\}|apply\s+plugin:\s*["']java["']''',
        content,
    ))
    if has_kotlin_plugin and has_java_plugin:
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "Redundant java plugin — kotlin(\"jvm\"/\"multiplatform\") already applies it",
            "detail": {"kind": "redundant_java_plugin"},
            "tier": 3,
            "confidence": "high",
        })

    # A4: withJava() deprecation
    if "withJava()" in content and is_kmp:
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "withJava() is deprecated in Gradle 8.7+ — remove it from JVM target",
            "detail": {"kind": "deprecated_withjava"},
            "tier": 2,
            "confidence": "medium",
        })

    # A5: kapt usage when KSP available
    if re.search(r'kotlin\(\s*"kapt"\s*\)|org\.jetbrains\.kotlin\.kapt', content):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "kapt is deprecated — migrate to KSP for faster builds",
            "detail": {"kind": "kapt_deprecated"},
            "tier": 3,
            "confidence": "medium",
        })

    # A6: Hardcoded dependency versions (only when version catalog exists)
    if has_version_catalog:
        # Match implementation("group:artifact:1.2.3") patterns
        if re.search(
            r'(implementation|api|compileOnly|runtimeOnly)\s*\(\s*"[^"]+:[^"]+:\d+\.',
            content,
        ):
            findings.append({
                "file": filepath,
                "line": 1,
                "summary": "Hardcoded dependency version — use version catalog (libs.versions.toml) instead",
                "detail": {"kind": "hardcoded_dep_version"},
                "tier": 3,
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

    # B1: Duplicate library entries (same group:artifact)
    libs_section = _extract_toml_section(content, "libraries")
    if libs_section:
        seen_artifacts: dict[str, str] = {}
        # Match module = "group:artifact" or group = "...", name = "..." patterns
        for m in re.finditer(
            r'^(\w[\w-]*)\s*=\s*\{[^}]*module\s*=\s*"([^"]+)"',
            libs_section,
            re.MULTILINE,
        ):
            alias, module = m.group(1), m.group(2)
            if module in seen_artifacts:
                findings.append({
                    "file": filepath,
                    "line": 1,
                    "summary": f"Duplicate catalog entry for {module} (aliases: {seen_artifacts[module]}, {alias})",
                    "detail": {"kind": "duplicate_catalog_entry", "module": module},
                    "tier": 3,
                    "confidence": "high",
                })
            else:
                seen_artifacts[module] = alias
        # Also match short form: alias = "group:artifact:version"
        for m in re.finditer(
            r'^(\w[\w-]*)\s*=\s*"([^":]+:[^":]+)(?::[^"]*)"',
            libs_section,
            re.MULTILINE,
        ):
            alias, module = m.group(1), m.group(2)
            if module in seen_artifacts:
                findings.append({
                    "file": filepath,
                    "line": 1,
                    "summary": f"Duplicate catalog entry for {module} (aliases: {seen_artifacts[module]}, {alias})",
                    "detail": {"kind": "duplicate_catalog_entry", "module": module},
                    "tier": 3,
                    "confidence": "high",
                })
            else:
                seen_artifacts[module] = alias

    # B2: AGP version < 9 warning
    agp_ver = versions.get("agp") or versions.get("android-gradle-plugin")
    if agp_ver:
        agp_major = _parse_major_minor(agp_ver)
        if agp_major and agp_major[0] < 9:
            findings.append({
                "file": filepath,
                "line": 1,
                "summary": f"AGP {agp_ver} is pre-9.0 — plan migration for KMP compatibility",
                "detail": {"kind": "agp_migration_needed", "agp": agp_ver},
                "tier": 2,
                "confidence": "medium",
            })

    return findings


def _find_settings_files(root: Path) -> list[Path]:
    result = []
    for name in ("settings.gradle.kts", "settings.gradle"):
        p = root / name
        if p.exists():
            result.append(p)
    return result


def _check_settings(filepath: str, content: str) -> list[dict]:
    findings = []

    # A2 also applies to settings files
    if re.search(r'(allprojects|subprojects)\s*\{', content):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "allprojects/subprojects blocks prevent Gradle optimizations — use convention plugins",
            "detail": {"kind": "allprojects_antipattern"},
            "tier": 3,
            "confidence": "medium",
        })

    return findings


def _check_buildsrc(root: Path) -> list[dict]:
    if (root / "buildSrc").is_dir():
        return [{
            "file": "buildSrc/",
            "line": 1,
            "summary": "buildSrc forces re-evaluation on every change — consider migrating to an included build (build-logic)",
            "detail": {"kind": "buildsrc_antipattern"},
            "tier": 3,
            "confidence": "low",
        }]
    return []


def _extract_toml_section(content: str, section: str) -> str | None:
    """Extract the content of a TOML section (e.g., [libraries])."""
    pattern = rf'^\[{re.escape(section)}\]\s*\n(.*?)(?=^\[|\Z)'
    m = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else None


def _parse_major_minor(version: str) -> tuple[int, int] | None:
    m = re.match(r"(\d+)\.(\d+)", version)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return None
