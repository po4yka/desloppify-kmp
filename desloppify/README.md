# Desloppify — Technical Internals

Desloppify is still a Python CLI, but its runtime surface is now focused on Android/iOS/KMP analysis. The shared engine exists to support the Kotlin and Swift analyzers that ship with the product, not to present a general multi-language scanner.

## Directory Layout

```text
desloppify/
├── cli.py              # Argparse entrypoint
├── state.py            # Persistent-state facade
├── hook_registry.py    # Detector-safe analyzer hook registry
├── app/                # CLI layer (commands, parser, output)
├── engine/             # Scan/scoring/state internals
│   ├── detectors/      # Shared detection engine (zero analyzer knowledge)
│   ├── planning/       # Prioritization and plan generation
│   ├── policy/         # Zones and scoring policy
│   ├── _scoring/
│   ├── _state/
│   └── _work_queue/
├── intelligence/       # Subjective/narrative/review layer
└── languages/
    ├── _framework/     # Shared analyzer framework, runtime, tree-sitter glue
    ├── kotlin/         # KMP/Compose/Android analyzer
    └── swift/          # iOS/Swift analyzer
```

## Architecture

```text
Layer 1: engine/detectors/       Shared detection engine. Data-in, data-out.
Layer 2: languages/_framework/   Shared analyzer contracts/helpers.
Layer 3: languages/<name>/       Kotlin or Swift analyzer config, phases, detectors, review hooks.
```

Import direction stays one-way: `languages/` -> `engine/detectors/`. Runtime-specific behavior is injected through analyzer hooks, not reverse imports.
Only the Kotlin and Swift analyzers are part of the documented product surface.

## Data Flow

```text
scan:    LangConfig -> LangRun(phases) -> generate_findings() -> merge_scan() -> state-{lang}.json
fix:     LangConfig.fixers -> fixer.fix() -> resolve in state
detect:  LangConfig.detect_commands[name](args) -> display
```

## Contracts

- **Detector**: `detect_*(data, config) -> list[dict]` with no direct Kotlin/Swift imports
- **Phase runner**: `_phase_*(path, lang) -> (list[Finding], dict[str, int])`
- **LangConfig**: static analyzer contract; owns phases, thresholds, hooks, and review guidance
- **LangRun**: per-invocation mutable runtime state such as zone maps, dependency graphs, and derived complexity

## Rules

- Entry command modules stay thin; orchestration lives below them
- Dynamic imports are limited to Kotlin/Swift analyzer discovery and hook extension points
- Persistent schema belongs to `state.py` and `engine/_state/`
- `LangRun` owns mutable runtime state, not `LangConfig`

## Non-Obvious Behavior

- **State scoping**: scans only auto-resolve findings for the same analyzer and path. A Kotlin pass over shared/Android code does not touch Swift iOS state.
- **Suspect guard**: if a detector drops from `>=5` findings to `0`, disappearances are held unless `--force-resolve` is used.
- **Scoring**: weighted by tier; strict score penalizes both open and `wontfix`.
- **Cascade effects**: fixing one category can surface the next category of work.
- **Optional tooling**: tree-sitter, `ktlint`, `detekt`, and `swiftlint` degrade gracefully when unavailable, with coverage warnings instead of hard failure.
