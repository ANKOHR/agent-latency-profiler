# Local build evidence

Measured on 2026-10-01 with Python 3.12.10 on this Windows CPU-only environment. No network, model calls or GPU workloads were used.

- pytest: 38 passed. Latest suite duration: 0.35 seconds.
- Installed executable demo: `alp fixtures --out demo`, `alp run --input demo`, `alp report --format md`, each in a separate process.
- Measured complete demo duration: 0.767232 seconds.
- Measured report process duration: 0.268677 seconds.
- Computed fixture results: 200 records, 40 workflows, 66000 ms summed stage duration, four slow records, zero false positives against the independent planted IDs.
- Tests confirm exact stage totals, counts, maxima and nearest-rank P95 values. Reports include provenance and source filenames.
- A changed fixture observation yields 64500 ms and three slow records; expected metadata is not used in computation.
- Determinism tests compare serialized result bytes and rendered report text across repeated identical runs.
- These timings measure this local synthetic demo only. They are not production timings or saved-time claims.

The two-week real-use trial, improvement and final verdict remain pending actual observations. See README and VERDICT.md.
