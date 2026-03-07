"""KMP test coverage hooks for mapping Kotlin sources to tests."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from desloppify.languages.kotlin.detectors.kmp_utils import get_source_set

ASSERT_PATTERNS = [
    re.compile(r"\bassertEquals\b"),
    re.compile(r"\bassertTrue\b"),
    re.compile(r"\bassertFalse\b"),
    re.compile(r"\bassertNotNull\b"),
    re.compile(r"\bassertNull\b"),
    re.compile(r"\bshould\b"),
    re.compile(r"\bexpectThat\b"),
]

MOCK_PATTERNS = [
    re.compile(r"\bmockk\b"),
    re.compile(r"\bevery\s*\{"),
    re.compile(r"\bcoEvery\s*\{"),
    re.compile(r"\bverify\s*\{"),
]

SNAPSHOT_PATTERNS = [
    re.compile(r"\btoMatchSnapshot\b"),
]

TEST_FUNCTION_RE = re.compile(
    r"^\s*(?:@Test\s+)?fun\s+`?(\w[^`(]*)(?:`|\()",
    re.MULTILINE,
)

BARREL_BASENAMES: set[str] = set()

_TEST_SET_MAP: dict[str, str] = {
    "commonMain": "commonTest",
    "androidMain": "androidTest",
    "iosMain": "iosTest",
    "jvmMain": "jvmTest",
    "desktopMain": "desktopTest",
    "nativeMain": "nativeTest",
}

_MEANINGFUL_DECL_RE = re.compile(
    r"\b(fun|class|object|interface|data\s+class|sealed\s+class|enum\s+class)\b"
)
_PLACEHOLDER_ASSERT_RE = re.compile(
    r"\bassert(?:True|Equals)\s*\(\s*(?:true|1\s*,\s*1)\s*\)"
)


def has_testable_logic(_filepath: str, content: str) -> bool:
    """Return True when a Kotlin file contains non-trivial runtime declarations."""
    stripped = strip_comments(content)
    lines = [line for line in stripped.splitlines() if line.strip()]
    if len(lines) < 3:
        return False
    return bool(_MEANINGFUL_DECL_RE.search(stripped))


def is_runtime_entrypoint(filepath: str, content: str) -> bool:
    """Best-effort entrypoint detection for Android/KMP host files."""
    lowered_path = filepath.replace("\\", "/").lower()
    stripped = strip_comments(content).lower()

    if lowered_path.endswith("/main.kt") and "fun main(" in stripped:
        return True
    if lowered_path.endswith("/mainactivity.kt") and (
        "componentactivity" in stripped or "setcontent" in stripped
    ):
        return True
    if "/androidmain/" in lowered_path and (
        "componentactivity" in stripped or ": application" in stripped
    ):
        return True
    return False


def resolve_import_spec(
    import_line: str,
    _test_path: str,
    production_files: set[str],
) -> str | None:
    """Resolve a Kotlin import to the likeliest production file."""
    match = re.match(r"^\s*import\s+([\w.]+)", import_line)
    if not match:
        return None

    spec = match.group(1)
    normalized_files = {
        filepath.replace("\\", "/"): filepath for filepath in production_files
    }
    direct_suffix = f"/{spec.replace('.', '/')}.kt"
    for normalized, original in normalized_files.items():
        if normalized.endswith(direct_suffix):
            return original

    stem = f"{spec.rsplit('.', 1)[-1]}.kt"
    matches = [
        original
        for normalized, original in normalized_files.items()
        if PurePosixPath(normalized).name == stem
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def resolve_barrel_reexports(
    _filepath: str,
    _production_files: set[str],
) -> set[str]:
    """Kotlin does not use barrel re-export files."""
    return set()


def parse_test_import_specs(content: str) -> list[str]:
    """Extract import specs from a Kotlin test file."""
    specs: list[str] = []
    for line in content.splitlines():
        match = re.match(r"^\s*import\s+([\w.]+)", line)
        if match:
            specs.append(match.group(1))
    return specs


def strip_test_markers(basename: str) -> str | None:
    """Convert Kotlin test basenames back to production basenames."""
    if basename.endswith("Test.kt"):
        return f"{basename[:-7]}.kt"
    if basename.endswith("Spec.kt"):
        return f"{basename[:-7]}.kt"
    if basename.endswith("Test.kts"):
        return f"{basename[:-8]}.kts"
    return None


def strip_comments(content: str) -> str:
    """Strip Kotlin line and block comments."""
    content = re.sub(r"//[^\n]*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return content


def is_placeholder_test(
    content: str,
    *,
    assertions: int,
    test_functions: int,
) -> bool:
    """Detect tautological smoke tests that inflate coverage confidence."""
    if assertions == 0 or test_functions == 0:
        return False
    return bool(_PLACEHOLDER_ASSERT_RE.search(strip_comments(content)))


def map_test_to_source(test_file: str, all_files: set[str]) -> str | None:
    """Map a test file back to its source file via KMP source set conventions."""
    source_set = get_source_set(test_file)
    if not source_set:
        return None

    reverse_map = {test_set: source for source, test_set in _TEST_SET_MAP.items()}
    source_main = reverse_map.get(source_set)
    if not source_main:
        return None

    basename = PurePosixPath(test_file).name
    source_basename = strip_test_markers(basename)
    if not source_basename:
        return None

    expected = test_file.replace(f"/{source_set}/", f"/{source_main}/")
    expected = re.sub(r"/[^/]+$", f"/{source_basename}", expected)
    if expected in all_files:
        return expected

    for filepath in all_files:
        if filepath.endswith(f"/{source_basename}") and f"/{source_main}/" in filepath:
            return filepath
    return None


def find_test_file(source_file: str, all_files: list[str]) -> str | None:
    """Find the test file corresponding to a KMP production source file."""
    source_set = get_source_set(source_file)
    if not source_set or source_set not in _TEST_SET_MAP:
        return None

    test_set = _TEST_SET_MAP[source_set]
    basename = PurePosixPath(source_file).stem
    test_name = f"{basename}Test.kt"

    expected = source_file.replace(f"/{source_set}/", f"/{test_set}/")
    expected = re.sub(r"/[^/]+\.kt$", f"/{test_name}", expected)
    if expected in all_files:
        return expected

    for filepath in all_files:
        if filepath.endswith(test_name) and f"/{test_set}/" in filepath:
            return filepath
    return None


def map_source_to_tests(
    source_files: list[str],
    all_files: list[str],
) -> dict[str, list[str]]:
    """Map each Kotlin production file to the corresponding test file(s)."""
    result: dict[str, list[str]] = {}
    for source in source_files:
        test = find_test_file(source, all_files)
        if test:
            result[source] = [test]
    return result
