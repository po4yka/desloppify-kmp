"""KMP test mapping — map source files to their test counterparts."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from desloppify.languages.kotlin.detectors.kmp_utils import (
    KNOWN_SOURCE_SETS,
    get_source_set,
)

# -- Constants required by standardization contract --

ASSERT_PATTERNS = [
    re.compile(r"\bassertEquals\b"),
    re.compile(r"\bassertTrue\b"),
    re.compile(r"\bassertFalse\b"),
    re.compile(r"\bassertNotNull\b"),
    re.compile(r"\bassertNull\b"),
    re.compile(r"\bshould\b"),  # Kotest
    re.compile(r"\bexpectThat\b"),  # Strikt
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

TEST_FUNCTION_RE = re.compile(r"^\s*(?:@Test\s+)?fun\s+`?(\w[^`(]*)(?:`|\()", re.MULTILINE)

BARREL_BASENAMES: set[str] = set()


def has_testable_logic(content: str) -> bool:
    """Return True if the file contains logic worth testing."""
    lines = [l for l in content.splitlines() if l.strip() and not l.strip().startswith("//")]
    if len(lines) < 3:
        return False
    return bool(re.search(r"\b(fun|class|object|interface)\b", content))


def resolve_import_spec(import_line: str) -> str | None:
    """Extract the module path from a Kotlin import statement."""
    m = re.match(r"^\s*import\s+([\w.]+)", import_line)
    return m.group(1) if m else None


def resolve_barrel_reexports(_filepath: str) -> list[str]:
    """Kotlin does not have barrel re-exports; return empty."""
    return []


def parse_test_import_specs(content: str) -> list[str]:
    """Extract import specs from test file content."""
    specs: list[str] = []
    for line in content.splitlines():
        spec = resolve_import_spec(line)
        if spec:
            specs.append(spec)
    return specs


def strip_test_markers(content: str) -> str:
    """Strip test annotations from content."""
    return re.sub(r"@Test\s*\n?", "", content)


def strip_comments(content: str) -> str:
    """Strip Kotlin comments from content."""
    content = re.sub(r"//[^\n]*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return content


def map_test_to_source(test_file: str, all_files: list[str]) -> str | None:
    """Map a test file back to its source file.

    Reverses the KMP convention: ``src/commonTest/kotlin/FooTest.kt`` ->
    ``src/commonMain/kotlin/Foo.kt``.
    """
    ss = get_source_set(test_file)
    if not ss:
        return None
    # Reverse lookup: find source set from test set
    _REVERSE_MAP = {v: k for k, v in _TEST_SET_MAP.items()}
    src_ss = _REVERSE_MAP.get(ss)
    if not src_ss:
        return None
    base_name = PurePosixPath(test_file).stem
    if base_name.endswith("Test"):
        base_name = base_name[:-4]
    src_name = f"{base_name}.kt"
    expected = test_file.replace(f"/{ss}/", f"/{src_ss}/")
    expected = re.sub(r"/[^/]+\.kt$", f"/{src_name}", expected)
    if expected in all_files:
        return expected
    for f in all_files:
        if f.endswith(src_name) and src_ss in f:
            return f
    return None


# Source set -> test source set mapping
_TEST_SET_MAP: dict[str, str] = {
    "commonMain": "commonTest",
    "androidMain": "androidTest",
    "iosMain": "iosTest",
    "jvmMain": "jvmTest",
    "desktopMain": "desktopTest",
    "nativeMain": "nativeTest",
}


def find_test_file(source_file: str, all_files: list[str]) -> str | None:
    """Find the test file corresponding to a source file.

    KMP convention: ``src/commonMain/kotlin/Foo.kt`` -> ``src/commonTest/kotlin/FooTest.kt``
    """
    ss = get_source_set(source_file)
    if not ss or ss not in _TEST_SET_MAP:
        return None

    test_ss = _TEST_SET_MAP[ss]
    base_name = PurePosixPath(source_file).stem
    test_name = f"{base_name}Test.kt"

    # Build expected test path by replacing source set in path
    expected = source_file.replace(f"/{ss}/", f"/{test_ss}/")
    expected = re.sub(r"/[^/]+\.kt$", f"/{test_name}", expected)

    # Direct match
    if expected in all_files:
        return expected

    # Fuzzy match: look for any file ending with the test name in the test source set
    for f in all_files:
        if f.endswith(test_name) and test_ss in f:
            return f

    return None


def map_source_to_tests(
    source_files: list[str],
    all_files: list[str],
) -> dict[str, list[str]]:
    """Map each source file to its test file(s)."""
    result: dict[str, list[str]] = {}
    for src in source_files:
        test = find_test_file(src, all_files)
        if test:
            result[src] = [test]
    return result
