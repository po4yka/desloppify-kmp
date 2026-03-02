"""Tests for Kotlin plugin configuration and contract."""

from __future__ import annotations

import pytest

from desloppify.languages import get_lang


class TestKotlinConfig:
    @pytest.fixture()
    def lang(self):
        return get_lang("kotlin")

    def test_name(self, lang):
        assert lang.name == "kotlin"

    def test_extensions(self, lang):
        assert ".kt" in lang.extensions
        assert ".kts" in lang.extensions

    def test_integration_depth(self, lang):
        assert lang.integration_depth == "full"

    def test_phases_not_empty(self, lang):
        assert len(lang.phases) > 0

    def test_kmp_phases_present(self, lang):
        labels = {p.label for p in lang.phases}
        expected = {
            "KMP platform leakage",
            "KMP expect/actual",
            "Coroutine safety",
            "Deprecated K/N patterns",
            "Compose smells",
            "Build config",
        }
        assert expected.issubset(labels), f"Missing: {expected - labels}"

    def test_shared_phases_present(self, lang):
        labels = {p.label for p in lang.phases}
        assert "Security" in labels
        assert "Test coverage" in labels
        assert "Structural analysis" in labels

    def test_detect_markers(self, lang):
        assert "build.gradle.kts" in lang.detect_markers

    def test_file_finder_set(self, lang):
        assert lang.file_finder is not None

    def test_zone_rules_not_empty(self, lang):
        assert len(lang.zone_rules) > 0

    def test_boundaries(self, lang):
        assert len(lang.boundaries) == 2
        labels = {b.label for b in lang.boundaries}
        assert "common->android" in labels
        assert "common->ios" in labels

    def test_holistic_review_dimensions(self, lang):
        assert "cross_module_architecture" in lang.holistic_review_dimensions
        assert "abstraction_fitness" in lang.holistic_review_dimensions
        assert "dependency_health" in lang.holistic_review_dimensions

    def test_exclusions(self, lang):
        assert "build" in lang.exclusions
        assert ".gradle" in lang.exclusions


class TestSwiftConfig:
    @pytest.fixture()
    def lang(self):
        return get_lang("swift")

    def test_name(self, lang):
        assert lang.name == "swift"

    def test_kmp_markers(self, lang):
        assert "iosApp/" in lang.detect_markers
