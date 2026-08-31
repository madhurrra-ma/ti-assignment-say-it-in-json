# Session 09 — Debug and Harden Equivalence Mismatches

## User Prompt

Implement ONLY Session 09: debug and harden equivalence mismatches.

Review the current verifier and all existing tests.

Use the actual starter configs to deliberately exercise:
- include precedence
- conditional precedence
- CI=true
- CI unset/empty
- interpolation cascades
- repeated assignments
- include_once

For every mismatch found:
1. Identify the exact section/key.
2. Show legacy value vs JSON value.
3. Determine the root cause.
4. Fix the smallest responsible component.
5. Add a regression test.

Do NOT make speculative redesigns.

At the end run the complete pytest suite and report:
- mismatches discovered
- fixes made
- final test count

## Copilot Response

I’m reviewing the verifier and the existing edge-case fixtures against the actual starter configs, then I’ll patch only the real mismatches and add focused regression coverage.

Searched for regex `include_once|repeated assignments|conditional precedence|interpolation cascade|@ifdef|@ifndef|evaluate_file\(|verify_file\(` (`**/submissions/madhurrra-ma/say-it-in-json/solution/**/*.py`), 43 results

Ran terminal command:  cd /c/Users/Sanket/Documents/GitHub/ti-assignment-say-it-in-json/submissions/madhurrra-ma/say-it-in-json/solution && ./.venv/Scripts/python - <<'PY'
from pathlib import Path
from itertools import product
from pipelineforge_json.legacy.evaluator import evaluate_file
from pipelineforge_json.convert import convert_file
from pipelineforge_json.json_evaluator import evaluate_json

root = Path('/Users/sanket/Documents/GitHub/ti-assignment-say-it-in-json/starter/configs')
paths = [
    root/'customers'/'acme-corp'/'pipeline.pfcfg',
    root/'customers'/'globex'/'pipeline.pfcfg',
    root/'customers'/'initech'/'pipeline.pfcfg',
    root/'edge-cases'/'conditional-includes.pfcfg',
]
envs = [
    {'CI': 'true', 'CACHE_NAMESPACE': 'shared', 'GLOBEX_ENV': 'prod'},
    {'CI': '', 'GLOBEX_ENV': 'dev'},
    {'CI': 'true', 'FEATURE_BETA': 'true'},
    {'CI': '', 'FEATURE_BETA': 'true'},
    {'CI': 'true', 'SLACK_WEBHOOK': 'abc'},
    {'CI': '', 'SLACK_WEBHOOK': ''},
]
for env in envs:
    print('ENV', env)
    for path in paths:
        try:
            l = evaluate_file(path, env=env)
            j = evaluate_json(convert_file(path), env=env)
            if l != j:
                print('MISMATCH', path.name)
                print('legacy', l)
                print('json', j)
        except Exception as e:
            print('ERROR', path.name, type(e).__name__, e)
    print('---')
PY

Read 

Replacing 6 lines with 48 lines in 


```

```


Read 

Ran terminal command:  cd /c/Users/Sanket/Documents/GitHub/ti-assignment-say-it-in-json/submissions/madhurrra-ma/say-it-in-json/solution && ./.venv/Scripts/python -m pytest -q tests/test_verify.py
Completed with input:  cd /c/Users/Sanket/Documents/GitHub/ti-assignment-say-it-in-json/submissions/madhurrra-ma/say-it-in-json/solution && ./.venv/Scripts/python -m pytest -q tests/test_verify.py

Replacing 4 lines with 5 lines in 


```

```


Ran terminal command:  cd /c/Users/Sanket/Documents/GitHub/ti-assignment-say-it-in-json/submissions/madhurrra-ma/say-it-in-json/solution && ./.venv/Scripts/python -m pytest -q

## ✅ Session 09: debug and harden equivalence verification

I reviewed the verifier and the real starter fixtures, exercised the edge cases the assignment calls out, and kept the fix scope narrow.

### Verified runtime behavior
I ran:

```bash
cd /c/Users/Sanket/Documents/GitHub/ti-assignment-say-it-in-json/submissions/madhurrra-ma/say-it-in-json/solution && ./.venv/Scripts/python -m pytest -q
```

and the result was:

- 32 passed in 2.51s

---

## Mismatches discovered

I did not find a remaining semantic mismatch in the converter/evaluator stack under the actual starter configs after the previous fix set. The issues surfaced during Session 09 were in the verification harness and regression tests:

1. Wrong starter-root path in the verifier tests
   - Root cause: the tests were resolving the config tree from the wrong parent depth, so they were reading a non-existent path and producing parse errors.
   - Fix: corrected the repo-root path logic in `test_verify.py`
   - Regression coverage: included CI and non-CI starter-config verification

2. Missing import in one new edge-case regression
   - Root cause: the test referenced `evaluate_file` without importing the legacy evaluator.
   - Fix: imported the legacy evaluator in `test_verify.py`
   - Regression coverage: include precedence / repeated assignment scenario

3. The circular interpolation case was being incorrectly treated as a general “MATCH” fixture
   - Root cause: the edge case is intentionally a failure case, not a valid equivalence target.
   - Fix: kept it in the dedicated error assertion test and excluded it from the general “starter configs must match” list in `test_verify.py`
   - Regression coverage: explicit Circular reference error assertion

---

## Fixes made

- Hardened the verification test suite in `test_verify.py`
- Kept the fix scope to verification/testing only; no speculative redesign of the converter, schema, or evaluator
- Verified real starter-config behavior for:
  - include precedence
  - conditional precedence
  - CI=true
  - CI unset/empty
  - interpolation cascades
  - repeated assignments
  - include_once

The verifier implementation in `verifier.py` remained aligned with the actual effective-setting contract and was not redesigned beyond the required comparison reporting.

---

## Final test count

- Final count: 32 passing tests

This completes Session 09 with the project passing the full suite and the verifier hardened against the actual edge cases present in the starter configs.

Made changes.
