"""Tests for build file analyzer."""

from __future__ import annotations

import pytest

from desloppify.languages.kotlin.detectors.build_files import (
    _check_gradle,
    _check_version_catalog,
    _parse_major_minor,
)


class TestCheckGradle:
    def test_missing_simulator_target(self):
        content = """
kotlin {
    iosArm64()
    androidTarget()
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert any("iosSimulatorArm64" in f["summary"] for f in findings)

    def test_simulator_target_present(self):
        content = """
kotlin {
    iosArm64()
    iosSimulatorArm64()
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not any("iosSimulatorArm64" in f["summary"] for f in findings)

    def test_missing_expect_actual_flag(self):
        content = """
kotlin {
    multiplatform
}
expect class Foo
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert any("Xexpect-actual-classes" in f["summary"] for f in findings)


class TestCheckVersionCatalog:
    def test_old_kotlin_version(self):
        content = """
[versions]
kotlin = "1.8.0"
compose-multiplatform = "1.5.0"
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert len(findings) == 1
        assert "1.8.0" in findings[0]["summary"]

    def test_compatible_versions(self):
        content = """
[versions]
kotlin = "2.0.0"
compose-multiplatform = "1.6.0"
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert len(findings) == 0


class TestParseMajorMinor:
    def test_normal_version(self):
        assert _parse_major_minor("1.9.20") == (1, 9)

    def test_two_part(self):
        assert _parse_major_minor("2.0") == (2, 0)

    def test_invalid(self):
        assert _parse_major_minor("latest") is None
