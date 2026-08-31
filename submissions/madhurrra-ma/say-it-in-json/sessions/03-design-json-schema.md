## User Prompt

We have completed the legacy .pfcfg semantic analysis.

Do NOT modify files and do NOT implement code yet.

Use the following locked semantic model:

1. Each entry config is evaluated from an empty state.
2. Files are processed as an ordered stream.
3. @ifdef and @ifndef are evaluated against the concrete environment while processing the stream.
4. Active @include and @include_once directives are recursively processed at their position in the stream.
5. Includes are resolved relative to the including file.
6. @include_once uses normalized resolved file identity and is tracked per top-level evaluation.
7. Assignments merge in encounter order; later values override earlier values.
8. After the complete active stream is merged, interpolation is resolved against the merged configuration.
9. Supported interpolation:
   - ${VAR}
   - ${VAR:-default}
   - ${VAR:+alternate}
   - $(section.key)
10. Cross-key references may be chained and may refer to values available in the merged tree.
11. Circular references are errors.
12. Include cycles are errors.
13. Missing required environment variables are evaluation errors.
14. Missing config references are evaluation errors.
15. Expansion is bounded by a finite safety limit.
16. Effective settings are the final resolved section/key/value map under a concrete environment.
17. The converter and JSON representation must preserve semantics; it must NOT merely emit one environment-specific resolved configuration.

Now design the target JSON format.

The goal is a small, explicit, defensible schema for this take-home assignment — NOT a production configuration platform.

Explore at least three possible schema designs.

For each design explain:

- How ordinary values are represented
- How includes are represented
- How conditional blocks are represented
- How environment variables are represented
- How ${VAR:-default} is represented
- How ${VAR:+alternate} is represented
- How $(section.key) references are represented
- How nested/chained expressions are represented
- How errors/unmigratable constructs can be represented
- How ordering and override semantics are preserved
- How the JSON evaluator would execute it
- Advantages
- Disadvantages
- How easy it is to validate with JSON Schema
- How likely it is to accidentally create false equivalence

Consider at least these architectural options:

A. A resolved/static JSON document
B. A structured semantic/AST-like JSON representation
C. A hybrid representation containing normal values plus explicit expression/directive objects

Do not choose a design merely because it is easiest to implement.

The primary optimization criterion is semantic safety:
a wrong migration must be detectable rather than silently producing different effective settings.

Then recommend ONE design.

For the recommended design, provide:

1. A concise conceptual model
2. Example JSON for:
   - normal configuration
   - include
   - include_once
   - ifdef
   - ifndef
   - environment variable
   - default expression
   - alternate expression
   - cross-key reference
   - chained references
3. Exact ordering/override semantics
4. Evaluation algorithm
5. Error model
6. JSON Schema structure
7. Migration rules from each legacy construct
8. Which legacy constructs should be rejected as unmigratable
9. How the design supports equivalence verification
10. Example of a deliberate converter bug and how the verifier would catch it

Be especially critical about whether representing directives structurally is better than encoding them as strings.

Do not implement anything.
Do not create files.
Do not modify the repository.

## Copilot Response

I’ve settled the locked semantics and am now evaluating the schema choices against the actual risk profile: whether the format preserves the legacy evaluation behavior or just a prettified final state.

## Design goal

The schema must preserve semantics, not just look nice. The repo is explicit that the danger is not “syntax converted correctly,” but “semantics silently changed,” which is called out in `platform-lead-brief.md` and restated in `assignment.md`. That means a resolved-only JSON document is not enough, because it discards the rules that made the config behave correctly.

---

## 1) Three schema designs

### Option A — Resolved/static JSON document
This is a snapshot of the final effective settings after evaluation.

#### How ordinary values are represented
- Simple key/value object
- Example:
  - `{"build":{"parallel":true,"timeout_minutes":90}}`

#### How includes are represented
- Usually discarded or converted into a flat resolved map
- No include provenance remains

#### How conditional blocks are represented
- Only the final active state survives
- Hidden branch information is lost

#### How environment variables are represented
- Resolved values are already substituted
- No record of which value came from `${VAR}`, `${VAR:-default}`, etc.

#### How `${VAR:-default}` is represented
- As final string value only
- No preserved expression metadata

#### How `${VAR:+alternate}` is represented
- As final string value only

#### How `$(section.key)` references are represented
- Resolved to plain strings
- Reference origin is lost

#### How nested/chained expressions are represented
- Flattened into final strings

#### How errors/unmigratable constructs can be represented
- A separate diagnostics list can exist, but the data itself no longer has the original semantics

#### How ordering and override semantics are preserved
- Not preserved beyond the final merged value
- The evaluator can no longer tell which rule won or why

#### How the JSON evaluator would execute it
- It would read the already-resolved output and validate the final map
- It does not reconstruct legacy semantics

#### Advantages
- Small and easy to read
- Very easy for a UI/editor
- Easy to validate with JSON Schema

#### Disadvantages
- Unsafe for migration proof
- Discards the representational semantics that are required to reason about equivalence
- Encourages false equivalence if the converter “just resolves once” under one environment

#### JSON Schema validation ease
- Very easy

#### Risk of accidental false equivalence
- High

This design is attractive but not safe enough for the assignment. It is only valid if the system is designed to treat the JSON as a post-evaluation artifact, not as a faithful representation of legacy configuration semantics.

---

### Option B — Full semantic/AST-like JSON
This preserves the configuration as a trace of semantic operations.

#### How ordinary values are represented
- Each assignment is a semantic node with section, key, source, and value expression
- Example:
  - `{ "type":"assignment","section":"build","key":"parallel","value":{"type":"literal","value":"true"}}`

#### How includes are represented
- Explicit nodes:
  - `{ "type":"include","path":"../../templates/container-publish.pfcfg"}`
  - `{ "type":"include_once","path":"../../_base/defaults.pfcfg"}`
- Maintains order and provenance

#### How conditional blocks are represented
- Nodes for `ifdef` and `ifndef` contain:
  - condition
  - body
  - source location
- Example:
  - `{ "type":"ifdef","var":"CI","body":[ ... ] }`

#### How environment variables are represented
- Explicit expression nodes:
  - `{ "type":"env","name":"CI" }`
  - `{ "type":"env","name":"CACHE_NAMESPACE","default":"default" }`

#### How `${VAR:-default}` is represented
- Node:
  - `{ "type":"env_default","name":"CACHE_NAMESPACE","default":"default" }`

#### How `${VAR:+alternate}` is represented
- Node:
  - `{ "type":"env_alternate","name":"CI","alternate":"ci-" }`

#### How `$(section.key)` references are represented
- Node:
  - `{ "type":"ref","path":["toolchain","node","install_cmd"] }`

#### How nested/chained expressions are represented
- Expression trees:
  - `{ "type":"concat", "parts":[{"type":"env_alternate",...},{"type":"ref",...}] }`
- This handles nested interpolations cleanly

#### How errors/unmigratable constructs can be represented
- Diagnostics list:
  - `{ "severity":"error","code":"MISSING_ENV","file":"...","section":"signing","key":"key_material" }`
- The raw semantically meaningful nodes remain available

#### How ordering and override semantics are preserved
- `statements` array preserves encounter order
- A later assignment is just a later node
- The evaluator replays in order

#### How the JSON evaluator would execute it
- Parse the semantic tree
- Reconstruct the ordered stream
- Apply include/conditional logic
- Merge assignments in order
- Resolve interpolation recursively/fixpoint
- Detect cycles and missing values

#### Advantages
- Maximum semantic fidelity
- Most robust against false equivalence
- Best for proving equivalence
- Makes gaps and unmigratable cases explicit

#### Disadvantages
- Verbose
- Harder to read
- Harder to validate with a simple JSON Schema
- Easy to over-engineer for a small take-home

#### JSON Schema validation ease
- Moderate to hard

#### Risk of accidental false equivalence
- Low

This is semantically safest, but it is also the most work and the most likely to be “too formal” for this assignment unless the goal is explicit proof.

---

### Option C — Hybrid representation: ordinary values + explicit expression/directive objects
This keeps the document mostly human-readable while preserving semantic intent.

#### How ordinary values are represented
- Normal “final-looking” keys and sections are stored as ordinary JSON
- Example:
  - `"build": { "parallel": "true", "timeout_minutes": "90" }`

#### How includes are represented
- A parallel metadata field or statement list:
  - `"includes":[{"kind":"include","path":"../../templates/container-publish.pfcfg"}]`
  - `"includes_once":[{"kind":"include_once","path":"../../_base/defaults.pfcfg"}]`

#### How conditional blocks are represented
- A separate block list or conditional wrapper objects:
  - `"conditionals":[{"when":{"op":"ifdef","var":"CI"},"body":{...}}]`

#### How environment variables are represented
- Values may be plain strings or expression objects
- Example:
  - `"image":{"kind":"env_default","name":"PF_BUILD_IMAGE","default":"pfci/builder:22.04"}`

#### How `${VAR:-default}` is represented
- Expression object:
  - `{ "kind":"env_default","name":"CACHE_NAMESPACE","default":"default" }`

#### How `${VAR:+alternate}` is represented
- Expression object:
  - `{ "kind":"env_alternate","name":"CI","alternate":"ci-" }`

#### How `$(section.key)` references are represented
- Expression object:
  - `{ "kind":"ref","path":["toolchain","node","install_cmd"] }`

#### How nested/chained expressions are represented
- Expression objects nest:
  - `{ "kind":"concat","parts":[{"kind":"env_alternate","name":"CI","alternate":"ci-"},{"kind":"ref","path":["cache","key_prefix"]}] }`
- Or a textual expression field plus metadata:
  - `"value":"${CI:+ci-}${CACHE_NAMESPACE:-default}"`

#### How errors/unmigratable constructs can be represented
- `diagnostics` array or an `unmigratable` list
- Ex:
  - `{ "kind":"missing_env","section":"signing","key":"key_material","var":"REQUIRED_SIGNING_SECRET" }`

#### How ordering and override semantics are preserved
- Primary representation contains a `statements` or `events` list preserving order
- The map is the convenient view, but the event log is the authoritative one

#### How the JSON evaluator would execute it
- Replay the ordered statements
- Evaluate `ifdef`/`ifndef` conditions inline
- Resolve includes in order
- Merge assignments
- Resolve expression objects against the merged map
- Fail on cycles or missing values

#### Advantages
- Readable and explicit
- Preserves semantics without being too verbose
- Good balance between proof and usability
- Easy to reason about in tests

#### Disadvantages
- Requires discipline: the JSON must not drift into “resolved-only” representation accidentally
- More design work than a fully resolved document
- Can still be done wrong if the converter strips semantics

#### JSON Schema validation ease
- Moderate

#### Risk of accidental false equivalence
- Low to moderate, if the schema is disciplined

This is the best fit for the assignment: it is explicit enough to preserve semantics, but not so abstract that it becomes a custom programming language.

---

## Recommendation: Option C — hybrid representation

This is the best choice for the assignment because the repo is not asking for a general config format; it is asking for a migration that can be proven equivalent.

### Why not Option A?
Because a static final map is too weak. It loses the legacy semantics and invites false equivalence.

### Why not Option B?
Because it is correct but too heavy for a thin take-home and harder to review by a human. It is more of a formal semantic model than a practical target representation.

### Why Option C?
Because the assignment explicitly requires:
- a target JSON format,
- a converter,
- a verifier,
- and a report for unmigratable cases.

A hybrid format is the practical compromise:
- it stores the ordinary resolved-looking structure for most humans,
- it keeps explicit expression and directive metadata to prove semantics,
- and it preserves enough ordering/provenance to detect silent drift.

The key principle is: do not allow the JSON representation to become a “declarative final state only” without provenance. Structural directives must remain explicit.

---

## Recommended design: conceptual model

The model is:

- A JSON document that contains:
  1. a `statements` or `events` list preserving stream order,
  2. a `sections` view for ordinary config reading,
  3. a `diagnostics` list for errors/unmigratable constructs,
  4. expression objects for environment and cross-key references.

This preserves both readability and semantics.

### Core idea
- Normal config is readable as a plain object.
- Expressions and directives are not stringified away.
- The evaluator replays the ordered stream before comparing effective settings.

That keeps the representation honest.

---

## 2) Example JSON for the recommended design

Below are conceptual examples, not a final exact schema. They show the semantics we want to preserve.

### Normal configuration
```json
{
  "format": "pf-json-v1",
  "statements": [
    {
      "kind": "assignment",
      "section": "build",
      "key": "parallel",
      "value": { "kind": "literal", "value": "true" }
    },
    {
      "kind": "assignment",
      "section": "build",
      "key": "timeout_minutes",
      "value": { "kind": "literal", "value": "90" }
    }
  ],
  "sections": {
    "build": {
      "parallel": { "kind": "literal", "value": "true" },
      "timeout_minutes": { "kind": "literal", "value": "90" }
    }
  }
}
```

### Include
```json
{
  "kind": "include",
  "path": "../../templates/container-publish.pfcfg"
}
```

### Include_once
```json
{
  "kind": "include_once",
  "path": "../../_base/defaults.pfcfg"
}
```

### Ifdef
```json
{
  "kind": "ifdef",
  "var": "CI",
  "body": [
    {
      "kind": "assignment",
      "section": "build",
      "key": "parallel",
      "value": { "kind": "literal", "value": "true" }
    }
  ]
}
```

### Ifndef
```json
{
  "kind": "ifndef",
  "var": "SLACK_WEBHOOK",
  "body": [
    {
      "kind": "assignment",
      "section": "notify",
      "key": "on_failure",
      "value": { "kind": "literal", "value": "email" }
    }
  ]
}
```

### Environment variable
```json
{
  "kind": "env",
  "name": "CI"
}
```

### Default expression
```json
{
  "kind": "env_default",
  "name": "CACHE_NAMESPACE",
  "default": "default"
}
```

### Alternate expression
```json
{
  "kind": "env_alternate",
  "name": "CI",
  "alternate": "ci-"
}
```

### Cross-key reference
```json
{
  "kind": "ref",
  "path": ["toolchain","node","install_cmd"]
}
```

### Chained references
```json
{
  "kind": "concat",
  "parts": [
    { "kind": "env_alternate", "name": "CI", "alternate": "ci-" },
    { "kind": "env_default", "name": "CACHE_NAMESPACE", "default": "default" }
  ]
}
```

And for a cross-key + env default combo:
```json
{
  "kind": "concat",
  "parts": [
    { "kind": "env_default", "name": "ACME_RELEASE_TAG", "default": { "kind": "ref", "path": ["build","node_version"] } },
    { "kind": "literal", "value": "-" },
    { "kind": "env_default", "name": "GIT_SHA", "default": "dev" }
  ]
}
```

---

## 3) Exact ordering/override semantics

This is the single most important rule.

### Semantics
- The document preserves a chronological `statements` list.
- Each statement is processed in order.
- Includes are executed in place.
- Conditional blocks are evaluated when encountered.
- Assignments are merged in order.
- Later assignments override earlier ones.

This matches the locked semantics we established earlier and the actual behavior in:
- `pipeline.pfcfg`
- `ci-shared.pfcfg`
- `pipeline.pfcfg`

### Why this matters
A converter that just emits the final flat map without preserving `statements` loses the ability to prove that later overrides were truly later in the stream. That is exactly the kind of silent semantic drift Jordan warns about in `platform-lead-brief.md`.

---

## 4) Evaluation algorithm

The JSON evaluator should be defined as a semantic replay of the same logical steps as the legacy evaluator.

### Algorithm
1. Initialize empty config state.
2. Walk the `statements` array in order.
3. For each statement:
   - if `include`: resolve path relative to the current file and recurse
   - if `include_once`: skip if identity already seen in this top-level evaluation
   - if `ifdef`: evaluate env condition; if true, process body
   - if `ifndef`: evaluate env condition; if true, process body
   - if `assignment`: merge into current section/key map
4. After the active stream is merged, evaluate expression objects:
   - env vars
   - default/alternate operators
   - refs to section keys
   - nested concat chains
5. Detect:
   - circular refs
   - missing env vars
   - missing config refs
   - expansion limit exceeded
6. Emit the final effective settings map.

This mirrors the locked legacy semantics and preserves proofability.

---

## 5) Error model

The JSON representation should include an explicit diagnostics model.

### Error categories
- `parse_error`
- `include_error`
- `missing_env`
- `missing_ref`
- `circular_ref`
- `expansion_limit`
- `unmigratable`

### Example
```json
{
  "diagnostics": [
    {
      "severity": "error",
      "code": "missing_env",
      "file": "customers/initech/secrets.pfcfg",
      "section": "signing",
      "key": "key_material",
      "var": "REQUIRED_SIGNING_SECRET"
    }
  ]
}
```

### Why this is necessary
A target schema that only contains successful values is not enough. The assignment requires a report for things that cannot be migrated and for evaluation failures. This is the place to put that information.

---

## 6) JSON Schema structure

Conceptually, the schema should have these top-level fields:

```json
{
  "format": "pf-json-v1",
  "entry": "string",
  "statements": [ "statement objects" ],
  "sections": { "sectionName": { "keyName": "value expression or literal" } },
  "diagnostics": [ "diagnostic objects" ],
  "unmigratable": [ "report entries" ]
}
```

### Statement object types
- `assignment`
- `include`
- `include_once`
- `ifdef`
- `ifndef`

### Value expression types
- `literal`
- `env`
- `env_default`
- `env_alternate`
- `ref`
- `concat`
- `list`

### Why structurally explicit directives are better than strings
A directive encoded as a string such as:
```json
"raw": "@ifdef CI\n[build]\nparallel = true\n@endif"
```
is too lossy. The conversion is no longer semantic; it is only text. That makes it much easier to accidentally create false equivalence. Structural representation preserves:
- whether it was included
- whether it was conditional
- whether it was nested
- what variables drove the condition
- which order the statements were processed

This is safer than raw text.

---

## 7) Migration rules from each legacy construct

### Legacy rule → JSON representation
- Section + key assignment → `assignment`
- Include → `include`
- Include once → `include_once`
- `@ifdef VAR` → `ifdef` with `var`
- `@ifndef VAR` → `ifndef` with `var`
- `${VAR}` → `env`
- `${VAR:-default}` → `env_default`
- `${VAR:+alternate}` → `env_alternate`
- `$(section.key)` → `ref`
- chained/reference nested interpolation → `concat` with nested expression objects
- repeated override by later assignment → same `key` with later `statement`; final effective value is determined by replay order

This is a direct mapping and is safer than trying to flatten everything to a final final map.

---

## 8) Legacy constructs that should be rejected as unmigratable

These should not be silently guessed:

- missing required env values with no default
  - e.g. `secrets.pfcfg`
- circular config references
  - e.g. `interpolation-cascade.pfcfg`
- include cycles
- malformed conditional or include directives
- unsupported syntax that the target schema cannot represent without inventing new semantics
- any config whose effective behavior depends on a legacy evaluation rule the JSON representation cannot preserve explicitly

These should be recorded in `unmigratable` or `diagnostics` with file, section, key, and reason.

---

## 9) How the design supports equivalence verification

This design directly supports verification because the verifier can do the following:

1. Evaluate the legacy entry file under the chosen environment using the locked semantics.
2. Evaluate the JSON representation under the same environment.
3. Compare the final resolved maps.
4. Also compare the semantic statements trace if needed.
5. Emit a pass/fail result plus detailed diagnostics.

This is much stronger than comparing textual output or final static values because it proves the semantics, not just the appearance.

The important safety property is:
- the JSON preserves enough meaning to replay the same conditions and expressions
- the verifier does not have to infer from a flat snapshot

---

## 10) Example of a deliberate converter bug and how the verifier would catch it

### Bug
A converter incorrectly reorders the two assignments:

Legacy:
- `@include default.pfcfg`
- `build.parallel = false`
- `@ifdef CI`
- `build.parallel = true`
- `@endif`

The naive converter emits:
- `build.parallel = true` in the static JSON because it “merges after all conditions,” ignoring the actual stream order.

### Why this is a bug
The real legacy behavior depends on the stream order and environment condition. The final map is not the same if the condition is evaluated in the wrong place.

### How the verifier catches it
- The legacy evaluator computes one effective map under the concrete environment.
- The JSON evaluator replays the statement list in the JSON document.
- The final map differs.
- The verifier reports mismatch specifically at `build.parallel`, with enough detail to show the sequence ordering issue.

This is exactly the kind of failure the assignment wants to detect before production.

---

## Final recommendation

The safest representation for this assignment is:

- hybrid JSON with:
  - a chronological `statements` log,
  - ordinary section/key map for readability,
  - explicit expression objects for env/default/alternate/ref/concat nodes,
  - a diagnostics/unmigratable list.

This is the strongest choice because it preserves semantics without becoming a custom programming language. It is the best way to guard against silent false equivalence.

> The critical design rule is: never allow a converter to turn directives and expressions into a plain already-resolved object unless the semantics are preserved elsewhere in the document. Structural directives are much safer than strings.

If you want, I can turn this into a final “schema design decision memo” format next, without writing any implementation code.


## User Prompt

We need to refine the proposed JSON schema before implementation.

Do NOT modify files.
Do NOT write implementation code.

We identified two architectural concerns in the previous schema proposal:

CONCERN 1:
The proposal contained both:
- statements[]
- sections{}

These can become two conflicting sources of truth.

CONCERN 2:
The proposal represented includes using paths such as:
../../templates/container-publish.pfcfg

But the target format is JSON. A migrated configuration should ideally not remain dependent on legacy .pfcfg files.

Analyze these issues rigorously.

Part 1 — Single source of truth

Compare:

A. statements[] as the only authoritative representation
B. sections{} as the only authoritative representation
C. statements[] authoritative + sections{} as a derived/read-only view
D. both independently authoritative

For each:
- semantic safety
- ordering preservation
- override preservation
- conditional preservation
- include preservation
- verifier complexity
- risk of inconsistent representations

Recommend one.

Part 2 — Include representation

Compare:

A. Converted JSON includes converted JSON files
B. JSON continues referencing legacy .pfcfg files
C. Fully inline included content into the entry JSON
D. Store include references plus embedded converted modules

Consider:
- preservation of include order
- @include_once semantics
- relative paths
- include cycles
- reuse of shared configs
- migration completeness
- ability to remove the legacy format after migration
- verifier design

Recommend one.

Part 3 — Output structure

Compare:

A. One JSON file for every .pfcfg file
B. One self-contained JSON file per entry-point config
C. Both module JSON files and entry-point JSON files

Consider the starter repository structure:
- customers/
- edge-cases/
- environments/
- templates/
- _base/

Do not assume that every .pfcfg is an independent customer entry point.

Part 4 — Define the final architecture

Provide an exact conceptual model for:

1. What one generated JSON file represents
2. How an include is represented
3. How conditionals are represented
4. How assignments are represented
5. How expressions are represented
6. What is authoritative
7. How the JSON evaluator resolves includes
8. How @include_once semantics are reproduced
9. How the converter handles the entire reachable include graph
10. How the verifier chooses the entry point

Part 5 — False-equivalence attack

Construct at least 5 examples where a superficially reasonable JSON schema would silently change legacy behavior.

Examples should cover:
- include order
- include_once
- conditional include
- later override
- interpolation/reference resolution

For each, explain how the recommended architecture prevents or detects the bug.

Part 6 — Final recommendation

End with:

LOCKED JSON ARCHITECTURE

containing the exact rules we should use in the implementation.

Do not design Python classes or code structure yet.
Do not create files.
Do not modify the repository.

## Copilot Response

I’m tightening the schema decision around the two real failure modes: conflicting truth sources and legacy file dependencies. The goal is to lock the architecture so the verifier can prove semantic equivalence instead of just comparing a pretty JSON snapshot.

## Part 1 — Single source of truth

The key problem is not whether both representations can exist; it is whether both can be treated as authoritative. In a migration that must prove semantic equivalence, the answer should be no.

### A. statements[] as the only authoritative representation
- Semantic safety: High
- Ordering preservation: High
- Override preservation: High
- Conditional preservation: High
- Include preservation: High
- Verifier complexity: Medium
- Risk of inconsistent representations: Low

Why it is strong:
- The legacy semantics are fundamentally stream-based, as shown in `format-reference.md` and in the starter examples under `configs`, especially `pipeline.pfcfg`, `pipeline.pfcfg`, and `conditional-includes.pfcfg`.
- A statement log preserves exact encounter order and therefore the override behavior.

Weakness:
- It is not ergonomic for humans.
- A plain object view must be derived, not used as the actual source of truth.

### B. sections{} as the only authoritative representation
- Semantic safety: Low
- Ordering preservation: Low
- Override preservation: Medium only if strict last-write-wins is encoded
- Conditional preservation: Low
- Include preservation: Low
- Verifier complexity: Medium
- Risk of inconsistent representations: High

Reason:
- A plain merged object discards the order in which rules were applied.
- The repo’s most dangerous failure modes are precisely about ordering and environment-dependent branch selection, so a flat object is not enough.

### C. statements[] authoritative + sections{} derived/read-only view
- Semantic safety: High
- Ordering preservation: High
- Override preservation: High
- Conditional preservation: High
- Include preservation: High
- Verifier complexity: Low to Medium
- Risk of inconsistent representations: Low if the view is generated, not edited

Why this is best:
- The stream is the true semantic source.
- The flat map is the convenience view used by UI tools, tests, and human review.
- This matches the evidence in the repo: the effective settings are the result of a merge process, not the raw final object itself.

### D. both independently authoritative
- Semantic safety: Low
- Ordering preservation: High if both are maintained, but inconsistent if they drift
- Override preservation: Depends on implementation
- Conditional preservation: Depends on implementation
- Include preservation: Depends on implementation
- Verifier complexity: High
- Risk of inconsistent representations: Very high

This is unacceptable for silent-failure prevention.

### Recommendation
Choose C:
- statements[] is authoritative
- sections{} is derived/read-only
- the verifier and evaluator operate on the authoritative stream
- any flat view is a convenience artifact, never a separate truth source

This is the safest architecture because it preserves the actual semantics the legacy system depends on.

---

## Part 2 — Include representation

The critical question is whether the migrated JSON continues to depend on legacy file paths or becomes standalone.

### A. Converted JSON includes converted JSON files
- Preservation of include order: Good
- @include_once semantics: Good if tracked by canonical module id
- Relative paths: Need canonicalization
- Include cycles: Detectable
- Reuse of shared configs: Good
- Migration completeness: Good
- Remove legacy format after migration: Good
- Verifier design: Good

Advantages:
- It separates the migrated config from the original file tree.
- The final JSON can be a graph of modules.

Disadvantages:
- Requires module identity and module graph tracking.
- A converter must retain the full reachable include graph.

### B. JSON continues referencing legacy .pfcfg files
- Preservation of include order: Medium
- @include_once semantics: Medium
- Relative paths: High complexity
- Include cycles: Medium
- Reuse of shared configs: Medium
- Migration completeness: Low
- Remove legacy format after migration: Poor
- Verifier design: Complex

This should be rejected. It keeps the migrated result coupled to the original source tree and makes the target config not truly independent.

### C. Fully inline included content into the entry JSON
- Preservation of include order: Good if the include order is retained
- @include_once semantics: Requires dedupe logic
- Relative paths: Can be erased, but then provenance is lost
- Include cycles: Must still be detected
- Reuse of shared configs: Poor if shared configs are copied repeatedly
- Migration completeness: Medium
- Remove legacy format after migration: Good
- Verifier design: Medium

This is workable but has a problem: it duplicates content and makes reusable modules less explicit. It also risks losing the distinction between:
- a file being included once,
- a file being inlined multiple times,
- and a module that is shared across multiple entry points.

### D. Store include references plus embedded converted modules
- Preservation of include order: High
- @include_once semantics: High
- Relative paths: High if stored as metadata, but the final target should not require them
- Include cycles: High
- Reuse of shared configs: High
- Migration completeness: High
- Remove legacy format after migration: High
- Verifier design: High

This is the best compromise:
- The target JSON contains include nodes that describe the source relationship in semantic terms.
- Each included module can be converted to a module JSON document.
- The entry JSON continues to reference converted modules by module ID rather than by legacy file path.
- The path is kept only as provenance metadata if needed, not as the semantic source of truth.

### Recommendation
Choose D:
- The target format should not keep the legacy file tree as semantic authority.
- The target should keep a semantic include graph with module identities and include order.
- It may preserve legacy path metadata for diagnostics, but not as the source of behavior.

This makes the migrated JSON independent from the .pfcfg tree while still preserving the semantics needed for equivalence verification.

---

## Part 3 — Output structure

### A. One JSON file for every .pfcfg file
- Pros: simple mapping to source tree
- Cons: too many file-level artifacts, not all are entry points, duplicates config modules that are reused
- Not ideal for the starter repo because not every .pfcfg is a customer entry point; many are shared templates or environment overlays

### B. One self-contained JSON file per entry-point config
- Pros: easier to verify behavior for customer entry points
- Cons: shared modules are duplicated or hidden
- Good for verifier convenience, but incomplete for reusable module semantics

### C. Both module JSON files and entry-point JSON files
- Pros: best fit for real structure of `configs`
- Cons: more artifact plumbing

This is the best fit because the repo is intentionally structured into:
- customers/
- environments/
- templates/
- _base/
- edge-cases/

The shared config tree has reusable modules and includes, so a module-based output structure is natural.

### Recommendation
Choose C:
- module JSON files for shared/reusable config fragments
- entry-point JSON files for customer or edge-case top-level configs
- entry files include or reference module IDs as part of a semantic graph
- the verifier chooses an entry file based on the top-level config to evaluate

This matches the repository structure without pretending every file is an entry point.

---

## Part 4 — Final architecture

### 1. What one generated JSON file represents
One generated JSON file represents one logical config module:
- either a top-level entry config, or
- a reusable included module converted from a legacy .pfcfg

It is not necessarily a 1:1 mapping to a single original .pfcfg file in the legacy tree. The file is semantically a module with a stable identity.

### 2. How an include is represented
An include is represented as a semantic include node:
- kind: include or include_once
- target module id
- source path metadata if desired for traceability
- order index
- parent module id

This preserves include order and semantics without keeping the migration dependent on the original .pfcfg file path as the semantic authority.

### 3. How conditionals are represented
Conditionals are explicit structural nodes:
- kind: ifdef or ifndef
- variable name
- body statements
- source metadata

The condition is a semantic fact, not just a text string. This is essential because:
- the repo explicitly distinguishes active vs inactive blocks,
- and the assignment warns against silent behavior changes.

### 4. How assignments are represented
Assignments are explicit statement objects:
- kind: assignment
- section
- key
- value expression
- source file metadata
- order index

This is the authoritative representation for override semantics.

### 5. How expressions are represented
Expressions are typed objects:
- literal
- env
- env_default
- env_alternate
- ref
- concat
- list

This keeps env expressions and config references distinct instead of flattening them into strings too early.

### 6. What is authoritative
The authoritative representation is:
- the ordered statement list for each module
- the include graph between modules
- the semantic expression tree for every assignment value

The flat sections view is derived.

### 7. How the JSON evaluator resolves includes
The evaluator:
- loads the chosen entry module
- resolves the module graph recursively
- evaluates includes in order
- respects include_once by canonical module identity
- detects cycles
- replays statements in encounter order

This is the semantic equivalent of the locked legacy model.

### 8. How @include_once semantics are reproduced
By canonical module identity:
- normalize the include target to a canonical resolved module id
- track already-seen module ids for the current top-level evaluation
- skip duplicates only when the canonical module has already been loaded
- do not compare raw relative paths

This prevents false differences caused by aliasing and different relative path spellings.

### 9. How the converter handles the entire reachable include graph
The converter:
- starts from the chosen entry-point
- traverses the reachable include graph recursively
- converts each reachable module to a JSON module
- assigns each module a stable identity
- writes include references using module ids
- preserves include order and the original declaration order inside each file
- records diagnostics for anything that cannot be represented

This produces a migrated graph independent from the legacy file tree while preserving semantics.

### 10. How the verifier chooses the entry point
The verifier chooses the entry point from the set of top-level files in the repo, such as the ones named in `format-reference.md`:
- customer pipelines
- edge-case entry files
- environment overlays if they are top-level evaluation artifacts
- not every file is necessarily an entry point

The key is:
- an entry point is a config that is intended to be evaluated as a top-level configuration
- include-only modules and shared modules are not entry points by default

---

## Part 5 — False-equivalence attack examples

Below are concrete ways a superficially reasonable JSON schema can silently change behavior.

### 1. Include order bug
Legacy behavior:
- a later include overrides an earlier included file

Buggy JSON:
- final object is built from a set or by sorting includes alphabetically

Why it fails:
- the repo shows actual override sequences in `pipeline.pfcfg` and `ci-shared.pfcfg`

Prevention in recommended architecture:
- include nodes preserve order explicitly
- the evaluator replays statements in order
- the verifier compares semantic effective settings, not a sorted object

### 2. Include_once identity bug
Legacy behavior:
- same file included via different relative path strings should still count as same module

Buggy JSON:
- include_once compares raw path strings

Why it fails:
- different relative references can resolve to the same file
- this breaks the exact path semantics in `format-reference.md`

Prevention:
- use canonical module id, not raw string
- include_once state is tracked by resolved module identity

### 3. Conditional include bug
Legacy behavior:
- conditional include blocks decide whether a file is processed at all

Buggy JSON:
- both branches are represented without preserving the condition

Why it fails:
- the repo has conditionally active includes in `conditional-includes.pfcfg` and `pipeline.pfcfg`

Prevention:
- conditional includes are explicit ifdef/ifndef nodes
- the JSON evaluator must replay the condition with the concrete environment

### 4. Later override bug
Legacy behavior:
- later assignments override earlier ones

Buggy JSON:
- uses object merging without preserving statement chronology

Why it fails:
- many starter values are intentionally layered in override order, especially in `defaults.pfcfg` and `ci-shared.pfcfg`

Prevention:
- assignments are explicit chronological statements
- the flat sections view is derived from replaying them

### 5. Interpolation/reference resolution bug
Legacy behavior:
- `${VAR:-default}` and `$(section.key)` are resolved against the merged config and the environment

Buggy JSON:
- schema stores literal strings only after one conversion pass

Why it fails:
- cross-key interpolation and chained refs are used in `interpolation-cascade.pfcfg` and `pipeline.pfcfg`

Prevention:
- expression objects preserve the original computation structure
- evaluator resolves them using the same semantics, not by a convenient one-pass flattening strategy

### 6. False equivalence through silent stringification
Legacy behavior:
- a value may be intended as a list, a boolean-like string, or an environment expression

Buggy JSON:
- all values are just strings, losing distinction

Why it fails:
- keys like build.parallel and build.steps are semantically different even when they look string-like

Prevention:
- typed expression objects and statement semantics preserve the structure
- the verifier compares resolved effective settings only after evaluation

---

## Part 6 — Final recommendation

## LOCKED JSON ARCHITECTURE

This is the exact model to use in implementation.

1. The authoritative representation is the ordered statement list for each module.
2. The flat section map is derived and read-only.
3. A generated JSON file represents one config module, not necessarily one original .pfcfg file.
4. A module can be:
   - an entry-point config, or
   - a shared or included config fragment
5. Includes are represented as semantic include nodes with:
   - kind
   - target module id
   - include order
   - source metadata
   - canonical file identity for @include_once tracking
6. Conditionals are represented as explicit ifdef or ifndef nodes containing a variable and a body.
7. Assignments are explicit statement nodes with:
   - section
   - key
   - value expression
   - source metadata
   - ordinal order
8. Expressions are explicit typed nodes:
   - literal
   - env
   - env_default
   - env_alternate
   - ref
   - concat
   - list
9. The converter must convert the full reachable include graph from the top-level entry config.
10. The JSON evaluator must:
   - load the entry module
   - resolve include graph
   - evaluate conditionals inline against the concrete environment
   - apply include_once by canonical module identity
   - merge assignments in encounter order
   - resolve interpolation against the merged config
   - detect cycles and missing values
   - compute the final effective settings map
11. The verifier compares final effective settings from the legacy evaluator and the JSON evaluator under the same concrete environment.
12. Legacy file paths are allowed only as provenance metadata, not as the semantic authority.
13. The target format is not allowed to become a static final map unless the semantic trace remains available elsewhere.
14. Any construct that cannot be faithfully represented must be reported as unmigratable, not silently guessed.

This preserves the semantics that matter and prevents the exact silent-failure pattern Jordan calls out in `platform-lead-brief.md`.
