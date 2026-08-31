# PipelineForge JSON migration tooling

This project turns legacy PipelineForge `.pfcfg` configuration files into a schema-validated JSON representation and verifies that the migrated configuration evaluates to the same effective settings as the original legacy source.

## What the project does

- Parses legacy `.pfcfg` configuration files, including sections, assignments, includes, conditional blocks, and interpolation.
- Converts the parsed legacy structure into a JSON document that matches the project schema.
- Evaluates both the legacy and converted JSON forms to compute effective settings.
- Compares them and reports `MATCH`, `MISMATCH`, or `ERROR` outcomes.
- Produces an unmigratable report for values that require runtime environment input and cannot be safely converted automatically.

## Setup with uv

From the project root:

```bash
cd submissions/madhurrra-ma/say-it-in-json/solution
uv sync
```

This project targets Python 3.12.

## How to run the converter

The converter is used via the Python API:

```bash
uv run python - <<'PY'
from pathlib import Path
from pipelineforge_json.convert import convert_file

path = Path('starter/configs/customers/acme-corp/pipeline.pfcfg')
doc = convert_file(path)
print(doc['version'])
print(len(doc['sections']))
PY
```

## How to run the verifier

```bash
uv run python - <<'PY'
from pathlib import Path
from pipelineforge_json.verify import verify_file

path = Path('starter/configs/customers/acme-corp/pipeline.pfcfg')
result = verify_file(path, env={'CI': 'true', 'CACHE_NAMESPACE': 'shared', 'GLOBEX_ENV': 'prod'})
print(result['status'])
print(result.get('differences'))
PY
```

## How to generate the unmigratable report

```bash
uv run python - <<'PY'
from pathlib import Path
from pipelineforge_json.verify import write_unmigratable_report

paths = [Path('starter/configs/edge-cases/conditional-includes.pfcfg')]
out = write_unmigratable_report(paths, 'artifacts/unmigratable.json')
print(out)
PY
```

## How to run the tests

```bash
uv run pytest -q
```

## Required starter fixtures covered

The equivalence and converter checks intentionally exercise the real fixtures under `starter/configs`:

- `customers/acme-corp/pipeline.pfcfg`
- `customers/globex/pipeline.pfcfg`
- `customers/initech/pipeline.pfcfg`
- `edge-cases/conditional-includes.pfcfg`
- `edge-cases/interpolation-cascade.pfcfg`

These are the source-of-truth fixtures for migration validation.
