import json
import time
import pytest
from agent_latency_profiler.cli import main, load, InputError
from agent_latency_profiler.fixtures import generate

def test_run_completes_on_fixture(tmp_path, capsys):
    generate(tmp_path/'input')
    state = str(tmp_path/'state.json')
    started = time.perf_counter()
    assert main(['run','--input',str(tmp_path/'input'),'--state',state]) == 0
    assert main(['report','--state',state,'--format','md']) == 0
    assert time.perf_counter()-started < 5
    assert 'Provenance:' in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path,capsys):
    assert main(['run','--input',str(tmp_path),'--state',str(tmp_path/'saved'/'result.json')]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value['results']['total_ms'] == 0
    assert value['results']['record_count'] == 0

@pytest.mark.parametrize('name,content,line', [('bad.json','{',1),('bad.jsonl','# Synthetic\n{',2),('bad.csv','broken',1),('bad.yaml','[',1)])
def test_malformed_input_named_error(tmp_path,capsys,name,content,line):
    (tmp_path/name).write_text(content)
    assert main(['run','--input',str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert name in error and f'line {line}' in error and 'Error' in error
    assert 'Traceback' not in error

def test_determinism_byte_identical(tmp_path,capsys):
    generate(tmp_path/'input')
    state = tmp_path/'state.json'
    argv = ['run','--input',str(tmp_path/'input'),'--state',str(state)]
    assert main(argv) == 0
    first = state.read_bytes()
    output = capsys.readouterr().out
    assert main(argv) == 0
    assert first == state.read_bytes()
    assert output == capsys.readouterr().out
    assert main(['report','--state',str(state)]) == 0
    report = capsys.readouterr().out
    assert main(['report','--state',str(state)]) == 0
    assert report == capsys.readouterr().out

def test_cli_smoke_all_subcommands(tmp_path,capsys):
    assert main(['fixtures','--out',str(tmp_path/'input')]) == 0
    for command in ['run','stages','slow']:
        argv = [command,'--input',str(tmp_path/'input')]
        if command == 'run':
            argv += ['--state',str(tmp_path/'state.json')]
        assert main(argv) == 0
    for fmt in ['md','json']:
        assert main(['report','--state',str(tmp_path/'state.json'),'--format',fmt]) == 0
    for command in ['fixtures','run','stages','slow','report']:
        with pytest.raises(SystemExit) as error:
            main([command,'--help'])
        assert error.value.code == 0
        assert 'Example:' in capsys.readouterr().out

def test_missing_input(tmp_path,capsys):
    assert main(['run','--input',str(tmp_path/'missing')]) == 2
    assert 'MissingInput' in capsys.readouterr().err

def test_report_write_failure_no_partial_files(tmp_path,capsys):
    generate(tmp_path/'input')
    state = tmp_path/'state.json'
    assert main(['run','--input',str(tmp_path/'input'),'--state',str(state)]) == 0
    capsys.readouterr()
    assert main(['report','--state',str(state),'--out',str(tmp_path/'missing'/'out.md')]) == 2
    assert 'Error' in capsys.readouterr().err
    assert not (tmp_path/'missing').exists()
    assert not list(tmp_path.glob('tmp*'))

def test_cross_file_duplicates(tmp_path):
    row = dict(id='a', workflow='w', stage='s', duration_ms=5, synthetic=True)
    for name in ['a.jsonl','b.jsonl']:
        (tmp_path/name).write_text(json.dumps(row))
    with pytest.raises(InputError,match='duplicate id'):
        load(tmp_path)

def test_envelope_mismatch(tmp_path):
    (tmp_path/'bad.json').write_text(json.dumps(dict(_comment='Synthetic',synthetic=True,records=[dict(id='a',workflow='w',stage='s',duration_ms=5,synthetic=False)])))
    with pytest.raises(InputError,match='synthetic'):
        load(tmp_path)


def test_mixed_file_provenance(tmp_path,capsys):
    for name,synthetic in [('real.jsonl',False),('synthetic.jsonl',True)]:
        row = dict(id=name,workflow='w',stage='s',duration_ms=1,synthetic=synthetic)
        (tmp_path/name).write_text(json.dumps(row))
    assert main(['run','--input',str(tmp_path),'--state',str(tmp_path/'saved'/'results.json')]) == 0
    result = json.loads(capsys.readouterr().out)['results']
    assert result['real_count'] == result['synthetic_count'] == 1
    assert result['input_sources'] == [dict(file='real.jsonl',real_count=1,synthetic_count=0),dict(file='synthetic.jsonl',real_count=0,synthetic_count=1)]
