# Decisions

## JSON schema design and tradeoffs

The JSON representation is intentionally conservative: it keeps the original assignment structure, source metadata, interpolation tokens, and reference metadata, while also recording includes and conditional blocks as first-class statements. This is the least-lossy shape for a migration tool because it preserves enough provenance to validate equivalence and explain mismatches without requiring a full re-implementation of the legacy language.

## Effective settings definition

Effective settings are the final, fully resolved values after applying all includes, conditional blocks, and interpolation rules in the legacy parser. The verifier compares these resolved settings between the legacy evaluator and the JSON evaluator. A configuration is considered equivalent only when the same section/key/value mapping is obtained under the same environment.

## Include, conditional, and interpolation decisions

- Includes are evaluated relative to the including file.
- `include_once` suppresses duplicate loads without changing semantics for later assignments.
- Conditional bodies run only when their environment variable is truthy (`ifdef`) or empty (`ifndef`).
- Last assignment wins within a section, matching legacy behavior.
- Environment interpolation and cross-key `$()` references are resolved recursively with explicit circular-reference and expansion-limit protections.

## What the verifier proves

The verifier proves that, for the supported fixture set and environment combinations, the converted JSON config evaluates to the same effective settings as the original `.pfcfg` file. It also surfaces mismatches with a precise section/key diff and distinguishes execution errors from expected behavioral differences.

## What it does not prove

It does not prove that arbitrary future `.pfcfg` files are valid under all runtime conditions. It also does not infer a runtime environment for missing values; such cases are reported as unmigratable rather than silently defaulted.

## Known gaps

- The converter is deliberately scoped to the project’s supported legacy subset.
- Values that require runtime-only environment inputs without a default remain intentionally flagged as unmigratable.
- The project focuses on correctness and auditability rather than broad generality.

## If we had four more hours

We would add a richer CLI for file scanning, a JSON report writer with clearer summary output, and more fixture-driven tests around edge-case combinations, but without changing the semantics already proven by the current implementation.
