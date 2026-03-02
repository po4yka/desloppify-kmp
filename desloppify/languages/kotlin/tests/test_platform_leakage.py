"""Tests for platform leakage detector."""

from __future__ import annotations

import pytest

from desloppify.languages.kotlin.detectors.platform_leakage import (
    detect_platform_leakage,
)


def _make_read_fn(file_contents: dict[str, str]):
    def read_fn(path):
        return file_contents.get(path)
    return read_fn


class TestPlatformLeakage:
    def test_java_import_in_common_main(self):
        files = ["src/commonMain/kotlin/Foo.kt"]
        content = {
            "src/commonMain/kotlin/Foo.kt": "import java.util.Date\nclass Foo {}\n",
        }
        findings = detect_platform_leakage(files, zone_map=None, read_fn=_make_read_fn(content))
        assert len(findings) == 1
        assert findings[0]["tier"] == 1
        assert "java.util" in findings[0]["summary"]

    def test_android_import_in_common_main(self):
        files = ["src/commonMain/kotlin/Bar.kt"]
        content = {
            "src/commonMain/kotlin/Bar.kt": "import android.os.Bundle\nclass Bar {}\n",
        }
        findings = detect_platform_leakage(files, zone_map=None, read_fn=_make_read_fn(content))
        assert len(findings) == 1
        assert findings[0]["tier"] == 1

    def test_no_leakage_in_android_main(self):
        files = ["src/androidMain/kotlin/Foo.kt"]
        content = {
            "src/androidMain/kotlin/Foo.kt": "import android.os.Bundle\nclass Foo {}\n",
        }
        findings = detect_platform_leakage(files, zone_map=None, read_fn=_make_read_fn(content))
        assert len(findings) == 0

    def test_hilt_annotation_in_common_main(self):
        files = ["src/commonMain/kotlin/VM.kt"]
        content = {
            "src/commonMain/kotlin/VM.kt": "@HiltViewModel\nclass MyViewModel {}\n",
        }
        findings = detect_platform_leakage(files, zone_map=None, read_fn=_make_read_fn(content))
        assert len(findings) >= 1
        assert any(f["tier"] == 2 for f in findings)

    def test_clean_common_main(self):
        files = ["src/commonMain/kotlin/Clean.kt"]
        content = {
            "src/commonMain/kotlin/Clean.kt": "package com.example\nclass Clean {}\n",
        }
        findings = detect_platform_leakage(files, zone_map=None, read_fn=_make_read_fn(content))
        assert len(findings) == 0
