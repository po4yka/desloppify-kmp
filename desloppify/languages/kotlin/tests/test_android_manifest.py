"""Tests for Android manifest detector."""

from __future__ import annotations

from desloppify.languages.kotlin.detectors.android_manifest import _check_manifest


def _has_kind(findings, kind):
    return any(f["detail"]["kind"] == kind for f in findings)


class TestDebuggable:
    def test_detects_debuggable_true(self):
        content = '<application android:debuggable="true" />'
        assert _has_kind(_check_manifest("AndroidManifest.xml", content), "debuggable_enabled")

    def test_no_flag_debuggable_false(self):
        content = '<application android:debuggable="false" />'
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "debuggable_enabled")


class TestCleartextTraffic:
    def test_detects_cleartext_true(self):
        content = '<application android:usesCleartextTraffic="true" />'
        assert _has_kind(_check_manifest("AndroidManifest.xml", content), "cleartext_traffic")

    def test_no_flag_cleartext_false(self):
        content = '<application android:usesCleartextTraffic="false" />'
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "cleartext_traffic")


class TestAllowBackup:
    def test_detects_backup_without_rules(self):
        content = '<application android:allowBackup="true" />'
        assert _has_kind(_check_manifest("AndroidManifest.xml", content), "allow_backup_no_rules")

    def test_no_flag_with_full_backup_content(self):
        content = '<application android:allowBackup="true" android:fullBackupContent="@xml/backup" />'
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "allow_backup_no_rules")

    def test_no_flag_with_data_extraction_rules(self):
        content = '<application android:allowBackup="true" android:dataExtractionRules="@xml/rules" />'
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "allow_backup_no_rules")


class TestNetworkSecurityConfig:
    def test_detects_missing_config(self):
        content = '<application android:name=".App">'
        assert _has_kind(_check_manifest("AndroidManifest.xml", content), "missing_network_security_config")

    def test_no_flag_with_config(self):
        content = '<application android:name=".App" android:networkSecurityConfig="@xml/network">'
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "missing_network_security_config")


class TestHardcodedKey:
    def test_detects_google_api_key(self):
        content = '<meta-data android:name="com.google.android.geo.API_KEY" android:value="AIzaSyA1234567890abcdefghijklmnopqrstu" />'
        assert _has_kind(_check_manifest("AndroidManifest.xml", content), "hardcoded_manifest_key")

    def test_no_flag_placeholder(self):
        content = '<meta-data android:name="key" android:value="TODO" />'
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "hardcoded_manifest_key")


class TestExportedNoPermission:
    def test_detects_exported_without_permission(self):
        content = """
<activity android:name=".MainActivity" android:exported="true">
</activity>
"""
        assert _has_kind(_check_manifest("AndroidManifest.xml", content), "exported_no_permission")

    def test_no_flag_with_permission(self):
        content = """
<activity android:name=".MainActivity" android:exported="true" android:permission="com.example.PERM">
</activity>
"""
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "exported_no_permission")

    def test_no_flag_exported_false(self):
        content = """
<activity android:name=".MainActivity" android:exported="false">
</activity>
"""
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "exported_no_permission")


class TestMissingExportedAttr:
    def test_detects_intent_filter_without_exported(self):
        content = """
<activity android:name=".MainActivity">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
    </intent-filter>
</activity>
"""
        assert _has_kind(_check_manifest("AndroidManifest.xml", content), "missing_exported_attr")

    def test_no_flag_with_exported(self):
        content = """
<activity android:name=".MainActivity" android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
    </intent-filter>
</activity>
"""
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "missing_exported_attr")

    def test_no_flag_no_intent_filter(self):
        content = """
<activity android:name=".DetailActivity">
</activity>
"""
        assert not _has_kind(_check_manifest("AndroidManifest.xml", content), "missing_exported_attr")

    def test_detects_on_service(self):
        content = """
<service android:name=".MyService">
    <intent-filter>
        <action android:name="com.example.START" />
    </intent-filter>
</service>
"""
        assert _has_kind(_check_manifest("AndroidManifest.xml", content), "missing_exported_attr")
