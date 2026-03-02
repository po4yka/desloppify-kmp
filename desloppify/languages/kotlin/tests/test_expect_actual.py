"""Tests for expect/actual detector."""

from __future__ import annotations

import pytest

from desloppify.languages.kotlin.detectors.expect_actual import (
    detect_expect_actual,
)


def _make_read_fn(file_contents: dict[str, str]):
    def read_fn(path):
        return file_contents.get(path)
    return read_fn


class TestExpectActual:
    def test_missing_actual(self):
        files = [
            "src/commonMain/kotlin/Platform.kt",
        ]
        content = {
            "src/commonMain/kotlin/Platform.kt": "expect fun getPlatformName(): String\n",
        }
        findings = detect_expect_actual(files, read_fn=_make_read_fn(content))
        missing = [f for f in findings if f["detail"]["kind"] == "missing_actual"]
        assert len(missing) == 1
        assert "getPlatformName" in missing[0]["summary"]

    def test_complete_expect_actual(self):
        files = [
            "src/commonMain/kotlin/Platform.kt",
            "src/androidMain/kotlin/Platform.kt",
        ]
        content = {
            "src/commonMain/kotlin/Platform.kt": "expect fun getPlatformName(): String\n",
            "src/androidMain/kotlin/Platform.kt": "actual fun getPlatformName(): String = \"Android\"\n",
        }
        findings = detect_expect_actual(files, read_fn=_make_read_fn(content))
        missing = [f for f in findings if f["detail"]["kind"] == "missing_actual"]
        assert len(missing) == 0

    def test_expect_class_with_body(self):
        files = [
            "src/commonMain/kotlin/Platform.kt",
            "src/androidMain/kotlin/Platform.kt",
        ]
        content = {
            "src/commonMain/kotlin/Platform.kt": (
                "expect class Platform {\n"
                "    fun getName(): String\n"
                "}\n"
            ),
            "src/androidMain/kotlin/Platform.kt": (
                "actual class Platform {\n"
                "    actual fun getName(): String = \"Android\"\n"
                "}\n"
            ),
        }
        findings = detect_expect_actual(files, read_fn=_make_read_fn(content))
        body = [f for f in findings if f["detail"]["kind"] == "expect_class_body"]
        assert len(body) == 1

    def test_non_kt_files_ignored(self):
        files = ["build.gradle.kts"]
        content = {
            "build.gradle.kts": "expect something\n",
        }
        findings = detect_expect_actual(files, read_fn=_make_read_fn(content))
        assert len(findings) == 0
