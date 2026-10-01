"""Synthetic fixtures, no randomness; expectations are independent constants."""
import json
from pathlib import Path

EXPECTED = {"synthetic": True, "_comment": "Synthetic hand-computed expectations: 40*1500 + 4*1500 ms.",
            "record_count": 200, "workflow_count": 40, "total_ms": 66000, "slow_count": 4,
            "slow_ids": ["w00-s5", "w10-s5", "w20-s5", "w30-s5"],
            "stage_totals_ms": {"s1": 4000, "s2": 8000, "s3": 12000, "s4": 16000, "s5": 26000}}

def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = [{"id": f"w{w:02d}-s{s}", "workflow": f"w{w:02d}", "stage": f"s{s}",
             "duration_ms": 2000 if s == 5 and w % 10 == 0 else s*100, "synthetic": True}
            for w in range(40) for s in range(1, 6)]
    from .report import write_atomic, json_text
    write_atomic(out / "records.json", json_text({"_comment": "Synthetic fixture records", "synthetic": True, "records": rows}))
    write_atomic(out / "expectations.json", json_text(EXPECTED))
    return rows
