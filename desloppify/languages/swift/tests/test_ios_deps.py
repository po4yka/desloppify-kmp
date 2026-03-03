"""Tests for iOS dependency detector."""

from __future__ import annotations

from desloppify.languages.swift.detectors.ios_deps import detect_ios_dependency_issues


def _has_kind(findings, kind):
    return any(f["detail"]["kind"] == kind for f in findings)


class TestPodfileLockMissing:
    def test_detects_missing_lock(self, tmp_path):
        (tmp_path / "Podfile").write_text("pod 'Alamofire', '~> 5.0'\n")
        findings = detect_ios_dependency_issues(tmp_path)
        assert _has_kind(findings, "podfile_lock_missing")

    def test_no_flag_with_lock(self, tmp_path):
        (tmp_path / "Podfile").write_text("pod 'Alamofire', '~> 5.0'\n")
        (tmp_path / "Podfile.lock").write_text("PODS:\n")
        findings = detect_ios_dependency_issues(tmp_path)
        assert not _has_kind(findings, "podfile_lock_missing")

    def test_no_flag_no_podfile(self, tmp_path):
        findings = detect_ios_dependency_issues(tmp_path)
        assert not _has_kind(findings, "podfile_lock_missing")


class TestPodsNoVersion:
    def test_detects_pod_without_version(self, tmp_path):
        (tmp_path / "Podfile").write_text("pod 'Alamofire'\n")
        (tmp_path / "Podfile.lock").write_text("PODS:\n")
        findings = detect_ios_dependency_issues(tmp_path)
        assert _has_kind(findings, "pods_no_version")

    def test_no_flag_with_version(self, tmp_path):
        (tmp_path / "Podfile").write_text("pod 'Alamofire', '~> 5.0'\n")
        (tmp_path / "Podfile.lock").write_text("PODS:\n")
        findings = detect_ios_dependency_issues(tmp_path)
        assert not _has_kind(findings, "pods_no_version")


class TestPackageResolvedMissing:
    def test_detects_missing_resolved(self, tmp_path):
        (tmp_path / "Package.swift").write_text("// swift-tools-version:5.9\n")
        findings = detect_ios_dependency_issues(tmp_path)
        assert _has_kind(findings, "package_resolved_missing")

    def test_no_flag_with_resolved(self, tmp_path):
        (tmp_path / "Package.swift").write_text("// swift-tools-version:5.9\n")
        (tmp_path / "Package.resolved").write_text("{}\n")
        findings = detect_ios_dependency_issues(tmp_path)
        assert not _has_kind(findings, "package_resolved_missing")
