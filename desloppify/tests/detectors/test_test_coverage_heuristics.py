"""Focused unit tests for test_coverage.heuristics helpers."""

from __future__ import annotations

from types import SimpleNamespace

from desloppify.engine.detectors.test_coverage import heuristics as heuristics_mod


def test_load_lang_test_coverage_module_falls_back_to_object(monkeypatch):
    monkeypatch.setattr(heuristics_mod, "get_lang_hook", lambda *_args, **_kwargs: None)

    loaded = heuristics_mod._load_lang_test_coverage_module("swift")

    assert loaded.__class__ is object


def test_has_testable_logic_uses_language_hook(tmp_path, monkeypatch):
    source = tmp_path / "module.kt"
    source.write_text("fun run(): Int = 1\n")

    def _hook(_filepath: str, content: str) -> bool:
        return "run" in content

    monkeypatch.setattr(
        heuristics_mod,
        "_load_lang_test_coverage_module",
        lambda _lang: SimpleNamespace(has_testable_logic=_hook),
    )

    assert heuristics_mod._has_testable_logic(str(source), "kotlin") is True


def test_has_testable_logic_supports_legacy_one_arg_hook(tmp_path, monkeypatch):
    source = tmp_path / "module.kt"
    source.write_text("fun run(): Int = 1\n")

    monkeypatch.setattr(
        heuristics_mod,
        "_load_lang_test_coverage_module",
        lambda _lang: SimpleNamespace(has_testable_logic=lambda content: "run" in content),
    )

    assert heuristics_mod._has_testable_logic(str(source), "kotlin") is True


def test_runtime_entrypoint_uses_hook_when_available(tmp_path, monkeypatch):
    source = tmp_path / "App.swift"
    source.write_text("@main\nstruct DemoApp: App {}\n")

    monkeypatch.setattr(
        heuristics_mod,
        "_load_lang_test_coverage_module",
        lambda _lang: SimpleNamespace(
            is_runtime_entrypoint=lambda _filepath, _content: True
        ),
    )

    assert heuristics_mod._is_runtime_entrypoint(str(source), "swift") is True


def test_runtime_entrypoint_uses_kotlin_fallback_for_main_activity(tmp_path, monkeypatch):
    source = tmp_path / "composeApp" / "src" / "androidMain" / "kotlin" / "MainActivity.kt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("class MainActivity : ComponentActivity() { fun render() = setContent {} }\n")

    monkeypatch.setattr(
        heuristics_mod,
        "_load_lang_test_coverage_module",
        lambda _lang: object(),
    )

    assert heuristics_mod._is_runtime_entrypoint(str(source), "kotlin") is True


def test_runtime_entrypoint_uses_swift_fallback_for_app_delegate(tmp_path, monkeypatch):
    source = tmp_path / "iosApp" / "AppDelegate.swift"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("class AppDelegate: UIResponder, UIApplicationDelegate {}\n")

    monkeypatch.setattr(
        heuristics_mod,
        "_load_lang_test_coverage_module",
        lambda _lang: object(),
    )

    assert heuristics_mod._is_runtime_entrypoint(str(source), "swift") is True


def test_runtime_entrypoint_hook_failure_falls_back_without_throwing(
    tmp_path, monkeypatch
):
    source = tmp_path / "src" / "module.swift"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("const value = 1;\n")

    monkeypatch.setattr(
        heuristics_mod,
        "_load_lang_test_coverage_module",
        lambda _lang: SimpleNamespace(
            is_runtime_entrypoint=lambda _filepath, _content: (_ for _ in ()).throw(
                TypeError("bad hook")
            )
        ),
    )

    assert heuristics_mod._is_runtime_entrypoint(str(source), "swift") is False
