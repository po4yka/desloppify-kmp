"""Tests for Info.plist detector."""

from __future__ import annotations

from desloppify.languages.swift.detectors.info_plist import _check_info_plist


def _has_kind(findings, kind):
    return any(f["detail"]["kind"] == kind for f in findings)


class TestAtsDisabled:
    def test_detects_arbitrary_loads_true(self):
        content = """
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
"""
        assert _has_kind(_check_info_plist("Info.plist", content), "ats_disabled")

    def test_no_flag_arbitrary_loads_false(self):
        content = """
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
</dict>
"""
        assert not _has_kind(_check_info_plist("Info.plist", content), "ats_disabled")


class TestMissingBundleId:
    def test_detects_missing_bundle_id(self):
        content = """
<dict>
    <key>CFBundleName</key>
    <string>MyApp</string>
</dict>
"""
        assert _has_kind(_check_info_plist("Info.plist", content), "missing_bundle_id")

    def test_no_flag_with_bundle_id(self):
        content = """
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.mycompany.myapp</string>
</dict>
"""
        assert not _has_kind(_check_info_plist("Info.plist", content), "missing_bundle_id")


class TestPlaceholderBundleId:
    def test_detects_example_placeholder(self):
        content = """
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.example.myapp</string>
</dict>
"""
        assert _has_kind(_check_info_plist("Info.plist", content), "placeholder_bundle_id")

    def test_no_flag_real_bundle_id(self):
        content = """
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.mycompany.myapp</string>
</dict>
"""
        assert not _has_kind(_check_info_plist("Info.plist", content), "placeholder_bundle_id")


class TestMissingBundleVersion:
    def test_detects_missing_version(self):
        content = """
<dict>
    <key>CFBundleName</key>
    <string>MyApp</string>
</dict>
"""
        findings = _check_info_plist("Info.plist", content)
        version_findings = [f for f in findings if f["detail"]["kind"] == "missing_bundle_version"]
        assert len(version_findings) == 2  # both CFBundleVersion and CFBundleShortVersionString

    def test_no_flag_with_versions(self):
        content = """
<dict>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
</dict>
"""
        assert not _has_kind(_check_info_plist("Info.plist", content), "missing_bundle_version")


class TestAtsExceptionHttp:
    def test_detects_insecure_http_exception(self):
        content = """
<dict>
    <key>api.example.com</key>
    <dict>
        <key>NSExceptionAllowsInsecureHTTPLoads</key>
        <true/>
    </dict>
</dict>
"""
        assert _has_kind(_check_info_plist("Info.plist", content), "ats_exception_http")

    def test_no_flag_localhost(self):
        content = """
<dict>
    <key>localhost</key>
    <dict>
        <key>NSExceptionAllowsInsecureHTTPLoads</key>
        <true/>
    </dict>
</dict>
"""
        assert not _has_kind(_check_info_plist("Info.plist", content), "ats_exception_http")


class TestMissingEncryptionKey:
    def test_detects_missing_encryption(self):
        content = """
<dict>
    <key>CFBundleName</key>
    <string>MyApp</string>
</dict>
"""
        assert _has_kind(_check_info_plist("Info.plist", content), "missing_encryption_key")

    def test_no_flag_with_encryption_key(self):
        content = """
<dict>
    <key>ITSAppUsesNonExemptEncryption</key>
    <false/>
</dict>
"""
        assert not _has_kind(_check_info_plist("Info.plist", content), "missing_encryption_key")


class TestMinTlsTooLow:
    def test_detects_tls_1_0(self):
        content = """
<dict>
    <key>NSExceptionMinimumTLSVersion</key>
    <string>TLSv1.0</string>
</dict>
"""
        assert _has_kind(_check_info_plist("Info.plist", content), "min_tls_too_low")

    def test_detects_tls_1_1(self):
        content = """
<dict>
    <key>NSExceptionMinimumTLSVersion</key>
    <string>TLSv1.1</string>
</dict>
"""
        assert _has_kind(_check_info_plist("Info.plist", content), "min_tls_too_low")

    def test_no_flag_tls_1_2(self):
        content = """
<dict>
    <key>NSExceptionMinimumTLSVersion</key>
    <string>TLSv1.2</string>
</dict>
"""
        assert not _has_kind(_check_info_plist("Info.plist", content), "min_tls_too_low")
