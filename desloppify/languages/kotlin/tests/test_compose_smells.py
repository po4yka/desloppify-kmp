"""Tests for Compose smells detector."""

from __future__ import annotations

import pytest

from desloppify.languages.kotlin.detectors.compose_smells import (
    detect_compose_smells,
)


def _make_read_fn(file_contents: dict[str, str]):
    def read_fn(path):
        return file_contents.get(path)
    return read_fn


class TestComposableParamsBloat:
    def test_too_many_params(self):
        files = ["Foo.kt"]
        content = {
            "Foo.kt": (
                "@Composable\n"
                "fun BigScreen(a: Int, b: Int, c: Int, d: Int, e: Int, "
                "f: Int, g: Int, h: Int, i: Int) {\n}\n"
            ),
        }
        findings = detect_compose_smells(files, read_fn=_make_read_fn(content))
        bloat = [f for f in findings if f["detail"]["kind"] == "composable_params_bloat"]
        assert len(bloat) == 1
        assert bloat[0]["tier"] == 3

    def test_acceptable_params(self):
        files = ["Foo.kt"]
        content = {
            "Foo.kt": "@Composable\nfun SmallScreen(a: Int, b: Int) {\n}\n",
        }
        findings = detect_compose_smells(files, read_fn=_make_read_fn(content))
        bloat = [f for f in findings if f["detail"]["kind"] == "composable_params_bloat"]
        assert len(bloat) == 0


class TestStateWithoutRemember:
    def test_mutable_state_outside_remember(self):
        files = ["Foo.kt"]
        content = {
            "Foo.kt": (
                "@Composable\nfun Foo() {\n"
                "    val count = mutableStateOf(0)\n"
                "}\n"
            ),
        }
        findings = detect_compose_smells(files, read_fn=_make_read_fn(content))
        state_issues = [f for f in findings if f["detail"]["kind"] == "state_without_remember"]
        assert len(state_issues) == 1

    def test_mutable_state_inside_remember(self):
        files = ["Foo.kt"]
        content = {
            "Foo.kt": (
                "@Composable\nfun Foo() {\n"
                "    val count = remember { mutableStateOf(0) }\n"
                "}\n"
            ),
        }
        findings = detect_compose_smells(files, read_fn=_make_read_fn(content))
        state_issues = [f for f in findings if f["detail"]["kind"] == "state_without_remember"]
        assert len(state_issues) == 0


class TestViewModelInParams:
    def test_viewmodel_in_composable_params(self):
        files = ["Foo.kt"]
        content = {
            "Foo.kt": (
                "@Composable\n"
                "fun Screen(vm: MainViewModel) {\n}\n"
            ),
        }
        findings = detect_compose_smells(files, read_fn=_make_read_fn(content))
        vm_issues = [f for f in findings if f["detail"]["kind"] == "viewmodel_in_composable_params"]
        assert len(vm_issues) == 1

    def test_no_viewmodel_in_params(self):
        files = ["Foo.kt"]
        content = {
            "Foo.kt": "@Composable\nfun Screen(text: String) {\n}\n",
        }
        findings = detect_compose_smells(files, read_fn=_make_read_fn(content))
        vm_issues = [f for f in findings if f["detail"]["kind"] == "viewmodel_in_composable_params"]
        assert len(vm_issues) == 0


class TestLazyListNoKey:
    def test_items_without_key(self):
        files = ["Foo.kt"]
        content = {
            "Foo.kt": (
                "LazyColumn {\n"
                "    items(list) { item ->\n"
                "        Text(item.name)\n"
                "    }\n"
                "}\n"
            ),
        }
        findings = detect_compose_smells(files, read_fn=_make_read_fn(content))
        lazy_issues = [f for f in findings if f["detail"]["kind"] == "lazy_list_no_key"]
        assert len(lazy_issues) == 1

    def test_items_with_key(self):
        files = ["Foo.kt"]
        content = {
            "Foo.kt": (
                "LazyColumn {\n"
                "    items(list, key = { it.id }) { item ->\n"
                "        Text(item.name)\n"
                "    }\n"
                "}\n"
            ),
        }
        findings = detect_compose_smells(files, read_fn=_make_read_fn(content))
        lazy_issues = [f for f in findings if f["detail"]["kind"] == "lazy_list_no_key"]
        assert len(lazy_issues) == 0
