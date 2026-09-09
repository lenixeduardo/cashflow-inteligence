from app.cashflow import build_forecast, build_scenario, synthetic_history
from app.models import ScenarioRequest


def test_synthetic_history_is_explicit_and_reproducible():
    assert len(synthetic_history()) == 180
    assert synthetic_history()[0] == synthetic_history()[0]
    assert all(row.source == "synthetic" for row in synthetic_history())


def test_temporal_backtest_and_intervals_are_present():
    result = build_forecast(14)
    assert (result.comparison.train_rows, result.comparison.test_rows) == (152, 28)
    assert all(p.lower <= p.forecast <= p.upper for p in result.forecast)


def test_scenario_is_not_labelled_a_forecast():
    result = build_scenario(ScenarioRequest(receivables_change_pct=-25, one_off_outflow=500_000))
    assert result.kind == "scenario_simulation"
    assert "simulação" in result.disclaimer.lower()
