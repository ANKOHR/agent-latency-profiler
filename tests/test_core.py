import pytest
from agent_latency_profiler.core import analyze, SchemaError

def row(**changes):
    return dict(dict(id="a", workflow="w", stage="s", duration_ms=1001, synthetic=False), **changes)

def test_five_hand_written_records():
    rows = [row(id=str(i), duration_ms=d) for i,d in enumerate([0,100,1000,1001,2000])]
    result = analyze(rows)
    assert result['total_ms'] == 4101
    assert result['slow_count'] == 2
    assert result['stages'][0]['p95_ms'] == 2000

@pytest.mark.parametrize('changes', [{"duration_ms":-1},{"duration_ms":True},{"duration_ms":1.5},{"duration_ms":10**12+1},{"synthetic":"true"},{"id":""},{"stage":"x"*10001},{"stage":chr(0x2014)},{"timestamp":"2999-01-01"},{"amount":-10}])
def test_rejects_adversarial_values(changes):
    with pytest.raises(SchemaError):
        analyze([row(**changes)])

def test_duplicate_ids():
    with pytest.raises(SchemaError, match='duplicate id'):
        analyze([row(), row()])

def test_handles_unicode_and_long_inputs():
    result = analyze([row(stage='分析'+ 'x'*9000, workflow='C:\\用户\\流程')])
    assert result['total_ms'] == 1001

@pytest.mark.parametrize('threshold', [-1, True, 10**12+1])
def test_invalid_threshold(threshold):
    with pytest.raises(SchemaError):
        analyze([], threshold)
