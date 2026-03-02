"""KMP review guidance — holistic dimensions, migration patterns, API surface."""

from __future__ import annotations

import re
from typing import Any

# -- Constants required by the standardization contract --

REVIEW_GUIDANCE = {
    "patterns": [
        "expect/actual declarations should be complete for all targets",
        "commonMain should not import platform-specific APIs",
        "Compose @Composable functions should hoist state",
        "Coroutines: prefer structured concurrency over GlobalScope",
        "K/N new memory model: remove @SharedImmutable, @ThreadLocal, .freeze()",
    ],
    "naming": [
        "Kotlin naming: camelCase functions, PascalCase classes",
        "Source sets: commonMain, androidMain, iosMain, etc.",
        "Test files: FooTest.kt for Foo.kt",
    ],
    "auth": [
        "Check route-level authorization on Ktor endpoints",
        "Verify session/token validation in API handlers",
        "Ensure no hardcoded secrets in shared source sets",
    ],
}

MIGRATION_MIXED_EXTENSIONS: list[tuple[str, str]] = [
    (".java", ".kt"),
]

LOW_VALUE_PATTERN = re.compile(
    r"(?:BuildConfig|R\.kt|generated|build/)"
)

HOLISTIC_REVIEW_DIMENSIONS = [
    "cross_module_architecture",
    "convention_outlier",
    "error_consistency",
    "abstraction_fitness",
    "ai_generated_debt",
    "package_organization",
    "dependency_health",
    "high_level_elegance",
    "mid_level_elegance",
    "low_level_elegance",
    "design_coherence",
]

MIGRATION_PATTERN_PAIRS = [
    # (name, old_regex, new_regex)
    (
        "K/N old memory model\u2192new",
        re.compile(r"\.freeze\(\)|@SharedImmutable|@ThreadLocal"),
        re.compile(r"\b(?:new\s+memory\s+model|stateIn|shareIn)\b"),
    ),
    (
        "GlobalScope\u2192structured concurrency",
        re.compile(r"GlobalScope\.(launch|async)"),
        re.compile(r"coroutineScope\s*\{"),
    ),
    (
        "Dispatchers.IO\u2192Default",
        re.compile(r"Dispatchers\.IO\b"),
        re.compile(r"Dispatchers\.Default\b"),
    ),
]


def review_guidance() -> dict[str, Any]:
    """Return review guidance configuration for KMP projects."""
    return {
        "focus_areas": [
            "source-set boundary adherence (commonMain should not leak platform APIs)",
            "expect/actual completeness for all configured targets",
            "Compose state management (remember, side effects, hoisting)",
            "coroutine structured concurrency (no GlobalScope in production)",
            "deprecated K/N memory model patterns",
        ],
        "anti_patterns": [
            "ViewModel in @Composable parameters",
            "mutableStateOf outside remember{}",
            "platform imports in commonMain",
            "runBlocking in shared code",
        ],
    }


def module_patterns(filepath: str) -> list[str]:
    """Alias for standardization contract."""
    return review_module_patterns(filepath)


def api_surface(filepath: str) -> list[str]:
    """Alias for standardization contract."""
    return review_api_surface(filepath)


def review_module_patterns(filepath: str) -> list[str]:
    """Extract module-level patterns for review from a Kotlin file."""
    patterns = []
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return patterns

    # Detect architectural patterns
    if re.search(r"@Composable", content):
        patterns.append("compose-ui")
    if re.search(r"\bexpect\b", content):
        patterns.append("kmp-expect")
    if re.search(r"\bactual\b", content):
        patterns.append("kmp-actual")
    if re.search(r"class\s+\w*ViewModel", content):
        patterns.append("viewmodel")
    if re.search(r"class\s+\w*Repository", content):
        patterns.append("repository")
    if re.search(r"@(Dao|Entity|Database)\b", content):
        patterns.append("room-db")
    if re.search(r"\b(Ktor|HttpClient)\b", content):
        patterns.append("ktor-networking")

    return patterns


def review_api_surface(filepath: str) -> list[str]:
    """Extract public API surface for review."""
    surface = []
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            for line in f:
                # Public fun/class/interface/object declarations
                m = re.match(
                    r"^\s*(?:public\s+)?(?:fun|class|interface|object|val|var)\s+(\w+)",
                    line,
                )
                if m and not line.strip().startswith("private"):
                    surface.append(m.group(1))
    except OSError:
        pass
    return surface
