"""Direct tests for language resolution helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import desloppify.languages._framework.registry_state as registry_state
import desloppify.languages._framework.resolution as lang_resolution_mod


def test_make_lang_config_wraps_constructor_errors():
    class _BadConfig:
        def __init__(self):
            raise RuntimeError("boom")

    with pytest.raises(
        ValueError, match="Failed to instantiate language config 'bad'"
    ) as exc:
        lang_resolution_mod.make_lang_config("bad", _BadConfig)
    msg = str(exc.value)
    assert "bad" in msg
    assert "boom" in msg


def test_get_lang_uses_registry_and_reports_unknown(monkeypatch):
    sentinel_cls = object()
    monkeypatch.setattr(registry_state, "_registry", {"kotlin": sentinel_cls})
    monkeypatch.setattr(lang_resolution_mod, "load_all", lambda: None)
    monkeypatch.setattr(
        lang_resolution_mod, "make_lang_config", lambda name, cfg_cls: (name, cfg_cls)
    )

    resolved = lang_resolution_mod.get_lang("kotlin")
    assert resolved == ("kotlin", sentinel_cls)
    assert resolved[0] == "kotlin"
    assert resolved[1] is sentinel_cls
    assert registry_state.is_registered("kotlin")

    with pytest.raises(ValueError, match="Unknown language") as exc:
        lang_resolution_mod.get_lang("missing")
    assert "Available: kotlin" in str(exc.value)


def test_auto_detect_lang_prefers_marker_candidates_with_most_sources(
    monkeypatch, tmp_path
):
    (tmp_path / "build.gradle.kts").write_text("plugins {}\n")
    (tmp_path / "Package.swift").write_text("// swift-tools-version: 6.0\n")

    monkeypatch.setattr(
        registry_state,
        "_registry",
        {"kotlin": object(), "swift": object()},
    )
    monkeypatch.setattr(lang_resolution_mod, "load_all", lambda: None)

    cfg_by_name = {
        "kotlin": SimpleNamespace(
            detect_markers=["build.gradle.kts"],
            file_finder=lambda _root: ["App.kt", "SharedApp.kt", "Platform.kt"],
        ),
        "swift": SimpleNamespace(
            detect_markers=["Package.swift"],
            file_finder=lambda _root: ["App.swift"],
        ),
    }
    monkeypatch.setattr(
        lang_resolution_mod,
        "make_lang_config",
        lambda name, _cfg_cls: cfg_by_name[name],
    )

    detected = lang_resolution_mod.auto_detect_lang(tmp_path)
    assert detected == "kotlin"
    assert "kotlin" in cfg_by_name
    assert "swift" in cfg_by_name
    assert (tmp_path / "build.gradle.kts").exists()
    assert (tmp_path / "Package.swift").exists()


def test_auto_detect_lang_markerless_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(
        registry_state,
        "_registry",
        {"kotlin": object(), "swift": object()},
    )
    monkeypatch.setattr(lang_resolution_mod, "load_all", lambda: None)

    cfg_by_name = {
        "kotlin": SimpleNamespace(
            detect_markers=[], file_finder=lambda _root: ["App.kt"]
        ),
        "swift": SimpleNamespace(
            detect_markers=[], file_finder=lambda _root: ["App.swift", "Scene.swift"]
        ),
    }
    monkeypatch.setattr(
        lang_resolution_mod,
        "make_lang_config",
        lambda name, _cfg_cls: cfg_by_name[name],
    )

    detected = lang_resolution_mod.auto_detect_lang(tmp_path)
    assert detected == "swift"
    assert len(cfg_by_name["kotlin"].file_finder(tmp_path)) == 1
    assert len(cfg_by_name["swift"].file_finder(tmp_path)) == 2


def test_auto_detect_lang_supports_glob_markers(monkeypatch, tmp_path):
    (tmp_path / "Desloppify.podspec").write_text("Pod::Spec.new do |s| end\n")
    (tmp_path / "build.gradle.kts").write_text("plugins {}\n")

    monkeypatch.setattr(
        registry_state,
        "_registry",
        {"swift": object(), "kotlin": object()},
    )
    monkeypatch.setattr(lang_resolution_mod, "load_all", lambda: None)

    cfg_by_name = {
        "swift": SimpleNamespace(
            detect_markers=["*.podspec"],
            file_finder=lambda _root: ["App.swift", "SceneDelegate.swift"],
        ),
        "kotlin": SimpleNamespace(
            detect_markers=["build.gradle.kts"],
            file_finder=lambda _root: ["MainActivity.kt"],
        ),
    }
    monkeypatch.setattr(
        lang_resolution_mod,
        "make_lang_config",
        lambda name, _cfg_cls: cfg_by_name[name],
    )

    detected = lang_resolution_mod.auto_detect_lang(tmp_path)
    assert detected == "swift"


def test_available_langs_returns_sorted_list(monkeypatch):
    monkeypatch.setattr(
        registry_state, "_registry", {"swift": object(), "kotlin": object()}
    )
    monkeypatch.setattr(lang_resolution_mod, "load_all", lambda: None)

    langs = lang_resolution_mod.available_langs()
    assert langs == ["kotlin", "swift"]
    assert langs[0] < langs[1]
