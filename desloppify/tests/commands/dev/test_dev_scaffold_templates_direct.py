"""Direct tests for dev scaffold template builders."""

from __future__ import annotations

import desloppify.app.commands.dev_scaffold_templates as templates_mod


def test_build_scaffold_files_contains_expected_paths():
    files = templates_mod.build_scaffold_files(
        lang_name="swift_support",
        class_name="SwiftSupportConfig",
        extensions=[".swift"],
        markers=["Package.swift"],
        default_src="iosApp",
    )

    assert files["detectors/__init__.py"] == ""
    assert files["fixers/__init__.py"] == ""
    assert "review_data/per_file_dimensions.override.json" not in files
    assert files["review_data/holistic_dimensions.override.json"] == "{}\n"
    assert "build_dep_graph" in files["detectors/deps.py"]
    assert "register_lang_hooks" in files["__init__.py"]
    assert 'integration_depth="minimal"' in files["__init__.py"]
    assert 'exclusions=["build", ".gradle", "Pods", "DerivedData", ".build"]' in files["__init__.py"]
    assert "def is_runtime_entrypoint" in files["test_coverage.py"]


def test_init_template_registers_language_and_defaults():
    files = templates_mod.build_scaffold_files(
        lang_name="swift",
        class_name="SwiftConfig",
        extensions=[".swift"],
        markers=["Package.swift"],
        default_src="iosApp",
    )

    init_py = files["__init__.py"]
    assert '@register_lang("swift")' in init_py
    assert "class SwiftConfig(LangConfig):" in init_py
    assert "default_src='iosApp'" in init_py
    assert "detect_markers=['Package.swift']" in init_py
    assert "from desloppify.languages._framework.base.types import DetectorPhase, LangConfig" in init_py
    assert "from desloppify.languages._framework.base.phase_builders import (" in init_py
    assert "from desloppify.core.source_discovery import find_source_files" in init_py

    phases_py = files["phases.py"]
    assert "def phase_placeholder" in phases_py
