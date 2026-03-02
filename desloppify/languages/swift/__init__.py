"""Swift language plugin — swiftlint + KMP interop awareness."""

from desloppify.engine.policy.zones import COMMON_ZONE_RULES, Zone, ZoneRule
from desloppify.languages._framework.generic import generic_lang
from desloppify.languages._framework.treesitter import SWIFT_SPEC

# KMP-aware zone rules for Swift
_SWIFT_ZONE_RULES = [
    ZoneRule(Zone.GENERATED, ["/build/", "/DerivedData/", ".generated.swift"]),
    ZoneRule(Zone.TEST, [
        "/Tests/", "/UITests/",
        "Tests.swift", "Test.swift", "Spec.swift",
    ]),
    ZoneRule(Zone.CONFIG, [
        "Package.swift", "Podfile",
        "project.pbxproj", ".xcconfig",
    ]),
    ZoneRule(Zone.VENDOR, ["/Pods/", "/Carthage/", "/.build/"]),
    *COMMON_ZONE_RULES,
]

generic_lang(
    name="swift",
    extensions=[".swift"],
    tools=[
        {
            "label": "swiftlint",
            "cmd": "swiftlint lint --reporter json",
            "fmt": "json",
            "id": "swiftlint_violation",
            "tier": 2,
            "fix_cmd": "swiftlint --fix",
        },
    ],
    depth="shallow",
    detect_markers=[
        "Package.swift",
        # KMP iOS entry points
        "iosApp/",
        "iosMain/",
    ],
    treesitter_spec=SWIFT_SPEC,
    zone_rules=_SWIFT_ZONE_RULES,
)
