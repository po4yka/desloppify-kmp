"""Tests for KMP source set utility functions."""

from __future__ import annotations

import pytest

from desloppify.languages.kotlin.detectors.kmp_utils import (
    get_source_set,
    is_common_main,
    is_platform_source_set,
    is_test_source_set,
)


class TestGetSourceSet:
    def test_common_main(self):
        assert get_source_set("src/commonMain/kotlin/Foo.kt") == "commonMain"

    def test_android_main(self):
        assert get_source_set("src/androidMain/kotlin/Foo.kt") == "androidMain"

    def test_ios_main(self):
        assert get_source_set("src/iosMain/kotlin/Foo.kt") == "iosMain"

    def test_common_test(self):
        assert get_source_set("src/commonTest/kotlin/FooTest.kt") == "commonTest"

    def test_jvm_main(self):
        assert get_source_set("src/jvmMain/kotlin/Foo.kt") == "jvmMain"

    def test_no_source_set(self):
        assert get_source_set("src/main/kotlin/Foo.kt") is None

    def test_nested_path(self):
        assert get_source_set("module/src/iosArm64Main/kotlin/platform/Foo.kt") == "iosArm64Main"


class TestIsCommonMain:
    def test_common_main_true(self):
        assert is_common_main("src/commonMain/kotlin/Foo.kt") is True

    def test_android_main_false(self):
        assert is_common_main("src/androidMain/kotlin/Foo.kt") is False


class TestIsTestSourceSet:
    def test_common_test(self):
        assert is_test_source_set("src/commonTest/kotlin/FooTest.kt") is True

    def test_android_test(self):
        assert is_test_source_set("src/androidTest/kotlin/FooTest.kt") is True

    def test_common_main_not_test(self):
        assert is_test_source_set("src/commonMain/kotlin/Foo.kt") is False


class TestIsPlatformSourceSet:
    def test_android_main(self):
        assert is_platform_source_set("src/androidMain/kotlin/Foo.kt") is True

    def test_ios_main(self):
        assert is_platform_source_set("src/iosMain/kotlin/Foo.kt") is True

    def test_common_main_not_platform(self):
        assert is_platform_source_set("src/commonMain/kotlin/Foo.kt") is False
