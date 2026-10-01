"""Pure validation and measured duration aggregation. No estimated savings."""

class SchemaError(ValueError):
    """An input field violates the documented schema."""

def validate(records):
    seen = set()
    required = {"id", "workflow", "stage", "duration_ms", "synthetic"}
    for index, record in enumerate(records, 1):
        prefix = f"record {index}"
        if not isinstance(record, dict):
            raise SchemaError(f"{prefix}: expected object")
        if set(record) != required:
            raise SchemaError(f"{prefix}: fields missing={sorted(required-set(record))}, unknown={sorted(set(record)-required)}")
        for field in ("id", "workflow", "stage"):
            value = record[field]
            if not isinstance(value, str) or not value.strip() or len(value) > 10000:
                raise SchemaError(f"{prefix}: {field} must be a nonblank string of at most 10000 characters")
            if any(ord(c) < 32 for c in value) or chr(0x2014) in value:
                raise SchemaError(f"{prefix}: {field} contains forbidden control or punctuation characters")
        if record["id"] in seen:
            raise SchemaError(f"{prefix}: duplicate id {record['id']!r}")
        seen.add(record["id"])
        value = record["duration_ms"]
        if type(value) is not int or not 0 <= value <= 10**12:
            raise SchemaError(f"{prefix}: duration_ms must be an integer between 0 and 1000000000000")
        if type(record["synthetic"]) is not bool:
            raise SchemaError(f"{prefix}: synthetic must be boolean")
    return records

def analyze(records, threshold_ms=1000):
    if type(threshold_ms) is not int or not 0 <= threshold_ms <= 10**12:
        raise SchemaError("threshold_ms must be an integer between 0 and 1000000000000")
    validate(records)
    stages = []
    for stage in sorted({r["stage"] for r in records}):
        rows = [r for r in records if r["stage"] == stage]
        durations = sorted(r["duration_ms"] for r in rows)
        stages.append({"stage": stage, "count": len(rows), "total_ms": sum(durations),
                       "max_ms": max(durations), "p95_ms": durations[(95*len(rows)+99)//100-1],
                       "slow_count": sum(d > threshold_ms for d in durations)})
    slow = sorted((dict(r) for r in records if r["duration_ms"] > threshold_ms), key=lambda r: r["id"])
    return {"record_count": len(records), "workflow_count": len({r["workflow"] for r in records}),
            "total_ms": sum(r["duration_ms"] for r in records), "threshold_ms": threshold_ms,
            "slow_count": len(slow), "slow_records": slow, "stages": stages,
            "synthetic_count": sum(r["synthetic"] for r in records),
            "real_count": sum(not r["synthetic"] for r in records)}
