# Session 01 — Understand Assignment + Inspect Source Material

## User Prompt

We are building the take-home assignment "Say It in JSON" for PipelineForge.

IMPORTANT:
Do NOT modify, create, delete, or overwrite any files in this session.
This is an investigation and planning session only.

Your job is to deeply analyze the repository and produce an evidence-based technical analysis that we will use before implementation.

Read and inspect these files/directories completely:

- assignment.md
- README.md
- briefs/platform-lead-brief.md
- briefs/format-reference.md
- starter/README.md
- starter/configs/

Inspect every .pfcfg file under starter/configs, including all nested files.

Do not assume undocumented behavior. Clearly distinguish:
1. behavior explicitly documented in the assignment/reference
2. behavior demonstrated by starter configs
3. behavior that is ambiguous or requires a design decision

Analyze and report:

1. Assignment requirements
   - What must be implemented
   - Required deliverables
   - What the verifier must prove
   - What "silent failure" means in this assignment

2. Complete .pfcfg semantics
   - sections and keys
   - values
   - comments
   - @include
   - @include_once
   - relative include paths
   - include ordering
   - repeated includes
   - conditional blocks
   - @ifdef
   - @ifndef
   - conditional includes
   - environment interpolation
   - ${VAR}
   - ${VAR:-default}
   - ${VAR:+alternate}
   - $(section.key) references
   - chained references
   - precedence/overrides
   - unresolved variables
   - circular references
   - malformed or unsupported syntax

3. Build an include/dependency map of the starter configs.
   For each important entry-point config, explain which files it loads and in what order.

4. Analyze every edge-case config and explain exactly what behavior it is testing.

5. Identify all environment variables used by the starter configs and explain how different environments affect effective settings.

6. Identify likely migration hazards where a naive converter could silently change behavior.

7. Propose what "effective settings" should mean for this assignment.
   Explain the evaluation order needed to reproduce legacy behavior.

8. Identify cases that should be considered unmigratable rather than guessed or silently converted.

9. Identify ambiguities in the format reference where we must make an explicit schema or evaluator decision.

10. Propose a phased implementation plan for:
    - legacy parser/evaluator
    - target JSON schema
    - converter
    - JSON evaluator
    - equivalence verifier
    - unmigratable report
    - tests

11. Propose CI and non-CI environment fixtures required by the assignment.

12. Most importantly, challenge your own conclusions.
    List assumptions that could cause a false equivalence result or silently change customer behavior.

Do not write implementation code yet.

At the end, provide:
A. Requirements summary
B. Legacy semantics
C. Include/dependency graph
D. Environment/conditional behavior
E. Migration hazards
F. Unmigratable cases
G. Open design decisions
H. Recommended implementation phases
I. Questions/ambiguities that need human judgment

Be precise and reference specific files and examples from the repository whenever possible.

## Copilot Response

I’m reviewing the assignment and the config fixtures first so I can ground the analysis in the actual documented behavior and the starter examples before summarizing the semantics and risks.

Searched for files matching `**/*.pfcfg`, 15 matches

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

## Evidence base

I inspected the assignment docs and the full starter config tree, including all .pfcfg files under `configs`, and cross-checked the documented rules against the actual fixtures.

This is the key distinction:

1. Explicitly documented behavior
   - The assignment and the reference in `assignment.md`, `platform-lead-brief.md`, and `format-reference.md` give the baseline semantics: INI-like sections and keys, comments, include directives, conditional blocks, environment interpolation, and “effective settings” as the merged/resolved reality.
   - The reference is intentionally partial: it says several rules are disputed and left to the migration design.

2. Behavior demonstrated by starter configs
   - The actual sample trees under `configs` show the practical ordering rules and precedence behavior:
     - includes are merged in a linear, file-ordered way,
     - later assignments override earlier ones,
     - `@include_once` is tracked per entry config,
     - conditional blocks can change both includes and key values,
     - interpolation may reference both environment variables and previously merged config keys,
     - unresolved values and circular references are treated as errors, not loops.

3. Ambiguous / design-decision behavior
   - The docs explicitly call out some rules as open questions: conditional evaluation vs. includes, expansion pass limits, exact semantics of circular references, schema representation for includes/interpolation, and how to represent “equivalent effective settings” in JSON.
   - These are not minor details; they are central to silent-failure risk.

---

## 1) Assignment requirements

### What must be implemented
From `assignment.md` and `platform-lead-brief.md`:

- A target JSON schema for the legacy .pfcfg config.
- A converter from .pfcfg to JSON.
- A reference evaluator for legacy .pfcfg that computes effective settings for a given environment.
- An equivalence verifier comparing legacy effective settings vs. JSON-path effective settings.
- A machine-readable unmigratable report that calls out items that cannot be auto-converted or verified.

### Required deliverables
The deliverables are explicit in `assignment.md`:

- A working artifact in `solution/` containing schema, converter, evaluator, test harness, and README.
- AI session exports in `sessions/` with full tool transcripts.
- A short decisions note in `DECISIONS.md` describing schema choices, evaluation semantics, and known gaps.

### What the verifier must prove
The verifier must show:

- for each supported config entry, legacy and JSON produce the same effective settings under the same environment,
- the proof is environment-sensitive and runs under at least:
  - a CI-like fixture where `CI` is set and non-empty,
  - a non-CI fixture where `CI` is unset or empty,
- it reports pass/fail by config and includes enough details for debugging.

### What “silent failure” means here
The platform brief is explicit: a migration that “looks correct” but changes semantics is dangerous because customer builds fail later, not immediately. The assignment is intentionally about proving equivalence, not merely parsing or serializing successful text.

This is the core risk from `platform-lead-brief.md`:

- syntax is translated correctly,
- semantics are changed silently,
- the wrong config goes live,
- production behavior diverges only under specific env vars or cached conditions.

---

## 2) Complete .pfcfg semantics

### Sections and keys
From `format-reference.md`:

- Section headers are `[name]` or `[dotted.path]`.
- Keys are declared as `key = value` under the most recent section.
- A dotted section name such as `[parent.child]` is semantically nested; the sample configs use this pattern in `toolchains.pfcfg`, e.g. `[toolchain.node]` and `[notify.email]`.

### Values
- Quoted values use double quotes with escape handling for `\"` and `\\`.
- Unquoted values cannot begin or end with whitespace; surrounding whitespace is trimmed.
- List values are comma-separated without spaces, e.g. `steps = install,lint,test,build` in `node-build.pfcfg`.
- Values are strings unless the legacy consumer later interprets them as booleans or numbers; the reference does not norm them at parse time.

### Comments
- `#` and `;` are line comments.
- This is demonstrated throughout the config files, including `pipeline.pfcfg` and `interpolation-cascade.pfcfg`.

### @include
From `format-reference.md`:

- `@include path.pfcfg` merges an included file’s tree into the current config tree.
- Include directives must appear before any section headers in a file.
- Paths are relative to the directory containing the directive.

This is evidenced by:
- `node-build.pfcfg` using `@include ../_base/defaults.pfcfg`
- `pipeline.pfcfg` including both a template and a staging overlay.

### @include_once
- `@include_once` skips a file if that exact path was already included for the current top-level entry.
- This is crucial because the same include path can appear via multiple branches or file inclusion graphs.
- Example: `overrides.pfcfg` includes `_base/defaults.pfcfg` once even though the top-level pipeline includes it earlier.

### Relative include paths
The reference is explicit: relative paths resolve relative to the file containing the directive. This matters for:
- `container-publish.pfcfg` including `node-build.pfcfg`
- `pipeline.pfcfg` including sibling and ancestor paths using `Documents`

### Include ordering
The actual behavior is a merge in the order the parser encounters includes and subsequent declarations. The starter configs show that:
- later includes or later assignments override earlier config.
- merged state is cumulative, not hierarchical replacement.

Examples:
- `defaults.pfcfg` sets a base `key_prefix`.
- `ci-shared.pfcfg` later overrides `key_prefix` to `ci-${CACHE_NAMESPACE:-shared}` when `CI` is set.

### Repeated includes
- `@include` is additive and can repeat.
- `@include_once` suppresses repeats for the same path.
- This means the effective behavior is not just “file dependency graph”; it is a linearized inclusion sequence with dedupe rules.

### Conditional blocks
From `format-reference.md`:

- `@ifdef VAR`…`@endif` means the block is parsed only if `VAR` is set and non-empty.
- `@ifndef VAR`…`@endif` means it is parsed only if `VAR` is unset or empty.
- Conditionals can wrap section headers and keys; nested conditionals are supported.

Examples:
- `notifications.pfcfg` toggles `[notify.slack]` depending on `SLACK_WEBHOOK`.
- `container-publish.pfcfg` sets `push = true` only under `CI`.
- `pipeline.pfcfg` toggles `requires_approval` if `ACME_DEPLOY_TARGET` exists.
- `conditional-includes.pfcfg` selects between include trees based on `FEATURE_BETA`.

### Conditional includes
The reference is explicit that conditionals can wrap blocks, but the ordering between conditionals and includes is underspecified. The sample files resolve it by evaluating conditionals in the same linear parse stream as usual directives. That is the only interpretation consistent with the fixtures.

In `conditional-includes.pfcfg`:

- If `FEATURE_BETA` is set, it includes `node-build.pfcfg`
- Otherwise it includes `defaults.pfcfg` and then a legacy build section

This establishes that include selection is conditional and evaluated as part of the same parsed stream.

### Environment interpolation
From `format-reference.md`:

- `${VAR}` → env value if set, else empty string
- `${VAR:-default}` → value if set and non-empty, else default
- `${VAR:+alternate}` → alternate if set and non-empty, else empty
- `$(section.key)` → value of another key after merge
- dotted sections are dot-separated, e.g. `$(toolchain.node.binary)`

Examples:
- `defaults.pfcfg`: `image = ${PF_BUILD_IMAGE:-pfci/builder:22.04}`
- `node-build.pfcfg`: `install_cmd = $(toolchain.node.install_cmd)`
- `pipeline.pfcfg`: `compiler_path = /usr/local/bin/$(toolchain.default.compiler)`
- `interpolation-cascade.pfcfg`: `beta = prefix-$(cascade.alpha)-suffix`

### Chained references
The fixtures show that references can chain:

- `interpolation-cascade.pfcfg`
  - `alpha` resolves from an environment default,
  - `beta` uses `$(cascade.alpha)`,
  - `gamma` uses `${CASCADE_GAMMA:-$(cascade.beta)}`,
  - `delta` uses `${CASCADE_DELTA:-$(cascade.gamma)-final}`,
  - `epsilon` uses `$(cascade.delta)`.
- `pipeline.pfcfg`: `tag = ${ACME_RELEASE_TAG:-$(build.node_version)-${GIT_SHA:-dev}}`

This proves chained expansion is required and must be resolved in an ordered, iterative pass.

### Precedence / overrides
The starter configs show a clear precedence model:

- parse order matters,
- included files contribute in order,
- later assignments override earlier ones within the merged tree,
- active conditionals also participate in that same ordering.

Examples:
- `staging.pfcfg` overrides deploy strategy and target after the template.
- `ci-shared.pfcfg` overrides base build/cache/artifacts values when `CI` is set.
- `notifications.pfcfg` has mutually exclusive `@ifdef` vs `@ifndef` definitions for `[notify.slack]`.

### Unresolved variables
Examples show unresolved variables are not always fatal at parse time; they are fatal only when evaluation cannot resolve them under the supplied environment.

- `secrets.pfcfg`: `key_material = ${REQUIRED_SIGNING_SECRET}` with no default.
- `conditional-includes.pfcfg`: `api_endpoint = ${REQUIRED_API_ENDPOINT}` no default.

These are clear unmigratable cases unless the environment provides the value.

### Circular references
The reference explicitly says circular `$(section.key)` references are errors, not infinite loops. The sample confirms this:

- `interpolation-cascade.pfcfg` has:
  - `a = $(cascade.loop.b)`
  - `b = $(cascade.loop.a)`

This must be detected and reported as an error, not silently looped.

### Malformed or unsupported syntax
The reference does not specify a complete grammar for all malformed cases, but the converter/evaluator should explicitly detect and reject:

- unbalanced `@ifdef` / `@ifndef` / `@endif`
- include directives after the first section
- bad interpolation syntax
- references to missing sections or missing keys
- cycles in cross-key resolution
- expansion passes exceeding a reasonable limit

The reference explicitly calls out a production parser limit for expansion passes that is not specified; the implementation must choose a limit and embed it in the decisions note.

---

## 3) Include/dependency map of the starter configs

### Entry-point config: `pipeline.pfcfg`
Load order:

1. `container-publish.pfcfg`
   - includes `node-build.pfcfg`
   - node-build includes `defaults.pfcfg`
   - defaults includes `toolchains.pfcfg` and `notifications.pfcfg` via `@include_once`
2. `staging.pfcfg`
3. the file’s own section overrides at the bottom

Effect:
- template base values are loaded,
- staging overrides are applied after,
- then local file values override both if they are later in the stream.

### Entry-point config: `pipeline.pfcfg`
Load order:

1. `defaults.pfcfg`
2. `ci-shared.pfcfg`
3. if `PRODUCTION` is set:
   - `on-prem.pfcfg`
4. else:
   - `overrides.pfcfg`
5. local `pipeline.pfcfg` itself

Important nuance:
- `overrides.pfcfg` has `@include_once ../../_base/defaults.pfcfg`, but the same file was already loaded at the top, so the second include is skipped.

### Entry-point config: `pipeline.pfcfg`
Load order:

1. `node-build.pfcfg`
2. `secrets.pfcfg`
3. local pipeline section values

This is a key example of:
- env-driven secrets overlay,
- cross-key references,
- required env values without defaults.

### Edge entry: `conditional-includes.pfcfg`
Load order under `FEATURE_BETA`:

1. `node-build.pfcfg`

Load order when `FEATURE_BETA` is unset:

1. `defaults.pfcfg`
2. local legacy sections
3. later feature and migration values

This file is testing both conditional inclusion and required-value semantics.

### Edge entry: `interpolation-cascade.pfcfg`
Load order:

1. `defaults.pfcfg`
2. local cascade block
3. active `@ifdef CI` branch that overrides `epsilon`
4. circular self-reference block in `[cascade.loop]`

This is the stress-test for expansion ordering and cycle detection.

---

## 4) Analyze every edge-case config

### `conditional-includes.pfcfg`
Tests:
- conditional include selection,
- active/inactive blocks changing the same key and section,
- required environment variables without defaults,
- optional environment value fallback with cross-reference default ordering,
- conditional env-specific blocks with no default values.
Notable lines:
- `api_endpoint = ${REQUIRED_API_ENDPOINT}`
- `fallback_endpoint = ${OPTIONAL_API_ENDPOINT:-$(migration.api_endpoint)}`

This config strongly implies:
- `${VAR:-$(other.key)}` must evaluate the default using the already-merged config tree,
- evaluation order matters,
- missing required values in the environment should be reported as unmigratable or failing equivalence.

### `interpolation-cascade.pfcfg`
Tests:
- interpolation order sensitivity,
- chained defaults and cross-key references,
- conditional override of a later value under `CI`,
- genuine circular reference detection.

This config is the strongest evidence that the evaluator must do iterative expansion with:
- dependency tracking,
- cycle detection,
- a maximum expansion pass limit.

### `secrets.pfcfg`
Tests:
- choice between secrets backends based on `VAULT_ADDR`,
- missing-value semantics without defaults,
- environment-driven drift between fixture environments.

This config is also a signal that some config keys are not “migratable by default” because they are inherently env-dependent and can be invalid in some CI/non-CI contexts.

---

## 5) Environment variables used by the starter configs and their effects

This is the set of environment values that meaningfully alter effective settings:

- `CI`
- `CACHE_NAMESPACE`
- `PF_BUILD_IMAGE`
- `NODE_VERSION`
- `PKG_MGR`
- `NOTIFY_SUCCESS`
- `NOTIFY_FAILURE`
- `BUILD_NOTIFY_LIST`
- `SLACK_WEBHOOK`
- `SLACK_CHANNEL`
- `NODE_ENV`
- `TEST_RUNNER`
- `COVERAGE_MIN`
- `LINT_STRICT`
- `CONTAINER_REGISTRY`
- `CONTAINER_REPO`
- `GIT_SHA`
- `DOCKERFILE`
- `BUILD_PLATFORMS`
- `DEPLOY_APPROVAL`
- `ACME_RELEASE_TAG`
- `ACME_DEPLOY_TARGET`
- `PRODUCTION`
- `GLOBEX_ENV`
- `RELEASE_VERSION`
- `SIGNING_KEY_ID`
- `SIGNING_ALG`
- `VAULT_ADDR`
- `VAULT_SECRET_PATH`
- `REQUIRED_SIGNING_SECRET`
- `FEATURE_BETA`
- `OPTIONAL_API_ENDPOINT`
- `REQUIRED_API_ENDPOINT`
- `MIGRATION_AUDIT`
- `MIGRATION_AUDIT_USER`
- `MIGRATION_AUDIT_TICKET`
- `CASCADE_ALPHA`
- `CASCADE_GAMMA`
- `CASCADE_DELTA`

### Environment-driven differences observed in fixtures
- With `CI` set:
  - base build parallelism becomes true and retry_count becomes 0 in `ci-shared.pfcfg`
  - container publish sets `push = true` in `container-publish.pfcfg`
  - notifications may include Slack
- With `PRODUCTION` set:
  - `on-prem.pfcfg` is included instead of `overrides.pfcfg`
- With `VAULT_ADDR` set:
  - secrets provider becomes Vault in `secrets.pfcfg`
- With `FEATURE_BETA` set:
  - different include path and feature flag in `conditional-includes.pfcfg`
- With values missing:
  - the configuration becomes invalid or unmigratable in the same way the legacy system would be invalid without the required env.

---

## 6) Likely migration hazards where a naive converter could silently change behavior

1. Wrong include ordering
   - If the converter flattens includes in a different order than the legacy parse, values can silently overwrite the wrong keys.

2. Wrong `@include_once` behavior
   - A naive dedupe can drop required values or keep duplicates based on path normalization rather than exact path semantics.

3. Wrong conditional evaluation timing
   - If a converter evaluates conditionals after merge instead of in parse order, active/inactive blocks can change which file content is included.

4. Wrong interpolation evaluation order
   - `${VAR:-$(section.key)}` and `$(section.key)` may depend on other keys being resolved first. A naive pass that resolves env vars before config refs can change results.

5. Wrong treatment of circular refs
   - A naive converter may silently produce a partial value or a loop instead of reporting an error.

6. Wrong environment semantics
   - If the JSON evaluator treats empty strings and unset values as same, it can differ from the legacy `@ifdef` and `${VAR:-default}` rules.

7. Wrong comparison basis
   - A naive verifier may compare raw text or the first-pass parse tree instead of the effective resolved settings, which misses the actual semantics.

8. Silent coercion of booleans and lists
   - The legacy format is string-based and later semantics depend on how a consumer interprets strings, especially `false`, `0`, `on`, `off`, empty string, and list values. A converter can incorrectly normalize these.

---

## 7) What “effective settings” should mean for this assignment

Effective settings should mean:

- the fully merged config tree after all `@include` directives and conditional blocks are processed,
- with all environment interpolations and cross-key references resolved against that merged tree,
- under a concrete environment fixture.

A practical evaluation order for reproducibility:

1. Start with empty config state.
2. Read the entry file in lexical order.
3. Process directives in order:
   - `@include` files recursively,
   - `@include_once` skip exact duplicates,
   - `@ifdef` / `@ifndef` blocks include or exclude text based on the current environment,
   - section assignments and key assignments are merged into the config tree.
4. After the tree is complete, resolve all interpolation:
   - `${VAR}` / `${VAR:-default}` / `${VAR:+alternate}`
   - `$(section.key)` and chained references
5. Detect:
   - unresolved variables,
   - circular references,
   - expansion-pass overflow,
   - malformed syntax.
6. Emit the final resolved key-value map as the effective settings.

This is the only definition that matches the platform brief’s “after includes, conditionals, and interpolation are resolved, what does the pipeline actually see?” language in `platform-lead-brief.md`.

---

## 8) Cases that should be considered unmigratable rather than guessed or silently converted

These are not “skip and hope” cases:

- Required env variables with no default:
  - `${REQUIRED_SIGNING_SECRET}` in `secrets.pfcfg`
  - `${REQUIRED_API_ENDPOINT}` in `conditional-includes.pfcfg`
- Unresolvable circular references:
  - `interpolation-cascade.pfcfg`
- Expansion pass limit exceeded:
  - any expansion chain that exceeds the chosen limit
- Files with malformed directive syntax or invalid include targets
- Any generated JSON that cannot represent the legacy semantics without inventing behavior not specified by the docs

These should be surfaced as entries in the unmigratable report with `file`, `section`, `key`, `reason`, and optionally `line`.

---

## 9) Ambiguities in the format reference where we must make an explicit schema/evaluator decision

These are the major open design choices:

- How to represent include directives in JSON
  - Options: preserve an `includes` array, inline a merged object, or carry metadata with a provenance trail.
- How to represent config values that are not pure strings
  - lists, booleans, and numbers exist in semantics but are not explicitly typed in the reference.
- How to preserve conditional evaluation
  - as a processed tree with active conditions only, or as metadata recording conditions that were evaluated.
- How to preserve unresolved or conditional references
  - as strings with placeholders, or as explicit `interpolation` objects carrying source and expression.
- Expansion-pass limit
  - the reference says a production parser enforces a limit but does not specify it, so the implementation must pick one and document it.
- Circular detection
  - the reference says “error, not infinite loop,” but the concrete error format is not specified.

This is exactly why the assignment says the schema and evaluator choices must be documented in the decisions note.

---

## 10) Proposed phased implementation plan

### Phase 1 — Legacy parser/evaluator
- Build a parser for INI-like `.pfcfg` with:
  - section parsing
  - key-value parsing
  - comment handling
  - include directives
  - conditional block handling
  - environment resolution
- Implement `@include` and `@include_once` semantics exactly against the starter fixtures.
- Build a merged tree with deterministic ordering.

### Phase 2 — Target JSON schema
- Define a JSON representation that preserves:
  - `includes` as explicit provenance
  - conditionals as explicit metadata or as pre-merged active blocks
  - references as literal strings or structured interpolation nodes
- Keep the schema honest about what it does not round-trip.

### Phase 3 — Converter
- Convert each entry-point config to the target JSON representation.
- Preserve path-relative include metadata and provenance.
- Add conversion diagnostics for unhandled or ambiguous constructs.

### Phase 4 — JSON evaluator
- Implement an evaluator that consumes the converted JSON and produces the same effective settings as the legacy parser.
- This is the equivalent of the “trusted interpreter” for the new format.

### Phase 5 — Equivalence verifier
- For each config and fixture environment:
  - compute legacy effective settings
  - compute JSON effective settings
  - compare exact resolved maps
  - emit pass/fail + detailed diff
- Ensure at least CI and non-CI fixtures are covered.

### Phase 6 — Unmigratable report
- Emit machine-readable JSON or NDJSON.
- Record:
  - file
  - section
  - key
  - reason
  - optional line
- Use it for missing env vars, malformed syntax, circular refs, unsupported patterns.

### Phase 7 — Tests
- Unit tests for parser semantics
- Fixture tests for each starter config
- Env-specific tests for CI and non-CI cases
- Negative tests for cycles, unresolved values, malformed directives

---

## 11) CI and non-CI environment fixtures required by the assignment

Need at least:

- CI fixture
  - `CI=1`
  - plus representative variables:
    - `CACHE_NAMESPACE=shared`
    - `SLACK_WEBHOOK=https://example.invalid/hook`
    - `SLACK_CHANNEL=#release`
    - `BUILD_NOTIFY_LIST=ops@example.invalid`
    - `ACME_DEPLOY_TARGET=staging`
    - `FEATURE_BETA=1` for edge-case testing
- Non-CI fixture
  - `CI` unset or empty
  - examples:
    - `CACHE_NAMESPACE=default`
    - no `SLACK_WEBHOOK`
    - `PRODUCTION` unset
    - `FEATURE_BETA` unset
- Additional fixtures for:
  - `PRODUCTION=1` to choose on-prem path
  - `VAULT_ADDR=https://vault.example.invalid`
  - `REQUIRED_SIGNING_SECRET=...`
  - `REQUIRED_API_ENDPOINT=https://api.example.invalid`
  - `OPTIONAL_API_ENDPOINT=https://optional.example.invalid`
  - `CASCADE_ALPHA`, `CASCADE_GAMMA`, `CASCADE_DELTA` values for interpolation chain tests

This set is required because several configs are only valid under different environment combinations.

---

## 12) Challenge my own conclusions

The biggest risk is false equivalence.

Potential false assumptions:

- Assuming include order is just “graph order” rather than “parse order”
- Assuming `@ifdef` and `@ifndef` are evaluated only once instead of at the moment each block is interpreted
- Assuming `$(section.key)` can always resolve from a final merged tree, even when the key is defined later in the same include stream
- Assuming unresolved env values become empty strings rather than errors in the legacy system
- Assuming defaults and alternates only apply to environment vars, not to cross-key references
- Assuming deduplicating includes by normalized path is equivalent to exact-path include_once semantics
- Assuming runtime environment is stable while the config is being evaluated; in practice, environment is part of the effective settings, so fixtures must be explicit
- Assuming JSON “lossless” conversion is possible when the legacy format is not purely data but also contains directives and resolution metadata

These assumptions can create a converter that passes a happy-path diff while silently changing production behavior.

---

## A. Requirements summary

The assignment is not simply a parser challenge. It is a semantic equivalence challenge under environment variation. The real deliverable is a verifier that proves the JSON representation computes the same effective settings that the legacy config would produce for the same environment.

## B. Legacy semantics

The legacy semantics are:
- flat INI-like file structure with section and key merges
- includes before sections
- environment-dependent conditionals
- environment and cross-key interpolation
- last assignment wins in merge order
- circular refs and unresolved values are errors

## C. Include/dependency graph

The key dependency flows are:
- `pipeline.pfcfg` → `container-publish.pfcfg` → `node-build.pfcfg` → `defaults.pfcfg` → `toolchains.pfcfg`, `notifications.pfcfg`
- `pipeline.pfcfg` → `defaults.pfcfg`, then `ci-shared`, conditional `on-prem` or `overrides`
- `pipeline.pfcfg` → `node-build.pfcfg`, `secrets.pfcfg`

## D. Environment/conditional behavior

The effective settings shift based on:
- `CI`
- `PRODUCTION`
- `FEATURE_BETA`
- `VAULT_ADDR`
- many service-specific env vars and default fallbacks

These values are not just “extra config”; they determine which files are included and which keys are active.

## E. Migration hazards

Main hazards:
- include-order mistakes
- conditional mis-evaluation
- interpolation-order errors
- loss of circular-ref detection
- mistreatment of required env values as optional defaults

## F. Unmigratable cases

These should be reported rather than guessed:
- required env vars without defaults
- circular refs
- unsupported or malformed directives
- expansion overflow
- any case where the JSON schema cannot preserve legacy semantics without inventing behavior

## G. Open design decisions

The biggest explicit decisions to make:
- how JSON stores includes and conditionals
- how to encode interpolation and cross-key references
- how to represent unresolved values
- what expansion limit to enforce
- what constitutes equivalence in a schema that does not have direct legacy semantics

## H. Recommended implementation phases

1. Legacy parser/evaluator
2. target JSON schema
3. converter
4. JSON evaluator
5. equivalence verifier
6. unmigratable report
7. tests and fixtures

## I. Questions/ambiguities that need human judgment

- What is the exact semantics of conditional evaluation relative to include evaluation?
- What is the chosen expansion-pass limit?
- Should unresolved variables be treated as fatal during evaluation or just as unresolved placeholders in the JSON representation?
- How much provenance should the JSON schema preserve for includes and conditionals?
- Should the JSON format preserve original literal strings exactly, or only final effective values?

> The safest recommendation is to treat the legacy parser as the ground truth for equivalence and to make every JSON representation explicitly carry metadata that explains how it encoded include, conditional, and interpolation semantics. That keeps the migration honest and prevents silent drift.
