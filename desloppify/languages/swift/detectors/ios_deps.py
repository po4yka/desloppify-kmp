"""Detect iOS dependency management issues."""

from __future__ import annotations

import re
from pathlib import Path


def detect_ios_dependency_issues(
    scan_root: str | Path,
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Check for iOS dependency management issues (CocoaPods, SPM)."""
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []
    root = Path(scan_root)

    # CocoaPods checks
    podfile = root / "Podfile"
    if podfile.exists():
        if not (root / "Podfile.lock").exists():
            findings.append({
                "file": "Podfile",
                "line": 1,
                "summary": "Podfile exists but Podfile.lock is missing -- run pod install and commit the lockfile",
                "detail": {"kind": "podfile_lock_missing"},
                "tier": 1,
                "confidence": "high",
            })

        content = _read(str(podfile))
        if content:
            # Pods without version constraints
            for m in re.finditer(
                r"^\s*pod\s+['\"]([^'\"]+)['\"]\s*$",
                content,
                re.MULTILINE,
            ):
                pod_name = m.group(1)
                findings.append({
                    "file": "Podfile",
                    "line": content[:m.start()].count("\n") + 1,
                    "summary": f"Pod '{pod_name}' has no version constraint",
                    "detail": {"kind": "pods_no_version", "pod": pod_name},
                    "tier": 2,
                    "confidence": "high",
                })

    # Swift Package Manager checks
    package_swift = root / "Package.swift"
    if package_swift.exists():
        if not (root / "Package.resolved").exists():
            findings.append({
                "file": "Package.swift",
                "line": 1,
                "summary": "Package.swift exists but Package.resolved is missing -- resolve and commit the lockfile",
                "detail": {"kind": "package_resolved_missing"},
                "tier": 2,
                "confidence": "medium",
            })

    return findings
