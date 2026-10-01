# Agent Latency Profiler

`alp` finds recorded workflow stages whose supplied duration exceeds an explicit threshold. It computes from local inputs, uses only the CPU and Python standard library at runtime, and makes no network or model calls.

Hypothesis: deterministic validation, exact aggregation and planted ground truth make latency reports trustworthy. Acceptance: all four planted slow records found, zero false positives, exact counts and totals, and the 200-record demo completes in under five seconds.

## Quickstart

Python 3.10 or newer, setuptools and pytest are needed for local development. Install from this checkout without network access:

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
alp fixtures --out demo
alp run --input demo
alp report --format md
python -m pytest -q
```

If Windows reports that the user Scripts directory is not on PATH, add the directory named by pip to your shell PATH to invoke `alp`, or use the module command below.

The package also runs without installation as `python -m agent_latency_profiler.cli`. Saved results default to `.alp/results.json`, relative to the working directory. Reports read that snapshot; rerun `run` after changing input. `run` prints its full result with provenance. Generated demo and state files are ignored by git. Trial results from real use must stay local and must not be committed.

## Input format

Supply a directory containing only JSON or JSONL record files and optionally `expectations.json`. Files are processed in filename order; nested directories are not scanned. `expectations.json` is fixture metadata and is never used to compute results. CSV and YAML are explicitly unsupported and produce a named schema error with a conversion hint.

JSON uses this exact envelope. `_comment` is the header comment equivalent for JSON, which does not support literal comments:

```json
{
  "_comment": "Synthetic illustrative example, not measured real data",
  "synthetic": true,
  "records": [
    {"id": "demo-1", "workflow": "demo", "stage": "plan", "duration_ms": 100, "synthetic": true},
    {"id": "demo-2", "workflow": "demo", "stage": "fetch", "duration_ms": 200, "synthetic": true},
    {"id": "demo-3", "workflow": "demo", "stage": "execute", "duration_ms": 1000, "synthetic": true},
    {"id": "demo-4", "workflow": "demo", "stage": "review", "duration_ms": 1001, "synthetic": true},
    {"id": "demo-5", "workflow": "demo", "stage": "save", "duration_ms": 2000, "synthetic": true}
  ]
}
```

This five-record example totals 4301 ms and has two slow records at the default threshold. The independent five-record core test uses durations 0, 100, 1000, 1001 and 2000, totalling 4101 ms.

For Henry's own hand-entered observations, set `synthetic` to `false` on the envelope and every record, and describe the source in `_comment`. Ownership and instrument accuracy are user-declared, not verified. JSONL has one record object per line and may start with `# Synthetic illustrative records` for synthetic data. Every synthetic JSONL row must have `synthetic: true`. A directory can contain both real and synthetic files; reports retain their separate counts and per-file provenance.

| Field | Rule |
| :--- | :--- |
| id | Unique across every input file |
| workflow | Workflow grouping identifier |
| stage | Stage grouping identifier |
| duration_ms | Integer from 0 to 1000000000000 inclusive, no floats or booleans |
| synthetic | Explicit boolean provenance declaration |

All three strings must be nonblank, at most 10000 characters, and contain no ASCII control characters or U+2014 punctuation. Unicode and Windows path strings are supported. Unknown fields are rejected, including dates and amounts: this schema makes no date or money claims, so future dates and negative amounts cannot silently influence results. Duplicate IDs are errors, never silently dropped. JSON input must be UTF-8. Envelope provenance must match its records. A record is a stage occurrence; repeated workflow and stage identifiers are allowed with distinct record IDs.

## Commands

```powershell
alp fixtures --out demo
alp run --input demo --threshold-ms 1000 --state .alp/results.json
alp stages --input demo --threshold-ms 1000
alp slow --input demo --threshold-ms 1000
alp report --format md --out report.md
alp report --format json --state .alp/results.json --out report.json
```

Every command supports `--help` with an example. `stages` shows count, total, maximum, nearest-rank P95 and slow count by stage. `slow` shows exact qualifying records with IDs. Slow means strictly greater than the threshold, not equal to it. P95 uses the sorted value at one-based rank `ceil(0.95 * count)`; there is no interpolation or rounding of durations. Stages and slow IDs are sorted lexically.

Total milliseconds are the sum of supplied stage durations. They are not workflow elapsed wall time or a critical path: concurrent stages may overlap. The CLI does not infer bottleneck causality. Empty input produces zero counts, a zero total and empty lists. No random generation or seed is used. Identical inputs and threshold yield byte-identical results; reports omit timestamps and machine-specific absolute input paths.

## Architecture

```text
local JSON / JSONL -> CLI loader -> core validation and aggregation
                                        |
                                        v
                                atomic results snapshot
                                        |
                                        v
                                JSON / Markdown report
fixtures generator -> labelled inputs + independent expectations
```

`core.py` contains pure functions with no I/O. `cli.py` handles local parsing and named errors. `fixtures.py` generates deterministic labelled examples. `report.py` renders provenance and writes UTF-8 via an adjacent temporary file and atomic replacement. Runtime has no external dependencies.

## Honesty boundary and fixture labelling

All numerical results come from explicit records. Synthetic durations are illustrative, not measured production latencies. Reports label synthetic and user-declared real counts, list source filenames and state that durations are supplied observations. Time saved and money saved are unmeasured; hypothetical savings are not computed. There is no baseline comparison feature and no savings claim. Synthetic and real records are aggregated together only with this visible provenance breakdown.

Every generated JSON file has a leading `_comment` identifying it as synthetic and a `synthetic: true` field. Every fixture record also has that field. The 200-record fixture is 40 workflows with five stages: base durations 100, 200, 300, 400 and 500 ms. Workflows 00, 10, 20 and 30 have stage 5 replaced by 2000 ms. Independent expectations: 40 * 1500 + 4 * 1500 = 66000 ms; stage totals 4000, 8000, 12000, 16000 and 26000 ms; four slow records. Expectations are literal hand-computed constants, not generated by the core engine.

## Failure modes

Missing input gives `MissingInput` with a usage hint. Invalid JSON gives `ParseError` with filename and exact parser line. Invalid UTF-8 gives `ParseError` with filename and line 1. Invalid schema gives `SchemaError` naming the field and file; JSONL gives the exact row line, while JSON record validation names the record and the records-array starting line. Unsupported formats are rejected rather than guessed. Errors exit with status 2 and no traceback. A report write failure is a named `ReportWriteError`; temporary files are removed and an existing target is preserved if replacement fails. Parent output directories must exist. Fixture generation writes files atomically individually; it is not a multi-file transaction. Inputs and saved snapshots are trusted local files; concurrent writers and hostile symlink manipulation are outside this version's scope. `alp` does not time or instrument live agents.

## Evidence and two-week improvement hook

See `EVIDENCE.md` for the local tests and demo timing. Tests include malformed input, empty input, threshold boundaries, extreme and negative values, schema drift, duplicate IDs, Unicode, long strings, deterministic output, output write failures and corruption of an actual fixture record. Changing the record changes the totals, proving that expectations are not substituted for computation.

After two weeks of real use, hand-check at least 20 stage records and compare slow classification and stage totals against the report. Record actual run count, sample IDs, disagreements, denominator and error rate in a private local trial log. Error rate is incorrect checked classifications or stage totals divided by the number of checked items. This is the primary metric; no time-saving estimate substitutes for it. If error exceeds 10 percent, fix the top demonstrated cause and rerun the sample, or kill the project with the reason recorded. If there were no real runs, record non-use and kill it. One evidence-based improvement is deferred until those observations exist.

Verdict: **pending the two-week evidence window**, not a claim of adoption or revenue. Record the date, evidence and explicit final verdict in `VERDICT.md`: expand if it earns daily use or revenue; integrate if it substantially overlaps a sibling; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill if unused or unable to meet acceptance criteria. Local synthetic acceptance does not establish production utility.
