"""Swift/iOS test coverage hooks."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

ASSERT_PATTERNS = [
    re.compile(r"\bXCTAssert(?:Equal|True|False|NotNil|Nil|ThrowsError)\b"),
]

MOCK_PATTERNS = [
    re.compile(r"\bMock[A-Z]\w*\b"),
    re.compile(r"\bstub\b", re.IGNORECASE),
]

SNAPSHOT_PATTERNS = [
    re.compile(r"\bassertSnapshot\b"),
]

TEST_FUNCTION_RE = re.compile(r"^\s*func\s+(test\w+)\s*\(", re.MULTILINE)
BARREL_BASENAMES: set[str] = set()

_DECLARATION_RE = re.compile(
    r"\b(func|class|struct|enum|protocol|actor|extension)\b"
)
_PLACEHOLDER_ASSERT_RE = re.compile(
    r"\bXCTAssert(?:True|Equal)\s*\(\s*(?:true|1\s*,\s*1)\s*\)"
)


def has_testable_logic(_filepath: str, content: str) -> bool:
    """Return True when a Swift file contains real declarations to exercise."""
    stripped = strip_comments(content)
    lines = [line for line in stripped.splitlines() if line.strip()]
    if len(lines) < 3:
        return False
    return bool(_DECLARATION_RE.search(stripped))


def is_runtime_entrypoint(filepath: str, content: str) -> bool:
    """Best-effort entrypoint detection for SwiftUI/UIKit app bootstrap files."""
    lowered_path = filepath.replace("\\", "/").lower()
    stripped = strip_comments(content).lower()
    filename = PurePosixPath(lowered_path).name
    if filename in {"appdelegate.swift", "scenedelegate.swift"}:
        return True
    if "@main" in stripped and ("struct" in stripped or "class" in stripped):
        return True
    if "uiapplicationmain" in stripped:
        return True
    return False


def resolve_import_spec(
    spec: str,
    _test_path: str,
    production_files: set[str],
) -> str | None:
    """Resolve a Swift import spec to the likeliest production file."""
    module_name = spec.strip().split(".")[-1]
    if not module_name:
        return None
    expected_stem = module_name.lower()
    for filepath in production_files:
        stem = PurePosixPath(filepath.replace("\\", "/")).stem.lower()
        if stem == expected_stem:
            return filepath
    return None


def resolve_barrel_reexports(
    _filepath: str,
    _production_files: set[str],
) -> set[str]:
    """Swift does not use barrel re-export files."""
    return set()


def parse_test_import_specs(content: str) -> list[str]:
    """Extract import lines from a Swift test file."""
    specs: list[str] = []
    for line in content.splitlines():
        match = re.match(r"^\s*import\s+([A-Za-z_][\w.]*)", line)
        if match:
            specs.append(match.group(1))
    return specs


def map_test_to_source(test_path: str, production_set: set[str]) -> str | None:
    """Map `FooTests.swift` or `FooTest.swift` to `Foo.swift`."""
    basename = PurePosixPath(test_path).name
    source_basename = strip_test_markers(basename)
    if not source_basename:
        return None

    expected_dir = PurePosixPath(test_path.replace("\\", "/")).parent
    for filepath in production_set:
        normalized = PurePosixPath(filepath.replace("\\", "/"))
        if normalized.name == source_basename and (
            normalized.parent == expected_dir or normalized.parent.name != "Tests"
        ):
            return filepath
    return None


def strip_test_markers(basename: str) -> str | None:
    """Convert Swift test basenames back to production basenames."""
    if basename.endswith("Tests.swift"):
        return f"{basename[:-11]}.swift"
    if basename.endswith("Test.swift"):
        return f"{basename[:-10]}.swift"
    if basename.endswith("Spec.swift"):
        return f"{basename[:-10]}.swift"
    return None


def strip_comments(content: str) -> str:
    """Strip Swift line and block comments."""
    content = re.sub(r"//[^\n]*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return content


def is_placeholder_test(
    content: str,
    *,
    assertions: int,
    test_functions: int,
) -> bool:
    """Detect tautological XCTest smoke tests."""
    if assertions == 0 or test_functions == 0:
        return False
    return bool(_PLACEHOLDER_ASSERT_RE.search(strip_comments(content)))
