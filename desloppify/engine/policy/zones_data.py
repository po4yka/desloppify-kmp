"""Detector policy sets used by zone classification."""

SKIP_ALL_DETECTORS = frozenset(
    {
        "unused",
        "logs",
        "deprecated",
        "structural",
        "boilerplate_duplication",
        "props",
        "smells",
        "dupes",
        "single_use",
        "orphaned",
        "coupling",
        "facade",
        "naming",
        "patterns",
        "cycles",
        "flat_dirs",
        "test_coverage",
        "security",
    }
)

TEST_SKIP_DETECTORS = {
    "boilerplate_duplication",
    "dupes",
    "single_use",
    "orphaned",
    "coupling",
    "facade",
    "test_coverage",
    "security",
    "private_imports",
}

CONFIG_SKIP_DETECTORS = {
    "boilerplate_duplication",
    "smells",
    "structural",
    "dupes",
    "naming",
    "single_use",
    "orphaned",
    "coupling",
    "facade",
    "test_coverage",
    "security",
}

SCRIPT_SKIP_DETECTORS = {"coupling", "single_use", "orphaned", "facade"}
