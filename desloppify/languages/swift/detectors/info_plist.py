"""Detect security and configuration issues in Info.plist files."""

from __future__ import annotations

import re
from pathlib import Path

_SKIP_DIRS = {"build", "DerivedData", "Pods", ".build"}


def detect_info_plist_issues(
    scan_root: str | Path,
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Scan Info.plist and PrivacyInfo.xcprivacy files for common iOS issues."""
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []
    root = Path(scan_root)

    plists = _find_plists(root)
    for plist in plists:
        rel = str(plist.relative_to(root))
        content = _read(str(plist))
        if content is None:
            continue
        findings.extend(_check_info_plist(rel, content))

    # Check for missing PrivacyInfo.xcprivacy when iOS project detected
    if plists and not _find_privacy_manifests(root):
        findings.append({
            "file": str(plists[0].relative_to(root)),
            "line": 1,
            "summary": "No PrivacyInfo.xcprivacy found -- required for App Store submission since Spring 2024",
            "detail": {"kind": "missing_privacy_manifest"},
            "tier": 1,
            "confidence": "medium",
        })

    return findings


def _find_plists(root: Path) -> list[Path]:
    result = []
    for p in root.rglob("Info.plist"):
        parts = set(p.relative_to(root).parts)
        if not parts & _SKIP_DIRS:
            result.append(p)
    return result


def _find_privacy_manifests(root: Path) -> list[Path]:
    result = []
    for p in root.rglob("PrivacyInfo.xcprivacy"):
        parts = set(p.relative_to(root).parts)
        if not parts & _SKIP_DIRS:
            result.append(p)
    return result


def _plist_value(content: str, key: str) -> str | None:
    """Extract the value element following a <key>key</key> in plist XML."""
    pattern = rf"<key>{re.escape(key)}</key>\s*(<[^/][^>]*(?:/>|>[^<]*</[^>]+>)|<true\s*/>|<false\s*/>)"
    m = re.search(pattern, content)
    if m:
        return m.group(1).strip()
    return None


def _plist_has_key(content: str, key: str) -> bool:
    return bool(re.search(rf"<key>{re.escape(key)}</key>", content))


def _check_info_plist(filepath: str, content: str) -> list[dict]:
    findings: list[dict] = []

    # ATS disabled
    val = _plist_value(content, "NSAllowsArbitraryLoads")
    if val and "<true" in val:
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "NSAllowsArbitraryLoads is true -- App Transport Security is disabled",
            "detail": {"kind": "ats_disabled"},
            "tier": 1,
            "confidence": "high",
        })

    # Missing CFBundleIdentifier
    if not _plist_has_key(content, "CFBundleIdentifier"):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "Missing CFBundleIdentifier in Info.plist",
            "detail": {"kind": "missing_bundle_id"},
            "tier": 1,
            "confidence": "high",
        })
    else:
        # Placeholder bundle ID
        bundle_val = _plist_value(content, "CFBundleIdentifier")
        if bundle_val and "com.example" in bundle_val:
            findings.append({
                "file": filepath,
                "line": 1,
                "summary": "Bundle ID contains com.example placeholder",
                "detail": {"kind": "placeholder_bundle_id"},
                "tier": 1,
                "confidence": "high",
            })

    # Missing version keys
    for key, kind in [
        ("CFBundleVersion", "missing_bundle_version"),
        ("CFBundleShortVersionString", "missing_bundle_version"),
    ]:
        if not _plist_has_key(content, key):
            findings.append({
                "file": filepath,
                "line": 1,
                "summary": f"Missing {key} in Info.plist",
                "detail": {"kind": kind, "key": key},
                "tier": 1,
                "confidence": "high",
            })

    # ATS exception allowing insecure HTTP for non-localhost
    for m in re.finditer(
        r"<key>([^<]+)</key>\s*<dict>(.*?)</dict>",
        content,
        re.DOTALL,
    ):
        domain = m.group(1)
        block = m.group(2)
        if "NSExceptionAllowsInsecureHTTPLoads" in block and "<true" in block:
            if domain not in ("localhost", "127.0.0.1", "::1"):
                findings.append({
                    "file": filepath,
                    "line": 1,
                    "summary": f"ATS exception allows insecure HTTP for {domain}",
                    "detail": {"kind": "ats_exception_http", "domain": domain},
                    "tier": 2,
                    "confidence": "high",
                })

    # Missing encryption key
    if not _plist_has_key(content, "ITSAppUsesNonExemptEncryption"):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "Missing ITSAppUsesNonExemptEncryption -- causes App Store review delays",
            "detail": {"kind": "missing_encryption_key"},
            "tier": 2,
            "confidence": "medium",
        })

    # Min TLS too low
    val = _plist_value(content, "NSExceptionMinimumTLSVersion")
    if val:
        for old_ver in ("TLSv1.0", "TLSv1.1"):
            if old_ver in val:
                findings.append({
                    "file": filepath,
                    "line": 1,
                    "summary": f"NSExceptionMinimumTLSVersion set to {old_ver} -- use TLS 1.2+",
                    "detail": {"kind": "min_tls_too_low", "version": old_ver},
                    "tier": 2,
                    "confidence": "high",
                })
                break

    return findings
