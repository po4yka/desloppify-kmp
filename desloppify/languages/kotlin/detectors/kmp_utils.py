"""KMP source set detection utilities."""

from __future__ import annotations

from pathlib import PurePosixPath

KNOWN_SOURCE_SETS = frozenset({
    "commonMain", "androidMain", "iosMain", "iosArm64Main",
    "iosSimulatorArm64Main", "iosX64Main", "appleMain",
    "jvmMain", "commonTest", "androidTest", "iosTest",
    "androidUnitTest", "androidInstrumentedTest",
    "jvmTest", "desktopMain", "desktopTest",
    "nativeMain", "nativeTest", "linuxMain", "linuxTest",
})


def get_source_set(filepath: str) -> str | None:
    """Derive KMP source set from file path."""
    for part in PurePosixPath(filepath).parts:
        if part in KNOWN_SOURCE_SETS:
            return part
    return None


def is_common_main(filepath: str) -> bool:
    return get_source_set(filepath) == "commonMain"


def is_test_source_set(filepath: str) -> bool:
    ss = get_source_set(filepath)
    return ss is not None and "Test" in ss


def is_platform_source_set(filepath: str) -> bool:
    ss = get_source_set(filepath)
    if ss is None:
        return False
    return ss not in ("commonMain", "commonTest")
