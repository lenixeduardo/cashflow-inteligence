"""Reproducible cash-flow forecasting with an explicit synthetic data contract."""
from __future__ import annotations

import math
from datetime import date, timedelta

from .models import CashObservation, ErrorMetrics, ForecastPoint, ForecastResponse, ModelComparison, ScenarioRequest, ScenarioResponse

MINIMUM_RESERVE = 1_000_000.0
ANCHOR_DATE = date(2026, 8, 26)


def synthetic_history(days: int = 180) -> list[CashObservation]:
    """Deterministic fictional treasury ledger; it must never be read as real data."""
    balance = 1_260_000.0
    start = ANCHOR_DATE - timedelta(days=days - 1)
    rows: list[CashObservation] = []
    for i in range(days):
        current = start + timedelta(days=i)
        inflows = 87_000 + 18_000 * math.sin(i / 8) + 8_500 * math.cos(i / 17)
        outflows = 79_000 + 14_000 * math.cos(i / 9) + 7_000 * math.sin(i / 13)
        if current.weekday() in (5, 6):
            inflows, outflows = inflows * .34, outflows * .47
        if i % 29 == 0: outflows += 118_000
        if i % 37 == 0: inflows += 145_000
        opening = balance
        balance += inflows - outflows
        rows.append(CashObservation(date=current, opening_balance=round(opening, 2), inflows=round(inflows, 2), outflows=round(outflows, 2), closing_balance=round(balance, 2)))
    return rows


def _baseline(history: list[CashObservation], index: int) -> float:
    same_weekday = [r.closing_balance for r in history[:index] if r.date.weekday() == history[index].date.weekday()][-4:]
    values = same_weekday or [r.closing_balance for r in history[max(0, index - 7):index]]
    return sum(values) / len(values)


def _model(history: list[CashObservation], index: int) -> float:
    seasonal = _baseline(history, index)
    recent = history[max(0, index - 14):index]
    drift = (recent[-1].closing_balance - recent[0].closing_balance) / max(1, len(recent) - 1)
    return seasonal + 3 * drift


def _metrics(actual: list[float], predicted: list[float], lower: list[float] | None = None, upper: list[float] | None = None) -> ErrorMetrics:
    errors = [a - p for a, p in zip(actual, predicted)]
    mae = sum(abs(e) for e in errors) / len(errors)
    rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
    coverage = None if lower is None or upper is None else sum(lo <= a <= hi for a, lo, hi in zip(actual, lower, upper)) / len(actual)
    return ErrorMetrics(mae=round(mae, 2), rmse=round(rmse, 2), wape=round(sum(abs(e) for e in errors) / (sum(abs(a) for a in actual) or 1) * 100, 2), interval_coverage=None if coverage is None else round(coverage * 100, 2))


def _backtest(history: list[CashObservation]) -> tuple[ModelComparison, float, float]:
    split = len(history) - 28
    actual = [r.closing_balance for r in history[split:]]
    baseline = [_baseline(history, i) for i in range(split, len(history))]
    model = [_model(history, i) for i in range(split, len(history))]
    residuals = sorted(a - p for a, p in zip(actual, model))
    lo, hi = residuals[int(.1 * (len(residuals) - 1))], residuals[int(.9 * (len(residuals) - 1))]
    b_metrics, m_metrics = _metrics(actual, baseline), _metrics(actual, model, [p + lo for p in model], [p + hi for p in model])
    winner = "model" if m_metrics.mae < b_metrics.mae else "baseline" if b_metrics.mae < m_metrics.mae else "tie"
    return ModelComparison(baseline=b_metrics, model=m_metrics, winner=winner, test_start=history[split].date, test_end=history[-1].date, train_rows=split, test_rows=len(history)-split), lo, hi


def build_forecast(horizon_days: int = 30) -> ForecastResponse:
    horizon_days = max(7, min(horizon_days, 90)); history = synthetic_history(); comparison, residual_lo, residual_hi = _backtest(history); rolling = list(history); points = []
    for _ in range(horizon_days):
        index, next_date = len(rolling), rolling[-1].date + timedelta(days=1)
        placeholder = CashObservation(date=next_date, opening_balance=rolling[-1].closing_balance, inflows=0, outflows=0, closing_balance=rolling[-1].closing_balance); rolling.append(placeholder)
        baseline, estimate = _baseline(rolling, index), _model(rolling, index)
        rolling[-1] = placeholder.model_copy(update={"closing_balance": estimate})
        points.append(ForecastPoint(date=next_date, forecast=round(estimate, 2), lower=round(estimate + residual_lo, 2), upper=round(estimate + residual_hi, 2), baseline=round(baseline, 2)))
    return ForecastResponse(data_kind="synthetic", data_notice="Dados sintéticos, determinísticos e seguros para demonstração. Não representam caixa, clientes ou transações reais.", generated_from=history[-1].date, horizon_days=horizon_days, minimum_reserve=MINIMUM_RESERVE, current_balance=history[-1].closing_balance, history=history[-60:], forecast=points, comparison=comparison, limitations=["Modelo de referência sazonal; não substitui validação financeira.", "Intervalos vêm dos resíduos do período de teste, não são garantia.", "Dados sintéticos não comprovam desempenho em produção."])


def build_scenario(request: ScenarioRequest) -> ScenarioResponse:
    base = build_forecast(request.horizon_days); points = []; breach = None
    for i, point in enumerate(base.forecast):
        projected = point.forecast + 42_000 * request.receivables_change_pct / 100 * (i + 1) - 38_000 * request.outflows_change_pct / 100 * (i + 1) - (request.one_off_outflow if i == 0 else 0)
        new = ForecastPoint(date=point.date, forecast=round(projected, 2), lower=round(projected + point.lower - point.forecast, 2), upper=round(projected + point.upper - point.forecast, 2)); points.append(new)
        if breach is None and new.lower < MINIMUM_RESERVE: breach = new.date
    return ScenarioResponse(name=request.name, assumptions=request, minimum_reserve=MINIMUM_RESERVE, points=points, first_reserve_breach=breach, disclaimer="Cenário é uma simulação de premissas informadas. Não é uma previsão calibrada nem recomendação financeira.")
