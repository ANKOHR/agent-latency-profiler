"""Deterministic reports and atomic local writes."""
import json
import os
import tempfile
from pathlib import Path

class ReportWriteError(OSError):
    """An atomic local output write failed."""

def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).replace(chr(0x2014), "\\u2014") + "\n"

def banner(result):
    return (f"Provenance: {result['synthetic_count']} synthetic fixture records; "
            f"{result['real_count']} real records (user-declared, intended for Henry's own hand-entered data; ownership not verified). "
            "Durations are supplied observations, not independently measured by alp. "
            "Time and money saved: unmeasured; hypothetical savings are not computed.")

def render(result, format='md'):
    if format == 'json':
        return json_text({"provenance_banner": banner(result), "results": result})
    lines = ["# Agent Latency Profiler", "", banner(result), "",
             f"Records: {result['record_count']}", f"Workflows: {result['workflow_count']}",
             f"Total recorded stage duration: {result['total_ms']} ms", 
             f"Slow records: {result['slow_count']} (duration strictly greater than {result['threshold_ms']} ms)", "",
             "Stage durations are summed work, not elapsed workflow wall time; overlapping stages may occur.", "",
             "| Stage | Count | Total ms | Max ms | P95 ms | Slow count |", "| :--- | ---: | ---: | ---: | ---: | ---: |"]
    for s in result['stages']:
        name = s['stage'].replace('|', '&#124;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append(f"| {name} | {s['count']} | {s['total_ms']} | {s['max_ms']} | {s['p95_ms']} | {s['slow_count']} |")
    lines += ["", "Slow records (JSON for exact traceability):", "", "```json", json_text(result['slow_records']).rstrip(), "```", ""]
    lines += ["Input file provenance:", "", "```json", json_text(result.get('input_sources', [])).rstrip(), "```", ""]
    return "\n".join(lines)

def write_atomic(path, text):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        os.replace(temporary, path)
    except OSError as exc:
        raise ReportWriteError(f"{path}: {exc}") from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
