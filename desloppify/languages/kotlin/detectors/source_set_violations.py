"""Detect cross-source-set boundary violations in KMP projects."""

from __future__ import annotations

import re

from desloppify.languages.kotlin.detectors.kmp_utils import get_source_set

# Source set dependency DAG — keys may import from values.
_ALLOWED_DEPS: dict[str, frozenset[str]] = {
    "androidMain": frozenset({"commonMain"}),
    "iosMain": frozenset({"commonMain"}),
    "iosArm64Main": frozenset({"commonMain", "iosMain", "appleMain", "nativeMain"}),
    "iosSimulatorArm64Main": frozenset({"commonMain", "iosMain", "appleMain", "nativeMain"}),
    "iosX64Main": frozenset({"commonMain", "iosMain", "appleMain", "nativeMain"}),
    "appleMain": frozenset({"commonMain", "nativeMain"}),
    "jvmMain": frozenset({"commonMain"}),
    "desktopMain": frozenset({"commonMain", "jvmMain"}),
    "nativeMain": frozenset({"commonMain"}),
    "commonTest": frozenset({"commonMain"}),
    "androidTest": frozenset({"commonMain", "androidMain", "commonTest"}),
    "iosTest": frozenset({"commonMain", "iosMain", "commonTest"}),
    "jvmTest": frozenset({"commonMain", "jvmMain", "commonTest"}),
}

_IMPORT_RE = re.compile(r"^import\s+([\w.]+)", re.MULTILINE)


def detect_source_set_violations(
    files: list[str],
    dep_graph: dict | None = None,
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Detect imports that cross source-set boundaries incorrectly.

    This is a heuristic check based on package naming conventions and
    the KMP source set DAG.
    """
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []

    # Build a map of package -> source set from all files
    package_source_sets: dict[str, set[str]] = {}
    for filepath in files:
        if not filepath.endswith(".kt"):
            continue
        ss = get_source_set(filepath)
        if not ss:
            continue
        content = _read(filepath)
        if not content:
            continue
        pkg_match = re.search(r"^package\s+([\w.]+)", content, re.MULTILINE)
        if pkg_match:
            pkg = pkg_match.group(1)
            package_source_sets.setdefault(pkg, set()).add(ss)

    # Check: if a package only exists in a platform source set,
    # and is imported from commonMain, that's a violation.
    for filepath in files:
        if not filepath.endswith(".kt"):
            continue
        ss = get_source_set(filepath)
        if ss != "commonMain":
            continue

        content = _read(filepath)
        if not content:
            continue

        for m in _IMPORT_RE.finditer(content):
            imported_pkg = m.group(1)
            # Check if the imported package root exists only in platform sets
            pkg_root = ".".join(imported_pkg.split(".")[:3])
            source_sets = package_source_sets.get(pkg_root, set())
            platform_only = source_sets and "commonMain" not in source_sets
            if platform_only:
                line = content[:m.start()].count("\n") + 1
                findings.append({
                    "file": filepath,
                    "line": line,
                    "summary": (
                        f"commonMain imports {imported_pkg} which only exists "
                        f"in {', '.join(sorted(source_sets))}"
                    ),
                    "detail": {
                        "kind": "cross_source_set",
                        "imported": imported_pkg,
                        "target_sets": sorted(source_sets),
                    },
                    "tier": 2,
                    "confidence": "medium",
                })

    return findings
