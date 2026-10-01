"""Local-only command line interface."""
import argparse
import json
import sys
from pathlib import Path
from .core import analyze, SchemaError, validate
from .fixtures import generate
from .report import json_text, render, write_atomic

class InputError(ValueError):
    pass

def load(directory, sources=None):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use alp run --input <existing directory>")
    records = []
    for path in sorted(directory.iterdir()):
        if path.name == 'expectations.json' or not path.is_file():
            continue
        if path.suffix.lower() not in {'.json', '.jsonl'}:
            raise InputError(f"SchemaError: {path}: line 1: unsupported format; use JSON or JSONL")
        start = len(records)
        try:
            content = path.read_text(encoding='utf-8')
            if path.suffix.lower() == '.jsonl':
                entries = []
                for number, line in enumerate(content.splitlines(), 1):
                    if not line.strip() or line.startswith('#'):
                        continue
                    try:
                        entries.append((number, json.loads(line)))
                    except json.JSONDecodeError as exc:
                        raise InputError(f"ParseError: {path}: line {number}: {exc.msg}") from exc
            else:
                value = json.loads(content)
                if not isinstance(value, dict) or set(value) != {'_comment', 'synthetic', 'records'}:
                    raise SchemaError("envelope fields must be _comment, synthetic, records")
                if type(value['synthetic']) is not bool or not isinstance(value['_comment'], str) or not isinstance(value['records'], list):
                    raise SchemaError("invalid envelope synthetic, _comment or records field")
                if any(isinstance(r, dict) and r.get('synthetic') != value['synthetic'] for r in value['records']):
                    raise SchemaError("synthetic field disagrees with envelope")
                entries = [(content.count('\n', 0, content.find('"records"'))+1, r) for r in value['records']]
            for number, row in entries:
                try:
                    validate([row])
                except SchemaError as exc:
                    raise InputError(f"SchemaError: {path}: line {number}: {exc}") from exc
                if any(previous['id'] == row['id'] for previous in records):
                    raise InputError(f"SchemaError: {path}: line {number}: duplicate id {row['id']!r}")
                records.append(row)
            if sources is not None:
                added = records[start:]
                sources.append({'file': path.name, 'synthetic_count': sum(r['synthetic'] for r in added),
                                'real_count': sum(not r['synthetic'] for r in added)})
        except json.JSONDecodeError as exc:
            raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc
        except SchemaError as exc:
            raise InputError(f"SchemaError: {path}: line 1: {exc}") from exc
        except UnicodeError as exc:
            raise InputError(f"ParseError: {path}: line 1: invalid UTF-8") from exc
    return records

def main(argv=None):
    parser = argparse.ArgumentParser(prog='alp', description='Compute recorded stage latency from local inputs. No estimates or network calls.')
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('fixtures', help='Generate 200 labelled synthetic records', epilog='Example: alp fixtures --out demo')
    p.add_argument('--out', required=True)
    for name, description in [('run', 'Analyze and save results'), ('stages', 'Show stage aggregates'), ('slow', 'Show records above an explicit threshold')]:
        p = subs.add_parser(name, help=description, description=description, epilog=f'Example: alp {name} --input demo --threshold-ms 1000')
        p.add_argument('--input', required=True)
        p.add_argument('--threshold-ms', type=int, default=1000)
        if name == 'run':
            p.add_argument('--state', default='.alp/results.json')
    p = subs.add_parser('report', help='Render saved results with provenance', epilog='Example: alp report --format md')
    p.add_argument('--format', choices=['md', 'json'], default='md')
    p.add_argument('--state', default='.alp/results.json')
    p.add_argument('--out')
    args = parser.parse_args(argv)
    try:
        if args.command == 'fixtures':
            generate(args.out)
            print('Generated 200 synthetic records; supplied illustrative durations, not real measurements.')
        elif args.command in {'run', 'stages', 'slow'}:
            sources = []
            result = analyze(load(args.input, sources), args.threshold_ms)
            result['input_sources'] = sources
            if args.command == 'run':
                path = Path(args.state)
                path.parent.mkdir(parents=True, exist_ok=True)
                write_atomic(path, json_text(result))
                print(render(result, 'json'), end='')
            else:
                from .report import banner
                print(json_text({'provenance_banner': banner(result), args.command: result['stages' if args.command == 'stages' else 'slow_records']}), end='')
        else:
            path = Path(args.state)
            if not path.is_file():
                raise InputError(f'MissingInput: {path}; run alp run --input <dir> first')
            try:
                result = json.loads(path.read_text(encoding='utf-8'))
                output = render(result, args.format)
            except (ValueError, KeyError, TypeError) as exc:
                raise InputError(f'SchemaError: {path}: invalid saved results: {exc}') from exc
            if args.out:
                write_atomic(args.out, output)
            else:
                print(output, end='')
        return 0
    except (InputError, SchemaError, OSError) as exc:
        text = f'{type(exc).__name__}: {exc}'.replace(chr(0x2014), '[dash]')
        print(text, file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
