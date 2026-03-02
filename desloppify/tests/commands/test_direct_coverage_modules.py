"""Direct coverage smoke tests for modules often covered only transitively."""

from __future__ import annotations

import desloppify.app.cli_support.parser as cli_parser
import desloppify.app.cli_support.parser_groups as cli_parser_groups
import desloppify.app.commands.config_cmd as config_cmd
import desloppify.app.commands.move.move_directory as move_directory
import desloppify.app.commands.move.move_reporting as move_reporting
import desloppify.app.commands.move as move_pkg
import desloppify.app.commands.next_parts.output as next_output
import desloppify.app.commands.next_parts.render as next_render
import desloppify.app.commands.plan_cmd as plan_cmd
import desloppify.app.commands.registry as cmd_registry
import desloppify.app.commands.review.batch_core as review_batch_core
import desloppify.app.commands.review.batches as review_batches
import desloppify.app.commands.review.import_cmd as review_import
import desloppify.app.commands.review.import_helpers as review_import_helpers
import desloppify.app.commands.review.prepare as review_prepare
import desloppify.app.commands.review.runner_helpers as review_runner_helpers
import desloppify.app.commands.review.runtime as review_runtime
import desloppify.app.commands.scan as scan_pkg
import desloppify.app.commands.scan.scan_artifacts as scan_artifacts
import desloppify.app.commands.scan.scan_reporting_presentation as scan_reporting_presentation
import desloppify.app.commands.scan.scan_reporting_subjective as scan_reporting_subjective
import desloppify.app.commands.scan.scan_workflow as scan_workflow
import desloppify.app.commands.status_parts.render as status_render
import desloppify.app.commands.status_parts.summary as status_summary
import desloppify.app.output._viz_cmd_context as viz_cmd_context
import desloppify.app.output.scorecard_parts.draw as scorecard_draw
import desloppify.app.output.scorecard_parts.left_panel as scorecard_left_panel
import desloppify.app.output.scorecard_parts.ornaments as scorecard_ornaments
import desloppify.app.output.tree_text as tree_text_mod
import desloppify.core.runtime_state as runtime_state
import desloppify.engine._state.noise as noise
import desloppify.engine._state.persistence as persistence
import desloppify.engine._state.resolution as state_resolution
import desloppify.engine.planning.common as plan_common
import desloppify.engine.planning.scan as plan_scan
import desloppify.engine.planning.select as plan_select
import desloppify.intelligence.integrity as subjective_review_integrity
import desloppify.intelligence.review._context.structure as review_context_structure
import desloppify.intelligence.review.dimensions.holistic as review_dimensions_holistic
import desloppify.intelligence.review.dimensions.validation as review_dimensions_validation
import desloppify.languages as lang_pkg
import desloppify.languages._framework.discovery as lang_discovery
from desloppify.intelligence.review import prepare_batches as review_prepare_batches
from desloppify.languages import resolution as lang_resolution


def _assert_all_callables(*targets) -> None:
    for target in targets:
        assert callable(target)


def test_smoke_parser():
    """Parser and CLI support modules."""
    _assert_all_callables(
        cli_parser.create_parser,
        cli_parser_groups._add_scan_parser,
    )


def test_smoke_planning():
    """Planning modules: common, scan, select."""
    _assert_all_callables(
        plan_common.is_subjective_phase,
        plan_scan.generate_findings,
        plan_select.get_next_items,
        plan_select.get_next_item,
    )
    assert isinstance(plan_common.TIER_LABELS, dict)
    assert 1 in plan_common.TIER_LABELS


def test_smoke_commands():
    """App command modules: config, plan, move, scan, next, review, status."""
    _assert_all_callables(
        config_cmd.cmd_config,
        plan_cmd.cmd_plan_output,
        move_directory.run_directory_move,
        move_reporting.print_file_move_plan,
        move_reporting.print_directory_move_plan,
        move_pkg.cmd_move,
        scan_pkg.cmd_scan,
        scan_artifacts.build_scan_query_payload,
        scan_artifacts.emit_scorecard_badge,
        scan_workflow.prepare_scan_runtime,
        scan_workflow.run_scan_generation,
        scan_workflow.merge_scan_results,
        next_output.serialize_item,
        next_output.build_query_payload,
        next_render.render_queue_header,
        review_batch_core.merge_batch_results,
        review_batches.do_run_batches,
        review_import.do_import,
        review_import_helpers.load_import_findings_data,
        review_prepare.do_prepare,
        review_runner_helpers.run_codex_batch,
        review_runtime.setup_lang,
        status_render.show_tier_progress_table,
        status_summary.score_summary_lines,
        scan_reporting_presentation.show_score_model_breakdown,
        scan_reporting_presentation.show_detector_progress,
        scan_reporting_subjective.subjective_rerun_command,
        scan_reporting_subjective.subjective_integrity_followup,
        scan_reporting_subjective.build_subjective_followup,
    )
    assert isinstance(cmd_registry.get_command_handlers(), dict)
    assert "scan" in cmd_registry.get_command_handlers()
    runtime = runtime_state.current_runtime_context()
    assert isinstance(runtime.exclusions, tuple)
    assert isinstance(runtime.source_file_cache.max_entries, int)
    runtime.cache_enabled = True
    assert runtime.cache_enabled
    runtime.cache_enabled = False


def test_smoke_engine():
    """Engine modules: state internals."""
    _assert_all_callables(
        persistence.load_state,
        persistence.save_state,
        state_resolution.match_findings,
        state_resolution.resolve_findings,
        noise.resolve_finding_noise_budget,
        noise.resolve_finding_noise_global_budget,
        noise.resolve_finding_noise_settings,
    )


def test_smoke_lang_plugins():
    """Language plugin modules: package, discovery, resolution."""
    _assert_all_callables(
        lang_pkg.register_lang,
        lang_pkg.available_langs,
        lang_discovery.load_all,
        lang_discovery.raise_load_errors,
        lang_resolution.make_lang_config,
        lang_resolution.get_lang,
        lang_resolution.auto_detect_lang,
    )


def test_smoke_intelligence():
    """Intelligence modules: review dimensions, context, prepare, integrity."""
    assert isinstance(review_dimensions_holistic.DIMENSIONS, list)
    assert "cross_module_architecture" in review_dimensions_holistic.DIMENSIONS
    _assert_all_callables(
        review_prepare_batches.build_investigation_batches,
        review_context_structure.compute_structure_context,
        review_dimensions_validation.parse_dimensions_payload,
        subjective_review_integrity.subjective_review_open_breakdown,
        scorecard_draw.draw_left_panel,
        scorecard_draw.draw_right_panel,
        scorecard_draw.draw_ornament,
        scorecard_left_panel.draw_left_panel,
        scorecard_ornaments.draw_ornament,
        viz_cmd_context.load_cmd_context,
        tree_text_mod._aggregate,
    )


# ---------------------------------------------------------------------------
# Behavioral tests for key functions (beyond assert callable)
# ---------------------------------------------------------------------------


def test_noise_budget_defaults():
    """resolve_finding_noise_budget returns default for None config."""
    assert noise.resolve_finding_noise_budget(None) == 10
    assert noise.resolve_finding_noise_budget({}) == 10


def test_noise_budget_from_config():
    """resolve_finding_noise_budget reads the config value."""
    assert noise.resolve_finding_noise_budget({"finding_noise_budget": 5}) == 5
    assert noise.resolve_finding_noise_budget({"finding_noise_budget": 0}) == 0


def test_noise_settings_invalid_config():
    """resolve_finding_noise_settings returns warning for invalid values."""
    per, glob, warning = noise.resolve_finding_noise_settings(
        {"finding_noise_budget": "bad"}
    )
    assert per == 10  # default
    assert warning is not None
    assert "Invalid" in warning


def test_serialize_item_minimal():
    """serialize_item extracts expected fields from a minimal item dict."""
    item = {
        "id": "smells::foo.py::1",
        "kind": "finding",
        "tier": 2,
        "confidence": "high",
        "detector": "smells",
        "file": "foo.py",
        "summary": "Unused import",
        "status": "open",
    }
    result = next_output.serialize_item(item)
    assert result["id"] == "smells::foo.py::1"
    assert result["kind"] == "finding"
    assert result["tier"] == 2
    assert result["detector"] == "smells"
    assert result["file"] == "foo.py"
    assert "explain" not in result


def test_build_query_payload_structure():
    """build_query_payload returns well-formed dict with queue metadata."""
    items = [{"id": "f1", "kind": "finding", "tier": 1}]
    queue = {"tier_counts": {1: 1}, "total": 1}
    payload = next_output.build_query_payload(
        queue, items, command="next", narrative=None
    )
    assert payload["command"] == "next"
    assert len(payload["items"]) == 1
    assert payload["queue"]["total"] == 1
    assert payload["narrative"] is None


def test_command_registry_has_core_commands():
    """get_command_handlers includes scan, status, next, plan."""
    handlers = cmd_registry.get_command_handlers()
    for cmd in ("scan", "status", "next", "plan"):
        assert cmd in handlers, f"Missing command handler: {cmd}"
        assert callable(handlers[cmd])
