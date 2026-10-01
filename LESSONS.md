# Lessons for KOML

Recorded stage durations can identify threshold exceedances, but their sum is not workflow wall time when stages overlap. Integer milliseconds and nearest-rank percentiles make every figure exactly reproducible without floating-point tolerances.

Validated assumption: a deterministic local CLI finds all four planted slow stages with no false positives and reconciles 200 fixture records to 66000 ms. Corrupting a slow record from 2000 to 500 ms reduces the total to 64500 ms and the slow count to three. This validates arithmetic and threshold classification on synthetic data only. The assumption that the tool earns daily real use remains untested.

Operating rule: keep hand-computed expectations independent of the implementation, mutate an input to prove computation, and label provenance before interpreting any benchmark as production evidence.
