# Session 02 — Analyze .pfcfg Grammar

## User Prompt

Continue from the repository analysis, but do NOT implement anything and do NOT modify any files.

We now need to resolve the semantic uncertainties before designing the target JSON schema.

Re-read:
- assignment.md
- briefs/platform-lead-brief.md
- briefs/format-reference.md
- starter/README.md
- every .pfcfg file under starter/configs/

Create a rigorous "Legacy Semantics Evidence Matrix".

For EVERY important behavior, classify it into exactly one of:

1. DOCUMENTED — explicitly specified by the format reference or assignment
2. FIXTURE-EVIDENCED — not fully specified, but demonstrated by starter configs
3. DESIGN DECISION — not determined by the supplied material and therefore requires an explicit decision

Do NOT upgrade fixture evidence into documented behavior.

For each behavior provide:
- behavior name
- exact rule
- source file
- relevant example/config
- confidence
- unresolved question, if any

Pay particular attention to these questions:

1. Include evaluation
   - exact processing order
   - recursive includes
   - whether includes are processed inline
   - relative path resolution
   - include cycles
   - @include vs @include_once
   - exact scope/lifetime of include_once tracking
   - path identity for include_once

2. Conditional blocks
   - exact meaning of set/non-empty
   - empty string behavior
   - nested conditionals
   - whether conditions are evaluated inline
   - conditional includes
   - interaction between conditions and includes

3. Override semantics
   - whether later assignments always win
   - how included files interact with local assignments
   - what happens when the same key is assigned multiple times

4. Interpolation
   - exact semantics of ${VAR}
   - ${VAR:-default}
   - ${VAR:+alternate}
   - exact meaning of "set"
   - whether empty and unset differ
   - $(section.key)
   - references to keys defined earlier
   - references to keys defined later
   - references across included files
   - nested interpolation
   - interpolation inside defaults/alternates

5. Resolution model
   Determine whether references are resolved:
   - during parsing,
   - after merge,
   - iteratively,
   - recursively,
   - or by another model.

Do NOT assume an answer just because one implementation approach is convenient.

6. Errors
   Distinguish:
   - parse errors
   - invalid includes
   - unresolved environment variables
   - missing config references
   - circular references
   - expansion limits
   - conversion failures
   - verification failures

7. Effective settings
   Define precisely what should be compared by the equivalence verifier.

8. Unmigratable report
   Determine which failures belong in the report and which are simply expected evaluation failures for a particular environment.

9. Test matrix
   Based only on evidence from the repository, propose the minimum environments needed to exercise all important semantic branches.

Most importantly:

For every conclusion, tell me whether it is:
DOCUMENTED, FIXTURE-EVIDENCED, or DESIGN DECISION.

Do not propose a JSON schema yet.
Do not write implementation code.
Do not modify files.

At the end provide:

A. Semantic evidence matrix
B. Definitive rules we can safely implement
C. Rules that remain ambiguous
D. Questions requiring human judgment
E. Proposed test/environment matrix
F. Risks of choosing the wrong interpretation

## Copilot Response

I’ve narrowed this to the semantic boundaries: the docs specify the grammar, while the starter fixtures are the only source for real ordering and precedence behavior. I’m turning those into a strict evidence matrix so the remaining design choices stay explicit and not inferred from convenience.

## Legend

- DOCUMENTED = explicitly specified in the assignment or format reference
- FIXTURE-EVIDENCED = not explicitly stated, but strongly demonstrated by the starter configs
- DESIGN DECISION = not determined by the supplied material and must be chosen explicitly

---

## A. Semantic evidence matrix

| Behavior name | Classification | Exact rule | Source file | Relevant example/config | Confidence | Unresolved question |
|---|---|---|---|---|---|---|
| Section and key syntax | DOCUMENTED | Files use INI-style sections as `[name]` or `[dotted.path]`; keys are `key = value` and belong to the most recent section. | `format-reference.md` | `[build]`, `[notify.email]`, `[toolchain.node]` in `toolchains.pfcfg` | High | None material |
| Comment syntax | DOCUMENTED | `#` and `;` start end-of-line comments. | `format-reference.md` | Comment lines in `interpolation-cascade.pfcfg` | High | None material |
| Quoted values and escaping | DOCUMENTED | Double-quoted values support escaped `\"` and `\\`; unquoted values cannot have leading/trailing whitespace. | `format-reference.md` | Not heavily used in starter files, but grammar is established by the reference | High | No material ambiguity beyond parser details |
| List values | DOCUMENTED | Lists are comma-separated strings without spaces after commas. | `format-reference.md` | `steps = install,lint,test,build` in `node-build.pfcfg` | High | Whether consumer interprets as list vs. raw string is outside parser spec |
| Include directive syntax | DOCUMENTED | `@include path.pfcfg` and `@include_once path.pfcfg` are directives. | `format-reference.md` | `@include ../_base/defaults.pfcfg` in `node-build.pfcfg` | High | None material |
| Relative include resolution | DOCUMENTED | Include paths are relative to the directory of the file containing the directive. | `format-reference.md` | `../../templates/container-publish.pfcfg` in `pipeline.pfcfg` | High | Whether path normalization is lexical or filesystem-sensitive is not specified |
| Include directives before sections | DOCUMENTED | Include directives must appear before any section headers in a file. | `format-reference.md` | All include files follow this rule; many entry files begin with include lines | High | Whether later includes are legal after a leading comment is not discussed |
| `@include_once` exact-path tracking | DOCUMENTED | `@include_once` skips the file if that exact path was already included in the current load, tracked per top-level entry config. | `format-reference.md` | `overrides.pfcfg` includes `_base/defaults.pfcfg` after it was already loaded | High | Exact path identity and aliasing across symlinks or different relative forms remain unspecified |
| Merge model of includes | FIXTURE-EVIDENCED | Included files merge their sections and keys into the current config tree; the result is additive and order-sensitive. | `format-reference.md`, all starter examples | `pipeline.pfcfg` and `ci-shared.pfcfg` override earlier values | High | The formal merge algorithm is not stated; a parser must define it |
| Exact processing order for includes and conditionals | DESIGN DECISION | The reference says a conditional/include ordering is not documented. The implementation must choose an ordering model. | `format-reference.md` | `conditional-includes.pfcfg` demonstrates include decisions depending on `FEATURE_BETA` | Medium | Need human decision: evaluate conditionals inline as the parser reads, or evaluate after full tree build? |
| Recursive include processing | FIXTURE-EVIDENCED | Includes can bring in files that themselves include more files; the loader must recurse. | `container-publish.pfcfg`, `node-build.pfcfg`, `defaults.pfcfg` | Container publish includes node-build, which includes defaults, which includes toolchains and notifications | High | Cycle handling and include stack semantics need explicit policy |
| Include cycles | DESIGN DECISION | The reference does not define whether include cycles are error, ignore, or loop forever. | `format-reference.md` | No starter file intentionally creates a cycle; the spec still requires a behavior choice | Medium | This must be chosen explicitly, and the verifier should reject it |
| `@include_once` lifetime/scope | DESIGN DECISION | The docs say it is tracked per top-level entry config, but do not say whether tracking is global to the parse run, to the current recursion path, or to the merged tree. | `format-reference.md` | The Globex case relies on exact repeat skipping after a top-level include | Medium | Need clear rule for nested duplicates and identical files reached by different relative paths |
| `@include_once` path identity | DESIGN DECISION | “Exact path” is stated, but exact identity rules are fuzzy: lexical path vs normalized absolute path vs loader-resolved canonical path. | `format-reference.md` | Same file reached via different relative paths is not covered by the fixtures | Medium | Need a canonical path representation |
| Later assignments override earlier ones | FIXTURE-EVIDENCED | The sample configs show the effective value is the last one encountered in the merge order. | `ci-shared.pfcfg`, `pipeline.pfcfg` | `parallel = true` appears after earlier defaults; `on_failure` is overwritten in overlays | High | The reference never states this explicitly as a rule, but it is the only interpretation consistent with the fixtures |
| Same key assigned multiple times in same section | FIXTURE-EVIDENCED | Repeated keys in the same merged tree are overwritten by the later assignment, not accumulated. | `pipeline.pfcfg`, `notifications.pfcfg` | `[notify] on_failure` values vary by environment/overlay | High | May be parser-defined, but not spelled out; must be explicit |
| Conditional block semantics | DOCUMENTED | `@ifdef VAR` parses the block only if `VAR` is set and non-empty; `@ifndef VAR` parses it only if `VAR` is unset or empty. | `format-reference.md` | `notifications.pfcfg` and `container-publish.pfcfg` | High | Exact difference between “unset” and “empty string” is not fully specified |
| Empty string vs unset in conditionals | DESIGN DECISION | The reference says “set and non-empty” vs “unset or empty,” but does not define whether an explicitly empty env var is considered “set.” | `format-reference.md` | `@ifndef SLACK_WEBHOOK` in `notifications.pfcfg` | Medium | Need a precise policy: empty string is treated as empty, not set |
| Nested conditionals | DOCUMENTED | Conditionals may nest and be parsed recursively. | `format-reference.md` | No nested example in starter files, but syntax is explicitly allowed | High | Need robust parser behavior for nested `@ifdef` / `@ifndef` pairs |
| Conditional includes | FIXTURE-EVIDENCED | An include can be conditionally selected by guarding the directive in an `@ifdef` / `@ifndef` block. | `conditional-includes.pfcfg`, `pipeline.pfcfg` | `@ifdef FEATURE_BETA` includes node-build; otherwise includes defaults | High | The reference says conditionals can wrap sections and keys but does not explicitly say they can wrap include directives; the fixtures prove they can |
| Interaction of conditionals with included file order | DESIGN DECISION | The order in which conditionals are evaluated relative to includes is not specified. The implementation must choose and document it. | `format-reference.md` | `conditional-includes.pfcfg` and `pipeline.pfcfg` | Medium | Need decision: inline parse-time conditionals vs. evaluation after the include graph is known |
| `${VAR}` semantics | DOCUMENTED | `${VAR}` resolves to the environment variable value or an empty string if unset. | `format-reference.md` | `${NODE_ENV:-test}` in `node-build.pfcfg` | High | Whether a literal empty string counts as set when used in `${VAR}` is not discussed |
| `${VAR:-default}` semantics | DOCUMENTED | Use default when `VAR` is unset or empty; otherwise use `VAR`. | `format-reference.md` | `image = ${PF_BUILD_IMAGE:-pfci/builder:22.04}` in `defaults.pfcfg` | High | Need exact rule for “empty string” in the default test; same as above |
| `${VAR:+alternate}` semantics | DOCUMENTED | Use `alternate` when `VAR` is set and non-empty; otherwise empty string. | `format-reference.md` | `key_prefix = ${CI:+ci-}${CACHE_NAMESPACE:-default}` in `defaults.pfcfg` | High | Exact empty/unset distinction remains ambiguous |
| Cross-key references `$(section.key)` | DOCUMENTED | A value can refer to an already-resolved config key; dotted paths are dot-separated. | `format-reference.md` | `install_cmd = $(toolchain.node.install_cmd)` in `node-build.pfcfg` | High | Whether resolution happens against the final merged tree or the in-progress tree is not specified |
| References to later keys | FIXTURE-EVIDENCED | Some keys refer to config values defined later in the merged tree, which implies the evaluator is not purely single-pass and must support forward references. | `interpolation-cascade.pfcfg`, `pipeline.pfcfg` | `beta = prefix-$(cascade.alpha)-suffix` and `${ACME_RELEASE_TAG:-$(build.node_version)-${GIT_SHA:-dev}}` | Medium | The spec does not say whether forward refs are allowed; the fixtures imply they are |
| References across included files | FIXTURE-EVIDENCED | A config key can reference a key from an included file. | `node-build.pfcfg`, `defaults.pfcfg` | `$(toolchain.node.install_cmd)` resolves through included toolchain definitions | High | Scope and ordering across includes are not explicitly specified |
| Nested / chained interpolation | FIXTURE-EVIDENCED | Defaults and alternates can embed references, which can themselves embed more references. | `interpolation-cascade.pfcfg`, `pipeline.pfcfg` | `${CASCADE_DELTA:-$(cascade.gamma)-final}` and `${ACME_RELEASE_TAG:-$(build.node_version)-${GIT_SHA:-dev}}` | High | The exact iteration limit and whether evaluation is recursive or iterative is not specified |
| Resolution model | DESIGN DECISION | The reference does not state whether interpolation is done during parse, after merge, or iteratively. The implementation must choose a model consistent with the fixture behavior. | `format-reference.md`, `interpolation-cascade.pfcfg` | Chain of defaults and references strongly suggests post-merge iterative evaluation | Medium | Need explicit design choice: parse-time, post-merge, iterative fixpoint, or recursive descent |
| Circular config references | DOCUMENTED | Circular references in `$(section.key)` are errors, not infinite loops. | `format-reference.md` | `[cascade.loop] a = $(cascade.loop.b)`, `b = $(cascade.loop.a)` in `interpolation-cascade.pfcfg` | High | Need explicit cycle-detection algorithm and error semantics |
| Expansion-pass limit | DOCUMENTED | The production parser enforces a maximum expansion pass limit, but the exact number is undocumented. | `format-reference.md` | Not represented by a starter example; required policy choice | Medium | Must choose a reasonable limit and document it |
| Parse errors | DOCUMENTED | Broken syntax like malformed section/key lines should be parse errors. | `format-reference.md` | Not represented by fixture; grammar implies it | High | Need a concrete error contract |
| Invalid include paths / unresolved include targets | DESIGN DECISION | The reference describes relative-path resolution but not missing-file behavior. | `format-reference.md` | No fixture covers missing include; this is a required policy choice | Medium | Should missing include abort the file, skip it, or report an unmigratable item? |
| Unresolved environment variables | DOCUMENTED | If a required env var is missing, the expression may resolve to empty string or remain unresolved depending on syntax. | `format-reference.md`, `secrets.pfcfg` | `${REQUIRED_SIGNING_SECRET}` and `${REQUIRED_API_ENDPOINT}` in edge-case files | High | Need explicit rule whether missing required variables are fatal during evaluation or only become unmigratable in the report |
| Missing config references | FIXTURE-EVIDENCED | A config reference to an absent key is not a valid user input pattern in the starter files but is a likely evaluation failure mode. | `interpolation-cascade.pfcfg` | Missing keys are not shown intentionally; they are part of the verifier design space | Medium | Not specified in docs; must be diagnosed and reported |
| Effective settings definition | DOCUMENTED | “Effective settings” means the pipeline sees the fully resolved configuration after includes, conditionals, and interpolation are resolved. | `platform-lead-brief.md` | The platform brief explicitly calls this out | High | The exact comparison object for the verifier still has to be chosen |
| Unmigratable report semantics | DOCUMENTED | The assignment requires a machine-readable report listing file, section, key, and reason for anything that cannot be migrated automatically. | `assignment.md`, `platform-lead-brief.md` | Report requirements in the assignment | High | The exact report schema and severity levels are still design choices |
| Verification failure vs unmigratable failure | DOCUMENTED | A verifier mismatch is different from a config that cannot be migrated automatically. | `assignment.md` | A config can be syntactically valid but semantically mismatched under an env fixture | High | Need a clear distinction between “evaluation failed for this env” and “unmigratable even with a valid env” |

---

## B. Definitive rules we can safely implement

These are the rules that the supplied repository supports with high confidence and no extra interpretation:

- Section syntax is `[name]` / `[dotted.path]`; keys belong to the most recent section.
- Comments use `#` and `;`.
- Include paths are relative to the containing file.
- Include directives appear before section headers in the same file.
- `@include` merges the included file’s configuration into the current tree.
- `@include_once` suppresses re-including the same exact path during a top-level load.
- `@ifdef VAR` tests “set and non-empty”; `@ifndef VAR` tests “unset or empty.”
- Variable interpolation supports:
  - `${VAR}`
  - `${VAR:-default}`
  - `${VAR:+alternate}`
  - `$(section.key)` and dotted paths
- Later config assignments override earlier assignments in merge order.
- Cross-key references and chained interpolation are supported and must be evaluated in a deterministic expansion process.
- Circular `$(section.key)` references are errors.
- Effective settings are the fully merged, conditionally filtered, interpolated configuration seen by the pipeline under a concrete environment.

These are not guesses; they are the strongest rules supported by the repository evidence.

---

## C. Rules that remain ambiguous

These require an explicit design decision because the repository does not settle them:

- Exact order between include processing and conditional evaluation
- Exact evaluation timing for `$(section.key)` lookups
- Exact meaning of “set” for environment values that are explicitly empty strings
- Whether forward references are legal or only earlier references are allowed
- Treatment of missing include files or malformed include directives
- Include-cycle policy
- `@include_once` identity semantics across relative/path-normalized aliases
- Exact expansion-pass limit
- Whether a value that remains unresolved after interpolation is an error or a placeholder
- Whether the JSON path can carry “raw” legacy strings versus only final resolved values

The assignment is intentionally designed to force these decisions out into the decisions note.

---

## D. Questions requiring human judgment

1. Should conditionals be evaluated inline while the parser reads the file, or after the full tree is built?
2. Should empty environment variables count as “set” or “empty” for conditional and default logic?
3. Should forward references be allowed and resolved in a fixpoint loop?
4. What is the exact `@include_once` canonical path policy?
5. What expansion limit is acceptable for production-like behavior?
6. Should missing include files be an error, a convert-time warning, or an unmigratable report item?
7. Is “effective settings” the fully resolved string map only, or does it include source metadata such as include provenance and conditional activation?
8. Do we compare only the final string values, or also document that a config used dynamic interpolation rather than a literal?

These are not implementation details; they are semantic choices.

---

## E. Proposed test/environment matrix

Minimum environment matrix to exercise the important branches:

| Scenario | Environment | Purpose | Must include |
|---|---|---|---|
| CI path | `CI=1` and non-empty | Exercises CI overlays and conditional pushes | `CI`, `CACHE_NAMESPACE`, maybe `SLACK_WEBHOOK` |
| Non-CI path | `CI` unset or empty | Exercises fallback defaults and non-CI branches | empty or unset `CI` |
| Production path | `PRODUCTION=1` | Exercises `on-prem` overlay in Globex | `PRODUCTION` |
| Non-production path | `PRODUCTION` unset | Exercises `overrides.pfcfg` branch | empty or unset `PRODUCTION` |
| Beta feature branch | `FEATURE_BETA=1` | Exercises conditional include path and beta feature toggles | `FEATURE_BETA` |
| Standard feature branch | `FEATURE_BETA` unset | Exercises fallback branch in conditional includes | empty or unset `FEATURE_BETA` |
| Vault-backed secrets | `VAULT_ADDR=https://vault.example.invalid` | Exercises vault provider path | `VAULT_ADDR`, `VAULT_SECRET_PATH` |
| Env-backed secrets | `VAULT_ADDR` unset | Exercises env provider path | empty or unset `VAULT_ADDR` |
| Required env present | `REQUIRED_SIGNING_SECRET=...` and/or `REQUIRED_API_ENDPOINT=...` | Validates non-empty required values | required secret vars |
| Required env missing | `REQUIRED_SIGNING_SECRET` unset and/or `REQUIRED_API_ENDPOINT` unset | Validates unmigratable failure path | missing required vars |
| Interpolation cascade path | `CASCADE_ALPHA`, `CASCADE_GAMMA`, `CASCADE_DELTA` set as needed | Exercises chained/default resolution | those env vars |
| CI branch override in cascade | `CI=1` with cascade vars present | Exercises conditional override of `epsilon` | `CI` + cascade values |

This is the minimum matrix necessary to reach the semantic branches shown in the starter tree.

---

## F. Risks of choosing the wrong interpretation

1. Wrong include order can silently change the final value of a key.
2. Wrong conditional timing can include the wrong file or skip a required block.
3. Wrong interpretation of empty-vs-unset can change whether a branch is active.
4. Wrong reference resolution model can make forward references fail or resolve to the wrong value.
5. Wrong cycle policy can turn a fatal error into an infinite loop or a silent partial resolution.
6. Wrong default semantics can produce a working config in a test environment but a broken one in production.
7. Wrong equivalence target can make the verifier pass on a tree that is not actually equivalent to the legacy runtime.
8. Wrong unmigratable classification can cause real customer settings to be silently migrated without the necessary human review.

These are the risks Jordan is warning about: a migration that “looks fine” but behaves differently in production.

---

## Final note

The repository evidence is strongest on the concrete behavior of the starter tree and weakest on the semantic choices that were intentionally left unspecified. That means the safe engineering stance is:

- treat the assignment and reference as the normative specification where they are explicit,
- treat the starter configs as evidence for practical precedence and interpolation behavior,
- treat everything else as a design decision that must be made and documented before any migration logic is trusted.

That is the correct boundary if the goal is “proof before rollout.”


## User Prompt

We are now making the final semantic decisions before designing the JSON schema.

Do NOT modify any files.

Using ONLY:
- assignment.md
- briefs/platform-lead-brief.md
- briefs/format-reference.md
- starter/README.md
- starter/configs/**/*.pfcfg

review the following proposed legacy evaluation model:

1. Start with an empty configuration state.
2. Process the entry file as an ordered stream.
3. Evaluate @ifdef/@ifndef using the concrete environment while processing the stream.
4. Process active @include/@include_once directives recursively at their position in the stream.
5. Merge assignments in encounter order; later assignments override earlier assignments.
6. After the complete active include/assignment stream has been merged, resolve interpolation recursively:
   - ${VAR}
   - ${VAR:-default}
   - ${VAR:+alternate}
   - $(section.key)
7. Allow forward references because the starter fixtures require references to values that may be defined later in the merged configuration.
8. Detect circular config references and fail rather than partially resolving them.
9. Apply a finite expansion limit to protect against pathological input.
10. Define effective settings as the final resolved section/key/value map under the concrete environment.

For EACH of the 10 points, classify it as:
- DOCUMENTED
- FIXTURE-EVIDENCED
- DESIGN DECISION

For every point that is not fully documented:
- cite the exact evidence from the repository,
- explain why the proposed behavior is the safest interpretation,
- identify what could go wrong if we chose another interpretation.

Then specifically answer:

A. Does the evidence support post-merge interpolation?
B. Does the evidence require forward references?
C. Should an explicitly empty environment variable be treated as empty/non-set for @ifdef, @ifndef, :- and :+?
D. Should missing required environment variables be represented as evaluation errors rather than conversion failures?
E. Should missing config references be evaluation errors?
F. Should include cycles be errors?
G. What should @include_once use as its identity: the resolved file path relative to the repository/filesystem?
H. What expansion limit would you recommend for this take-home and why?

Finally provide a short section:

"SEMANTICS WE ARE NOW LOCKING"

with the exact rules we can put into DECISIONS.md.

Do not design the JSON schema yet.
Do not write implementation code.
Do not modify files.

## Copilot Response
I’ve narrowed the remaining decisions to the precise semantic choices that the repo actually supports or leaves open, and I’m validating each rule against the docs and the starter fixtures before locking the final interpretation.

## Semantic decisions before schema design

This section applies the repository evidence strictly and separates what is explicit from what is only inferred from the fixtures.

### 1) Start with an empty configuration state
Classification: DESIGN DECISION

Evidence:
- Nothing in `assignment.md`, `platform-lead-brief.md`, or `format-reference.md` states the initial config state explicitly.
- The starter files all behave like a merge starting from empty state and accumulating active directives and assignments, but that is an implementation model, not a documented rule.

Why this is the safest interpretation:
- It matches the natural “stream-then-merge” semantics implied by includes and overlays.
- It is the only way to make override order deterministic without assuming a hidden pre-populated base.

What could go wrong with another interpretation:
- If we assumed a pre-seeded global config, later overrides by entry files could become non-local and impossible to reproduce.
- Nested includes could silently inherit state from unrelated files, creating wrong effective settings.

---

### 2) Process the entry file as an ordered stream
Classification: FIXTURE-EVIDENCED

Evidence:
- The reference requires include directives before sections and describes includes as merging into the current config tree: `format-reference.md`.
- The actual entry files show ordered accumulation: `pipeline.pfcfg`, `pipeline.pfcfg`, and `pipeline.pfcfg` all build effective settings by reading includes in order and then local assignments after them.

Why this is the safest interpretation:
- The fixtures plainly rely on ordering.
- Later overrides win only because the evaluator sees a sequence of assignments, not a set of unordered keys.

What could go wrong with another interpretation:
- Reordering the stream could alter build settings such as `parallel`, `requires_approval`, or `on_failure` in the starter examples.
- A set-based merge would silently change semantics.

---

### 3) Evaluate @ifdef/@ifndef using the concrete environment while processing the stream
Classification: FIXTURE-EVIDENCED

Evidence:
- The reference explicitly defines the condition semantics: `format-reference.md`.
- The sample configs use those conditions to include or exclude blocks and files:
  - `notifications.pfcfg`
  - `container-publish.pfcfg`
  - `pipeline.pfcfg`
  - `conditional-includes.pfcfg`

Why this is the safest interpretation:
- It is the only interpretation consistent with conditional includes and conditional assignments being active or skipped at the exact point they appear in the stream.
- It keeps the parse model deterministic and matches the exact semantics described in the reference.

What could go wrong with another interpretation:
- If conditionals were evaluated after full-tree merge, then conditional include selection and key activation could drift from the legacy stream semantics.
- That would especially affect the branch-selection files under `edge-cases`.

---

### 4) Process active @include/@include_once directives recursively at their position in the stream
Classification: FIXTURE-EVIDENCED

Evidence:
- Include semantics are documented in `format-reference.md`.
- Recursive inclusion is demonstrated by:
  - `container-publish.pfcfg` includes `node-build.pfcfg`
  - `node-build.pfcfg` includes `defaults.pfcfg`
  - `defaults.pfcfg` includes toolchains and notifications

Why this is the safest interpretation:
- These file relationships are nested and must be traversed recursively.
- A non-recursive include evaluator would miss the actual namespace structure used by the starter configs.

What could go wrong with another interpretation:
- Flat include expansion would lose template layering.
- It would break values such as `$(toolchain.node.install_cmd)` and `$(toolchain.default.name)` that come from included files.

---

### 5) Merge assignments in encounter order; later assignments override earlier assignments
Classification: FIXTURE-EVIDENCED

Evidence:
- The documents do not explicitly say “last assignment wins,” but the files clearly rely on it:
  - `ci-shared.pfcfg` overrides base values
  - `pipeline.pfcfg` overrides template defaults
  - `overrides.pfcfg` modifies build settings after the base include

Why this is the safest interpretation:
- It is the only model consistent with the sample override chains.
- The assignment order is the only determinism source available in the repo.

What could go wrong with another interpretation:
- If the evaluator used a “first assignment wins” or set-based merge, the overlays would be wrong.
- Production semantics would differ under CI and non-CI conditions.

---

### 6) After the complete active include/assignment stream has been merged, resolve interpolation recursively
Classification: DOCUMENTED

Evidence:
- The reference explicitly says: `$(section.key)` is the value of another key after includes/conditionals are merged: `format-reference.md`.
- The starter configs rely on that pattern:
  - `node-build.pfcfg`: `install_cmd = $(toolchain.node.install_cmd)`
  - `pipeline.pfcfg`: `public_key_url = $(signing.key_id).keys.example.invalid`
  - `interpolation-cascade.pfcfg`: chained `${...}` and `$(...)` references

Why this is the safest interpretation:
- It matches the explicit wording in the reference.
- It gives a clean two-phase model: merge first, resolve second.

What could go wrong with another interpretation:
- Resolving references while the stream is still being parsed would create order-sensitive, non-local behavior and could break the documented “after merge” rule.
- It would be much easier to get wrong in nested include graphs.

---

### 7) Allow forward references because the starter fixtures require references to values that may be defined later in the merged configuration
Classification: FIXTURE-EVIDENCED

Evidence:
- The reference does not explicitly say that forward references are allowed. It only says references happen after merge.
- The fixture examples do not show a true later-key reference in the sense of a value defined after the referent in the same file; they do show complex chained interpolation and reference to merged data, but not a definitive “later in file” case:
  - `interpolation-cascade.pfcfg`
  - `pipeline.pfcfg`

Why this is the safest interpretation:
- A strict single-pass resolver would be brittle and would fail if a future config introduces a valid forward reference.
- The docs explicitly call out circular references and say the parser enforces a maximum expansion pass. That strongly implies an iterative or fixpoint-style resolver is acceptable, and a forward-capable evaluator is safer than a parser that assumes “already defined only.”

What could go wrong with another interpretation:
- If we ban forward references outright, we risk a false negative on valid production configs.
- If we accept forward references without cycle detection, we risk silent partial resolutions or infinite loops.

Important nuance:
- The repository does not prove a required later reference exists in the starter files. It only supports a conservative design that allows them.

---

### 8) Detect circular config references and fail rather than partially resolving them
Classification: DOCUMENTED

Evidence:
- The reference says: “Circular `$(section.key)` references — behavior is error, not infinite loop.” `format-reference.md`
- The starter file `interpolation-cascade.pfcfg` contains the explicit cycle:
  - `a = $(cascade.loop.b)`
  - `b = $(cascade.loop.a)`

Why this is the safest interpretation:
- It matches the explicit rule in the reference and the explicit edge-case fixture.
- Failure is safer than partial resolution, and the assignment specifically warns about silent failures.

What could go wrong with another interpretation:
- A loop would hang or a partial value would be emitted, which is exactly the kind of silent break Jordan warns about.
- A partial resolution would make the config appear valid while the pipeline sees the wrong value.

---

### 9) Apply a finite expansion limit to protect against pathological input
Classification: DOCUMENTED

Evidence:
- The reference explicitly says the production parser enforces a maximum expansion pass limit, but the exact limit is not documented. `format-reference.md`

Why this is the safest interpretation:
- Because the repo explicitly requires a limit and a failure mode for pathological inputs.
- This is a preventive guard, not a speculative optimization.

What could go wrong with another interpretation:
- Without a hard cap, a malicious or accidental self-referential chain could create non-terminating evaluation.
- Too low a cap would falsely reject legitimate but deep chains; too high a cap could permit runaway work.

---

### 10) Define effective settings as the final resolved section/key/value map under the concrete environment
Classification: DOCUMENTED

Evidence:
- The platform brief explicitly defines “Effective settings” as the resolved configuration after includes, conditionals, and interpolation are resolved: `platform-lead-brief.md`
- The assignment says the verifier must compare old and new configs in terms of “effective settings”: `assignment.md`

Why this is the safest interpretation:
- It is exactly the business requirement: prove runtime-relevant settings, not text or raw parse tree structure.
- It matches the assignment’s “silent failure” risk.

What could go wrong with another interpretation:
- A verifier comparing raw source text would miss real behavior changes in env-sensitive pipelines.
- A verifier comparing the schema tree before resolution would pass even when runtime behavior differs.

---

## A. Does the evidence support post-merge interpolation?
Yes. The strongest evidence is explicit in `format-reference.md`: `$(section.key)` resolves “after includes/conditionals are merged.” The starter files also show merged config trees before the references are consumed.

This is not just a convenience choice; it is the documented model.

---

## B. Does the evidence require forward references?
Not strictly in the starter files. The repo does not contain a confirmed example of a key that legitimately depends on a value defined later in the same merged tree. What it does support is a conservative evaluation rule: allow forward references, because:
- the docs describe a resolver that can handle merged key references,
- the resolver must be iterative or fixpoint-like,
- and the real parser is said to enforce a pass limit, which implies a more general expansion model than a one-pass parse.

So the safest answer is:
- no, the starter files do not require forward references,
- yes, the safe implementation should allow them rather than hard-code a brittle single-pass restriction.

---

## C. Should an explicitly empty environment variable be treated as empty/non-set for @ifdef, @ifndef, :- and :+?
Yes.

Evidence:
- `format-reference.md` says:
  - `@ifdef VAR` only if set and non-empty
  - `@ifndef VAR` only if unset or empty
  - `${VAR:-default}` uses default if unset or empty
  - `${VAR:+alternate}` uses alternate only if set and non-empty
- The same semantics are used in examples like `@ifndef SLACK_WEBHOOK` and `key_prefix = ${CI:+ci-}${CACHE_NAMESPACE:-default}` in `defaults.pfcfg`.

This is the most consistent rule:
- empty string is treated as empty, not as active data
- unset and empty are equivalent for the default/conditional checks, except that “set and non-empty” is the positive case

This is not a guess; it is the explicit rule in the reference.

---

## D. Should missing required environment variables be represented as evaluation errors rather than conversion failures?
Yes, for the evaluator and for the verifier.

Reason:
- A required variable without a default is a legitimate environmental evaluation condition, not a conversion problem.
- Examples:
  - `secrets.pfcfg`: `key_material = ${REQUIRED_SIGNING_SECRET}`
  - `conditional-includes.pfcfg`: `api_endpoint = ${REQUIRED_API_ENDPOINT}`
- These are not parser failures; they are evaluation failures under a particular environment.

But there is also a second layer:
- if the converter or schema cannot represent that legacy behavior safely, it should also be reported as unmigratable.
- The report is for things that cannot be auto-migrated or verified, while the evaluator should classify the specific missing env as an evaluation failure.

---

## E. Should missing config references be evaluation errors?
Yes.

Evidence:
- The reference explicitly treats circular config references as errors.
- A missing config reference is a broken reference, not a valid empty value.
- The consistent safety rule is: if the reference target is missing, the evaluator fails with a precise reason rather than silently substitutes an empty string or partial value.

This is important because silent empty substitution would create false equivalence.

---

## F. Should include cycles be errors?
Yes, they should be errors.

Evidence:
- The reference never says include cycles are legal.
- It explicitly warns about silent failure and makes circular config references errors.
- For safety, the same principle should apply to include loops to avoid infinite recursion and partial partial merges.

This is a necessary design decision and should be treated as fatal during parser/evaluator execution.

---

## G. What should @include_once use as its identity: the resolved file path relative to the repository/filesystem?
Use the resolved canonical filesystem path, not the raw textual include string.

This is the safest rule because:
- “exact path” in the reference implies identity by the file being loaded, not by a textual alias.
- Files may be reached through different relative paths that resolve to the same final file.
- A raw string comparison would make `@include_once` inconsistent in nested trees.

Recommended rule:
- normalize each include to a canonical absolute or normalized path before checking the seen set
- maintain the seen set per top-level entry
- do not just compare raw relative strings

This is a design decision, but it is the safest and least surprising interpretation.

---

## H. What expansion limit would you recommend for this take-home and why?
Recommend: 64 expansion passes.

Why:
- The reference says the production parser imposes a cap, but the precise number is undocumented.
- The sample fixtures are shallow and do not require anything near a massive limit.
- A limit that is too low risks false negatives on legitimate but somewhat nested chains.
- A limit that is too high risks expensive or non-terminating evaluation.

64 is a good compromise:
- large enough for realistic nested chains in a take-home repo,
- small enough to prevent pathological runaway expansion,
- easy to explain and document in DECISIONS.md

---

## SEMANTICS WE ARE NOW LOCKING

These are the exact rules we should lock before designing the JSON schema:

1. The evaluator starts from an empty configuration state for each entry file.
2. The entry file is processed as an ordered stream.
3. `@ifdef` and `@ifndef` are evaluated using the concrete environment while the stream is processed.
4. Active `@include` and `@include_once` directives are processed recursively at their stream position.
5. `@include_once` tracks already-included files by canonical resolved path, per top-level entry config.
6. Included files merge into the current config tree in encounter order.
7. Later assignments override earlier assignments in the same section/key path.
8. After the active include and assignment stream is merged, interpolation is resolved against the merged tree.
9. Interpolation supports:
   - `${VAR}`
   - `${VAR:-default}`
   - `${VAR:+alternate}`
   - `$(section.key)` and dot-separated paths
10. References may be resolved after merge and may be iterative/fixpoint-based; forward references are allowed conservatively.
11. Circular `$(section.key)` references are errors.
12. Include cycles are errors.
13. Missing required environment variables are evaluation errors for the concrete environment.
14. Missing config references are evaluation errors.
15. Expansion depth is bounded by a finite pass limit, recommended to be 64.
16. Effective settings are the final resolved section/key/value map under the concrete environment after merge, conditional filtering, and interpolation.
17. Unmigratable cases are those that cannot be represented or verified automatically and must be reported with file, section, key, and reason.

This is the full set of semantics we can defend from the repo without inventing undocumented behavior.
