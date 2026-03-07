# Desloppify - an agent harness for KMP codebases

[![PyPI version](https://img.shields.io/pypi/v/desloppify)](https://pypi.org/project/desloppify/) ![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

Desloppify is an agent-first code health scanner for Kotlin Multiplatform, Compose Multiplatform, Android, and native iOS repositories. It combines mechanical detection with subjective LLM review, keeps state across runs, and gives your agent a prioritized queue of what to fix next.

<img src="assets/explained.png" width="100%">

The score is the north star. A high strict score should correlate with a KMP/mobile codebase that has clean boundaries, deliberate UI state management, safe platform usage, and less hidden debt.

Focused analyzers:

- `kotlin`: KMP shared code, Android source sets, Gradle, AndroidManifest, Compose Multiplatform
- `swift`: native iOS modules, `Info.plist`, Swift code quality, dependency hygiene, KMP interop edges

If a repository contains both Kotlin and Swift, Desloppify auto-detects the dominant target. Use `--lang kotlin` or `--lang swift` when you want to force a specific pass.

That score still generates a scorecard badge for your GitHub profile or README:

<img src="assets/scorecard.png" width="100%">

## Quickstart for agents

Paste this prompt into your agent:

```text
I want you to improve the quality of this Android/iOS/KMP codebase. To do this, install and run desloppify.
Run ALL of the following (requires Python 3.11+):

pip install --upgrade "desloppify[full]"
desloppify update-skill codex     # or claude, cursor, copilot, windsurf, gemini, opencode
desloppify scan --path .
desloppify next

Use --lang kotlin for shared/Android/KMP analysis and --lang swift for native iOS analysis if auto-detection picks the wrong target.

Your goal is to raise the strict score honestly. Follow `next` exactly, fix issues properly, resolve them, then run `next` again.
Use `plan` to reorder or cluster work when a batch of related fixes should land together.
```

## What it checks

- KMP boundaries: `commonMain` platform leakage, missing `expect`/`actual`, Kotlin/Native migration leftovers
- Compose quality: state hoisting issues, `remember` misuse, oversized composables, mixed concerns
- Android correctness: Gradle/KMP build config drift, deprecated Android APIs, `AndroidManifest.xml` security/config errors
- iOS correctness: `Info.plist` issues, Swift code smells, dependency setup problems
- Cross-cutting structure: duplication, coupling, large files, naming drift, orphaned modules, subjective architecture review

## The workflow

Run the outer loop occasionally:

```bash
desloppify scan --path .
desloppify status
```

Spend most of your time in the inner loop:

```bash
desloppify next
# fix the issue
# run the exact resolve/done command that next recommends
```

Useful commands:

| Command | Description |
|---------|-------------|
| `scan [--reset-subjective]` | Run detectors, update state |
| `status` | Show score dashboard |
| `next [--count N]` | Show the next highest-value item(s) |
| `show <pattern>` | Inspect findings by file, detector, or ID |
| `plan` | Generate or manage the living prioritized queue |
| `review --run-batches --runner codex --parallel --scan-after-import` | Run subjective review batches |
| `langs` | List supported analyzers and detector coverage |
| `viz` | Generate an HTML treemap of files/findings |

## Why this exists

Mobile and KMP codebases rot in specific ways:

- platform APIs leak into shared code
- Compose screens accumulate state and orchestration
- Gradle/build logic drifts from current KMP guidance
- iOS wrappers and native entry points diverge from shared expectations
- architectural quality keeps slipping even when lint is green

Desloppify is built so an agent can see those issues, prioritize them, and work through them over multiple sessions without losing context.

If you'd like to join a community of vibe engineers who want to build beautiful things, [come hang out](https://discord.gg/aZdzbZrHaY).

<img src="assets/engineering.png" width="100%">

---

<details>
<summary><strong>Technical details</strong></summary>

### Supported targets

- `kotlin`: full analyzer for KMP/Compose/Android projects
- `swift`: shallow analyzer for native iOS and KMP iOS host code

### Optional extras

- `pip install "desloppify[treesitter]"` for deeper AST analysis
- `pip install "desloppify[scorecard]"` for scorecard image generation
- `pip install "desloppify[full]"` for everything above

### Scoring

- Overall score = **40% mechanical** + **60% subjective**
- Strict score penalizes both open and `wontfix`
- Weighted tiers mean large architectural problems matter more than cosmetic ones

### Internal layout

```text
engine/detectors/                 <- Generic algorithms
languages/_framework/             <- Shared analyzer framework
languages/kotlin/                 <- KMP/Compose/Android analyzer
languages/swift/                  <- iOS/Swift analyzer
intelligence/review/              <- Subjective review packet + merge flow
```

### Notes

- Subjective reviews are intentionally blind to score targets.
- Fixing one detector can surface work for another; temporary score drops are normal.
- The public product scope is Android/iOS/KMP only, even though the analyzer framework remains extensible internally.

</details>
