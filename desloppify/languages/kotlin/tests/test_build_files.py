"""Tests for build file analyzer."""

from __future__ import annotations

import pytest

from desloppify.languages.kotlin.detectors.build_files import (
    _check_buildsrc,
    _check_gradle,
    _check_settings,
    _check_version_catalog,
    _extract_toml_section,
    _parse_major_minor,
)


def _has_kind(findings, kind):
    return any(f["detail"]["kind"] == kind for f in findings)


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


class TestDeprecatedAgpKmp:
    def test_detects_deprecated_android_library_with_kmp(self):
        content = """
plugins {
    id("com.android.library")
    kotlin("multiplatform")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "deprecated_agp_kmp")

    def test_no_flag_without_kmp(self):
        content = """
plugins {
    id("com.android.library")
    kotlin("jvm")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "deprecated_agp_kmp")

    def test_no_flag_without_android_library(self):
        content = """
plugins {
    kotlin("multiplatform")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "deprecated_agp_kmp")


class TestAllprojectsAntipattern:
    def test_detects_allprojects_block(self):
        content = """
allprojects {
    repositories { mavenCentral() }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "allprojects_antipattern")

    def test_detects_subprojects_block(self):
        content = """
subprojects {
    apply(plugin = "kotlin")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "allprojects_antipattern")

    def test_no_flag_without_block(self):
        content = """
plugins {
    kotlin("multiplatform")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "allprojects_antipattern")

    def test_detects_in_settings(self):
        content = """
allprojects {
    repositories { mavenCentral() }
}
"""
        findings = _check_settings("settings.gradle.kts", content)
        assert _has_kind(findings, "allprojects_antipattern")


class TestRedundantJavaPlugin:
    def test_detects_java_with_kotlin_jvm(self):
        content = """
plugins {
    kotlin("jvm")
    id("java")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "redundant_java_plugin")

    def test_detects_java_with_kotlin_multiplatform(self):
        content = """
plugins {
    kotlin("multiplatform")
    id("java")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "redundant_java_plugin")

    def test_no_flag_java_only(self):
        content = """
plugins {
    id("java")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "redundant_java_plugin")

    def test_no_flag_kotlin_only(self):
        content = """
plugins {
    kotlin("jvm")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "redundant_java_plugin")


class TestDeprecatedWithJava:
    def test_detects_withjava_in_kmp(self):
        content = """
kotlin {
    multiplatform
    jvm {
        withJava()
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "deprecated_withjava")

    def test_no_flag_without_kmp(self):
        content = """
kotlin {
    jvm {
        withJava()
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "deprecated_withjava")


class TestKaptDeprecated:
    def test_detects_kapt_plugin_short(self):
        content = """
plugins {
    kotlin("kapt")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "kapt_deprecated")

    def test_detects_kapt_plugin_full(self):
        content = """
plugins {
    id("org.jetbrains.kotlin.kapt")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "kapt_deprecated")

    def test_no_flag_without_kapt(self):
        content = """
plugins {
    kotlin("jvm")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "kapt_deprecated")


class TestHardcodedDepVersion:
    def test_detects_hardcoded_version(self):
        content = """
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
}
"""
        findings = _check_gradle("build.gradle.kts", content, has_version_catalog=True)
        assert _has_kind(findings, "hardcoded_dep_version")

    def test_no_flag_with_catalog_ref(self):
        content = """
dependencies {
    implementation(libs.kotlinx.coroutines)
}
"""
        findings = _check_gradle("build.gradle.kts", content, has_version_catalog=True)
        assert not _has_kind(findings, "hardcoded_dep_version")

    def test_no_flag_without_catalog(self):
        content = """
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
}
"""
        findings = _check_gradle("build.gradle.kts", content, has_version_catalog=False)
        assert not _has_kind(findings, "hardcoded_dep_version")


class TestDuplicateCatalogEntry:
    def test_detects_duplicate_module(self):
        content = """
[versions]
kotlin = "2.0.0"

[libraries]
coroutines-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }
coroutines = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version = "1.7.3" }
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert _has_kind(findings, "duplicate_catalog_entry")

    def test_no_flag_unique_modules(self):
        content = """
[versions]
kotlin = "2.0.0"

[libraries]
coroutines-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }
coroutines-test = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-test", version.ref = "coroutines" }
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert not _has_kind(findings, "duplicate_catalog_entry")


class TestAgpMigrationNeeded:
    def test_detects_agp_below_9(self):
        content = """
[versions]
agp = "8.5.0"
kotlin = "2.0.0"
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert _has_kind(findings, "agp_migration_needed")

    def test_no_flag_agp_9(self):
        content = """
[versions]
agp = "9.0.0"
kotlin = "2.0.0"
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert not _has_kind(findings, "agp_migration_needed")

    def test_no_flag_no_agp(self):
        content = """
[versions]
kotlin = "2.0.0"
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert not _has_kind(findings, "agp_migration_needed")

    def test_detects_android_gradle_plugin_key(self):
        content = """
[versions]
android-gradle-plugin = "8.2.0"
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert _has_kind(findings, "agp_migration_needed")


class TestBuildSrcAntipattern:
    def test_detects_buildsrc_dir(self, tmp_path):
        (tmp_path / "buildSrc").mkdir()
        findings = _check_buildsrc(tmp_path)
        assert _has_kind(findings, "buildsrc_antipattern")

    def test_no_flag_without_buildsrc(self, tmp_path):
        findings = _check_buildsrc(tmp_path)
        assert not _has_kind(findings, "buildsrc_antipattern")


class TestExtractTomlSection:
    def test_extracts_libraries(self):
        content = """
[versions]
kotlin = "2.0.0"

[libraries]
coroutines = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core" }

[plugins]
kotlin-jvm = { id = "org.jetbrains.kotlin.jvm" }
"""
        section = _extract_toml_section(content, "libraries")
        assert section is not None
        assert "coroutines" in section
        assert "kotlin-jvm" not in section

    def test_returns_none_for_missing_section(self):
        content = """
[versions]
kotlin = "2.0.0"
"""
        assert _extract_toml_section(content, "libraries") is None


class TestCheckVersionCatalog:
    def test_old_kotlin_version(self):
        content = """
[versions]
kotlin = "1.8.0"
compose-multiplatform = "1.5.0"
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert len([f for f in findings if f["detail"]["kind"] == "version_mismatch"]) == 1
        assert "1.8.0" in findings[0]["summary"]

    def test_compatible_versions(self):
        content = """
[versions]
kotlin = "2.0.0"
compose-multiplatform = "1.6.0"
"""
        findings = _check_version_catalog("gradle/libs.versions.toml", content)
        assert not _has_kind(findings, "version_mismatch")


class TestJcenterDeprecated:
    def test_detects_jcenter_in_gradle(self):
        content = """
repositories {
    jcenter()
    mavenCentral()
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "jcenter_deprecated")

    def test_no_flag_without_jcenter(self):
        content = """
repositories {
    mavenCentral()
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "jcenter_deprecated")

    def test_detects_jcenter_in_settings(self):
        content = """
dependencyResolutionManagement {
    repositories {
        jcenter()
    }
}
"""
        findings = _check_settings("settings.gradle.kts", content)
        assert _has_kind(findings, "jcenter_deprecated")


class TestLowTargetSdk:
    def test_detects_target_sdk_below_34(self):
        content = """
android {
    defaultConfig {
        targetSdk = 33
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "low_target_sdk")

    def test_no_flag_target_sdk_34(self):
        content = """
android {
    defaultConfig {
        targetSdk = 34
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "low_target_sdk")


class TestMinifyNoProguard:
    def test_detects_minify_without_proguard(self):
        content = """
buildTypes {
    release {
        isMinifyEnabled = true
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "minify_no_proguard")

    def test_no_flag_with_proguard(self):
        content = """
buildTypes {
    release {
        isMinifyEnabled = true
        proguardFiles(getDefaultProguardFile("proguard-android.txt"), "proguard-rules.pro")
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "minify_no_proguard")


class TestMissingComposeFeature:
    def test_detects_compose_dep_without_feature(self):
        content = """
dependencies {
    implementation("androidx.compose.ui:ui:1.5.0")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "missing_compose_feature")

    def test_no_flag_with_compose_feature(self):
        content = """
android {
    buildFeatures {
        compose = true
    }
}
dependencies {
    implementation("androidx.compose.ui:ui:1.5.0")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "missing_compose_feature")

    def test_no_flag_kmp_project(self):
        content = """
kotlin("multiplatform")
dependencies {
    implementation("androidx.compose.ui:ui:1.5.0")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "missing_compose_feature")


class TestDebugSigningRelease:
    def test_detects_debug_signing_in_release(self):
        content = """
buildTypes {
    release {
        signingConfig = signingConfigs.debug
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "debug_signing_release")

    def test_no_flag_release_signing(self):
        content = """
buildTypes {
    release {
        signingConfig = signingConfigs.release
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "debug_signing_release")


class TestHardcodedSigning:
    def test_detects_hardcoded_store_password(self):
        content = """
signingConfigs {
    create("release") {
        storePassword = "mysecretpassword"
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "hardcoded_signing")

    def test_no_flag_env_variable(self):
        content = """
signingConfigs {
    create("release") {
        storePassword = System.getenv("STORE_PASSWORD")
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "hardcoded_signing")


class TestMinifyNoShrink:
    def test_detects_minify_without_shrink(self):
        content = """
buildTypes {
    release {
        isMinifyEnabled = true
        proguardFiles(getDefaultProguardFile("proguard-android.txt"))
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "minify_no_shrink")

    def test_no_flag_with_shrink(self):
        content = """
buildTypes {
    release {
        isMinifyEnabled = true
        isShrinkResources = true
        proguardFiles(getDefaultProguardFile("proguard-android.txt"))
    }
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "minify_no_shrink")


class TestKotlinAndroidExtensions:
    def test_detects_kotlin_android_extensions(self):
        content = """
plugins {
    id("kotlin-android-extensions")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert _has_kind(findings, "kotlin_android_extensions")

    def test_no_flag_without_extensions(self):
        content = """
plugins {
    kotlin("jvm")
}
"""
        findings = _check_gradle("build.gradle.kts", content)
        assert not _has_kind(findings, "kotlin_android_extensions")


class TestParseMajorMinor:
    def test_normal_version(self):
        assert _parse_major_minor("1.9.20") == (1, 9)

    def test_two_part(self):
        assert _parse_major_minor("2.0") == (2, 0)

    def test_invalid(self):
        assert _parse_major_minor("latest") is None
