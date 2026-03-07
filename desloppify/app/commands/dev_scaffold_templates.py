"""Template builders for `desloppify dev scaffold-lang`."""

from __future__ import annotations


def _empty_review_override() -> str:
    """Return an empty JSON override file body."""
    return "{}\n"


def _init_template(
    lang_name: str,
    class_name: str,
    ext_repr: str,
    marker_repr: str,
    default_src: str,
) -> str:
    upper_name = lang_name.upper()
    return (
        f'''"""Analyzer configuration for {lang_name}."""\n\n'''
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n\n"
        "from desloppify.core.source_discovery import find_source_files\n"
        "from desloppify.engine.policy.zones import COMMON_ZONE_RULES, Zone, ZoneRule\n"
        "from desloppify.hook_registry import register_lang_hooks\n"
        "from desloppify.languages import register_lang\n"
        "from desloppify.languages._framework.base.phase_builders import (\n"
        "    detector_phase_security,\n"
        "    detector_phase_test_coverage,\n"
        "    shared_subjective_duplicates_tail,\n"
        ")\n"
        "from desloppify.languages._framework.base.types import DetectorPhase, LangConfig\n"
        f"from desloppify.languages.{lang_name}.commands import get_detect_commands\n"
        f"from desloppify.languages.{lang_name}.extractors import extract_functions\n"
        f"from desloppify.languages.{lang_name}.phases import phase_placeholder\n"
        f"from desloppify.languages.{lang_name}.review import (\n"
        "    HOLISTIC_REVIEW_DIMENSIONS,\n"
        "    LOW_VALUE_PATTERN,\n"
        "    MIGRATION_MIXED_EXTENSIONS,\n"
        "    MIGRATION_PATTERN_PAIRS,\n"
        "    REVIEW_GUIDANCE,\n"
        "    api_surface,\n"
        "    module_patterns,\n"
        ")\n\n\n"
        f"{upper_name}_ZONE_RULES = [\n"
        '    ZoneRule(Zone.GENERATED, ["/build/", "/.gradle/", "/Pods/", "/DerivedData/", "/.build/"]),\n'
        "    *COMMON_ZONE_RULES,\n"
        "]\n\n\n"
        "def _find_files(path: Path) -> list[str]:\n"
        f"    return find_source_files(path, {ext_repr})\n\n\n"
        "def _build_dep_graph(path: Path) -> dict:\n"
        f"    from desloppify.languages.{lang_name}.detectors.deps import build_dep_graph\n\n"
        "    return build_dep_graph(path)\n\n\n"
        f'@register_lang("{lang_name}")\n'
        f"class {class_name}(LangConfig):\n"
        "    def __init__(self):\n"
        "        super().__init__(\n"
        f"            name={lang_name!r},\n"
        f"            extensions={ext_repr},\n"
        '            exclusions=["build", ".gradle", "Pods", "DerivedData", ".build"],\n'
        f"            default_src={default_src!r},\n"
        "            build_dep_graph=_build_dep_graph,\n"
        "            entry_patterns=[],\n"
        "            barrel_names=set(),\n"
        "            phases=[\n"
        '                DetectorPhase("Placeholder", phase_placeholder),\n'
        "                detector_phase_test_coverage(),\n"
        "                detector_phase_security(),\n"
        "                *shared_subjective_duplicates_tail(),\n"
        "            ],\n"
        "            fixers={},\n"
        '            get_area=lambda filepath: filepath.split("/")[0],\n'
        "            detect_commands=get_detect_commands(),\n"
        "            boundaries=[],\n"
        '            typecheck_cmd="",\n'
        "            file_finder=_find_files,\n"
        f"            detect_markers={marker_repr},\n"
        '            external_test_dirs=["commonTest", "androidTest", "iosTest", "Tests", "UITests"],\n'
        f"            test_file_extensions={ext_repr},\n"
        "            review_module_patterns_fn=module_patterns,\n"
        "            review_api_surface_fn=api_surface,\n"
        "            review_guidance=REVIEW_GUIDANCE,\n"
        "            review_low_value_pattern=LOW_VALUE_PATTERN,\n"
        "            holistic_review_dimensions=HOLISTIC_REVIEW_DIMENSIONS,\n"
        "            migration_pattern_pairs=MIGRATION_PATTERN_PAIRS,\n"
        "            migration_mixed_extensions=MIGRATION_MIXED_EXTENSIONS,\n"
        "            extract_functions=extract_functions,\n"
        f"            zone_rules={upper_name}_ZONE_RULES,\n"
        '            integration_depth="minimal",\n'
        "        )\n\n\n"
        f"from desloppify.languages.{lang_name} import test_coverage as _test_coverage  # noqa: E402\n\n"
        f'register_lang_hooks("{lang_name}", test_coverage=_test_coverage)\n'
    )


def _phases_template() -> str:
    return (
        '"""Phase runners for analyzer scaffolding."""\n\n'
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n"
        "from typing import Any\n\n\n"
        "def phase_placeholder(_path: Path, _lang: Any) -> tuple[list[dict], dict[str, int]]:\n"
        '    """Placeholder phase. Replace with real detector orchestration."""\n'
        "    return [], {}\n"
    )


def _commands_template(lang_name: str) -> str:
    return (
        '"""Detect command registry for analyzer scaffolding."""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import TYPE_CHECKING, Callable\n\n"
        "from desloppify.core.output_api import colorize\n\n"
        "if TYPE_CHECKING:\n"
        "    import argparse\n\n\n"
        "def cmd_placeholder(_args: argparse.Namespace) -> None:\n"
        f'    print(colorize("{lang_name}: placeholder detector command (not implemented)", "yellow"))\n\n\n'
        "def get_detect_commands() -> dict[str, Callable[..., None]]:\n"
        '    return {"placeholder": cmd_placeholder}\n'
    )


def _extractors_template() -> str:
    return (
        '"""Extractors for analyzer scaffolding."""\n\n'
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n\n\n"
        "def extract_functions(_path: Path) -> list:\n"
        '    """Return function-like items for duplicate/signature detectors."""\n'
        "    return []\n"
    )


def _move_template() -> str:
    return (
        '"""Move helpers for analyzer scaffolding."""\n\n'
        "from __future__ import annotations\n\n"
        "from desloppify.languages._framework.commands_base import (\n"
        "    scaffold_find_replacements,\n"
        "    scaffold_verify_hint,\n"
        ")\n"
        "from desloppify.languages._framework.commands_base import (\n"
        "    scaffold_find_self_replacements,\n"
        ")\n\n"
        "def get_verify_hint() -> str:\n"
        "    return scaffold_verify_hint()\n\n\n"
        "def find_replacements(\n"
        "    source_abs: str, dest_abs: str, graph: dict\n"
        ") -> dict[str, list[tuple[str, str]]]:\n"
        "    return scaffold_find_replacements(source_abs, dest_abs, graph)\n\n\n"
        "def find_self_replacements(\n"
        "    source_abs: str, dest_abs: str, graph: dict\n"
        ") -> list[tuple[str, str]]:\n"
        "    return scaffold_find_self_replacements(source_abs, dest_abs, graph)\n"
    )


def _review_template(lang_name: str) -> str:
    return (
        '"""Review guidance hooks for analyzer scaffolding."""\n\n'
        "from __future__ import annotations\n\n"
        "import re\n\n\n"
        "REVIEW_GUIDANCE = {\n"
        '    "patterns": [],\n'
        '    "auth": [],\n'
        f'    "naming": "{lang_name} naming guidance placeholder",\n'
        "}\n\n"
        'HOLISTIC_REVIEW_DIMENSIONS = ["cross_module_architecture", "test_strategy"]\n\n'
        "MIGRATION_PATTERN_PAIRS: list[tuple[str, object, object]] = []\n"
        "MIGRATION_MIXED_EXTENSIONS: set[str] = set()\n"
        'LOW_VALUE_PATTERN = re.compile(r"$^")\n\n\n'
        "def module_patterns(_content: str) -> list[str]:\n"
        "    return []\n\n\n"
        "def api_surface(_file_contents: dict[str, str]) -> dict:\n"
        "    return {}\n"
    )


def _test_coverage_template() -> str:
    return (
        '"""Test coverage hooks for analyzer scaffolding."""\n\n'
        "from __future__ import annotations\n\n"
        "import re\n\n\n"
        "ASSERT_PATTERNS: list[re.Pattern[str]] = []\n"
        "MOCK_PATTERNS: list[re.Pattern[str]] = []\n"
        "SNAPSHOT_PATTERNS: list[re.Pattern[str]] = []\n"
        'TEST_FUNCTION_RE = re.compile(r"$^")\n'
        "BARREL_BASENAMES: set[str] = set()\n\n\n"
        "def has_testable_logic(_filepath: str, content: str) -> bool:\n"
        "    return bool(content.strip())\n\n\n"
        "def is_runtime_entrypoint(_filepath: str, _content: str) -> bool:\n"
        "    return False\n\n\n"
        "def resolve_import_spec(\n"
        "    _spec: str, _test_path: str, _production_files: set[str]\n"
        ") -> str | None:\n"
        "    return None\n\n\n"
        "def resolve_barrel_reexports(\n"
        "    _filepath: str, _production_files: set[str]\n"
        ") -> set[str]:\n"
        "    return set()\n\n\n"
        "def parse_test_import_specs(_content: str) -> list[str]:\n"
        "    return []\n\n\n"
        "def map_test_to_source(\n"
        "    _test_path: str, _production_set: set[str]\n"
        ") -> str | None:\n"
        "    return None\n\n\n"
        "def strip_test_markers(_basename: str) -> str | None:\n"
        "    return None\n\n\n"
        "def is_placeholder_test(\n"
        "    _content: str, *, assertions: int, test_functions: int\n"
        ") -> bool:\n"
        "    return assertions == 0 and test_functions > 0\n\n\n"
        "def strip_comments(content: str) -> str:\n"
        "    return content\n"
    )


def _deps_template() -> str:
    return (
        '"""Dependency graph builder scaffold."""\n\n'
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n\n\n"
        "def build_dep_graph(_path: Path) -> dict:\n"
        "    return {}\n"
    )


def _test_init_template(lang_name: str, class_name: str, ext_sample: str) -> str:
    return (
        '"""Scaffold sanity tests for the generated analyzer package."""\n\n'
        "from __future__ import annotations\n\n"
        f"from desloppify.languages.{lang_name} import {class_name}\n\n\n"
        "def test_config_name():\n"
        f"    cfg = {class_name}()\n"
        f"    assert cfg.name == {lang_name!r}\n\n\n"
        "def test_config_extensions_non_empty():\n"
        f"    cfg = {class_name}()\n"
        f"    assert {ext_sample!r} in cfg.extensions\n\n\n"
        "def test_detect_commands_non_empty():\n"
        f"    cfg = {class_name}()\n"
        "    assert cfg.detect_commands\n"
    )


def build_scaffold_files(
    *,
    lang_name: str,
    class_name: str,
    extensions: list[str],
    markers: list[str],
    default_src: str,
) -> dict[str, str]:
    """Build the generated file map for a new analyzer scaffold."""
    ext_repr = repr(extensions)
    marker_repr = repr(markers)
    ext_sample = extensions[0]

    return {
        "__init__.py": _init_template(
            lang_name,
            class_name,
            ext_repr,
            marker_repr,
            default_src,
        ),
        "phases.py": _phases_template(),
        "commands.py": _commands_template(lang_name),
        "extractors.py": _extractors_template(),
        "move.py": _move_template(),
        "review.py": _review_template(lang_name),
        "test_coverage.py": _test_coverage_template(),
        "detectors/__init__.py": "",
        "detectors/deps.py": _deps_template(),
        "review_data/holistic_dimensions.override.json": _empty_review_override(),
        "fixers/__init__.py": "",
        "tests/__init__.py": "",
        "tests/test_init.py": _test_init_template(lang_name, class_name, ext_sample),
    }


__all__ = ["build_scaffold_files"]
