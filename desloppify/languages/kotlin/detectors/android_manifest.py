"""Detect security and configuration issues in AndroidManifest.xml files."""

from __future__ import annotations

import re
from pathlib import Path

# Skip build output and Gradle cache directories
_SKIP_DIRS = {"build", ".gradle", ".idea"}

# Patterns for API key detection in manifest values
_API_KEY_RE = re.compile(
    r'android:value\s*=\s*"('
    r"AIza[0-9A-Za-z_-]{35}"  # Google API key
    r"|[A-Za-z0-9_-]{32,}"  # generic long alphanumeric
    r')"'
)

# Component tags that can be exported
_COMPONENT_TAGS = ("activity", "service", "receiver", "provider")


def detect_android_manifest_issues(
    scan_root: str | Path,
    *,
    read_fn: callable | None = None,
) -> list[dict]:
    """Scan AndroidManifest.xml files for common Android issues."""
    from desloppify.core.source_discovery import read_file_text

    _read = read_fn or read_file_text
    findings: list[dict] = []
    root = Path(scan_root)

    for manifest in _find_manifests(root):
        rel = str(manifest.relative_to(root))
        content = _read(str(manifest))
        if content is None:
            continue
        findings.extend(_check_manifest(rel, content))

    return findings


def _find_manifests(root: Path) -> list[Path]:
    result = []
    for p in root.rglob("AndroidManifest.xml"):
        parts = set(p.relative_to(root).parts)
        if not parts & _SKIP_DIRS:
            result.append(p)
    return result


def _check_manifest(filepath: str, content: str) -> list[dict]:
    findings: list[dict] = []

    # ── Application-level checks ──────────────────────────────

    # debuggable
    if re.search(r'android:debuggable\s*=\s*"true"', content):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "android:debuggable=\"true\" in manifest -- remove for release builds",
            "detail": {"kind": "debuggable_enabled"},
            "tier": 1,
            "confidence": "high",
        })

    # cleartext traffic
    if re.search(r'android:usesCleartextTraffic\s*=\s*"true"', content):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "android:usesCleartextTraffic=\"true\" allows unencrypted HTTP",
            "detail": {"kind": "cleartext_traffic"},
            "tier": 1,
            "confidence": "high",
        })

    # allowBackup without rules
    if re.search(r'android:allowBackup\s*=\s*"true"', content):
        has_rules = bool(
            re.search(r'android:fullBackupContent\s*=', content)
            or re.search(r'android:dataExtractionRules\s*=', content)
        )
        if not has_rules:
            findings.append({
                "file": filepath,
                "line": 1,
                "summary": "android:allowBackup=\"true\" without backup rules -- add fullBackupContent or dataExtractionRules",
                "detail": {"kind": "allow_backup_no_rules"},
                "tier": 2,
                "confidence": "medium",
            })

    # missing networkSecurityConfig on <application>
    app_match = re.search(r"<application\b[^>]*>", content, re.DOTALL)
    if app_match:
        app_tag = app_match.group(0)
        if "networkSecurityConfig" not in app_tag:
            findings.append({
                "file": filepath,
                "line": 1,
                "summary": "No android:networkSecurityConfig on <application> -- consider adding network security config",
                "detail": {"kind": "missing_network_security_config"},
                "tier": 2,
                "confidence": "medium",
            })

    # hardcoded API keys in manifest
    for m in _API_KEY_RE.finditer(content):
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": "Possible hardcoded API key in manifest android:value",
            "detail": {"kind": "hardcoded_manifest_key", "snippet": m.group(1)[:20] + "..."},
            "tier": 1,
            "confidence": "medium",
        })

    # ── Component-level checks ────────────────────────────────

    # Extract each component tag block
    for tag in _COMPONENT_TAGS:
        for m in re.finditer(
            rf"<{tag}\b([^>]*?)(/?>)",
            content,
            re.DOTALL,
        ):
            attrs = m.group(0)
            _check_component(filepath, tag, attrs, content, m.start(), findings)

    return findings


def _check_component(
    filepath: str,
    tag: str,
    tag_text: str,
    full_content: str,
    tag_start: int,
    findings: list[dict],
) -> None:
    has_exported_true = bool(re.search(r'android:exported\s*=\s*"true"', tag_text))
    has_exported_attr = bool(re.search(r'android:exported\s*=', tag_text))
    has_permission = bool(re.search(r'android:permission\s*=', tag_text))

    # Check if this component has an intent-filter
    # Look for <intent-filter> between this tag and its closing tag
    has_intent_filter = _component_has_intent_filter(tag, tag_text, tag_start, full_content)

    # exported=true without permission
    if has_exported_true and not has_permission:
        name = _extract_name(tag_text)
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": f"Exported {tag} {name} has no android:permission -- any app can invoke it",
            "detail": {"kind": "exported_no_permission", "component": tag, "name": name},
            "tier": 1,
            "confidence": "medium",
        })

    # intent-filter without exported attribute (crashes on API 31+)
    if has_intent_filter and not has_exported_attr:
        name = _extract_name(tag_text)
        findings.append({
            "file": filepath,
            "line": 1,
            "summary": f"{tag} {name} has <intent-filter> but no android:exported -- crashes on API 31+",
            "detail": {"kind": "missing_exported_attr", "component": tag, "name": name},
            "tier": 1,
            "confidence": "high",
        })


def _component_has_intent_filter(
    tag: str, tag_text: str, tag_start: int, full_content: str
) -> bool:
    """Check if the component starting at tag_start has an <intent-filter> child."""
    # Self-closing tags can't have children
    if tag_text.rstrip().endswith("/>"):
        return False
    # Find closing tag
    close_tag = f"</{tag}>"
    close_idx = full_content.find(close_tag, tag_start)
    if close_idx == -1:
        return False
    block = full_content[tag_start:close_idx]
    return "<intent-filter" in block


def _extract_name(tag_text: str) -> str:
    m = re.search(r'android:name\s*=\s*"([^"]*)"', tag_text)
    return m.group(1) if m else "(unnamed)"
