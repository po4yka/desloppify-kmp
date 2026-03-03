"""Tests for Swift code detector."""

from __future__ import annotations

from desloppify.languages.swift.detectors.swift_code import detect_swift_code_issues


def _has_kind(findings, kind):
    return any(f["detail"]["kind"] == kind for f in findings)


def _scan(code: str) -> list[dict]:
    path = "Sources/App/ViewController.swift"
    return detect_swift_code_issues([path], read_fn=lambda _: code)


class TestUIWebView:
    def test_detects_uiwebview(self):
        assert _has_kind(_scan("let view = UIWebView()"), "uiwebview_deprecated")

    def test_no_flag_wkwebview(self):
        assert not _has_kind(_scan("let view = WKWebView()"), "uiwebview_deprecated")


class TestMainSyncDeadlock:
    def test_detects_main_sync(self):
        assert _has_kind(_scan("DispatchQueue.main.sync { }"), "main_sync_deadlock")

    def test_no_flag_main_async(self):
        assert not _has_kind(_scan("DispatchQueue.main.async { }"), "main_sync_deadlock")


class TestHardcodedSecret:
    def test_detects_google_api_key(self):
        code = 'let key = "AIzaSyA1234567890abcdefghijklmnopqrs_uX"'
        assert _has_kind(_scan(code), "hardcoded_secret")

    def test_detects_aws_key(self):
        code = 'let key = "AKIAIOSFODNN7EXAMPLE"'
        assert _has_kind(_scan(code), "hardcoded_secret")

    def test_no_flag_normal_string(self):
        code = 'let name = "hello world"'
        assert not _has_kind(_scan(code), "hardcoded_secret")


class TestForceTry:
    def test_detects_force_try(self):
        assert _has_kind(_scan("let data = try! Data(contentsOf: url)"), "force_try")

    def test_no_flag_try_optional(self):
        assert not _has_kind(_scan("let data = try? Data(contentsOf: url)"), "force_try")


class TestForceCast:
    def test_detects_force_cast(self):
        assert _has_kind(_scan("let vc = controller as! MyViewController"), "force_cast")

    def test_no_flag_optional_cast(self):
        assert not _has_kind(_scan("let vc = controller as? MyViewController"), "force_cast")


class TestDeprecatedUIAlertView:
    def test_detects_uialertview(self):
        assert _has_kind(_scan("let alert = UIAlertView()"), "deprecated_uialertview")

    def test_detects_uiactionsheet(self):
        assert _has_kind(_scan("let sheet = UIActionSheet()"), "deprecated_uialertview")

    def test_no_flag_uialertcontroller(self):
        assert not _has_kind(_scan("let alert = UIAlertController()"), "deprecated_uialertview")


class TestDeprecatedUISearchDisplay:
    def test_detects_searchdisplaycontroller(self):
        assert _has_kind(_scan("var search: UISearchDisplayController"), "deprecated_uisearchdisplay")

    def test_no_flag_searchcontroller(self):
        assert not _has_kind(_scan("var search: UISearchController"), "deprecated_uisearchdisplay")


class TestEmptyCatch:
    def test_detects_empty_catch(self):
        code = """
do {
    try something()
} catch { }
"""
        assert _has_kind(_scan(code), "empty_catch")

    def test_detects_catch_with_only_comment(self):
        code = """
do {
    try something()
} catch { // ignore }
"""
        assert _has_kind(_scan(code), "empty_catch")

    def test_no_flag_catch_with_body(self):
        code = """
do {
    try something()
} catch {
    print(error)
}
"""
        assert not _has_kind(_scan(code), "empty_catch")

    def test_skips_non_swift_files(self):
        findings = detect_swift_code_issues(
            ["readme.md"], read_fn=lambda _: "try!"
        )
        assert len(findings) == 0
