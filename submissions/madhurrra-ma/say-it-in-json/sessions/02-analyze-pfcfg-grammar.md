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
