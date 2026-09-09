from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class CashObservation(BaseModel):
    date: date
    opening_balance: float
    inflows: float
    outflows: float
    closing_balance: float
    source: Literal["synthetic", "uploaded"] = "synthetic"


class ForecastPoint(BaseModel):
    date: date
    forecast: float
    lower: float
    upper: float
    baseline: float | None = None
    actual: float | None = None


class ErrorMetrics(BaseModel):
    mae: float
    rmse: float
    wape: float
    interval_coverage: float | None = None


class ModelComparison(BaseModel):
    baseline: ErrorMetrics
    model: ErrorMetrics
    winner: Literal["baseline", "model", "tie"]
    test_start: date
    test_end: date
    train_rows: int
    test_rows: int


class ForecastResponse(BaseModel):
    data_kind: Literal["synthetic", "uploaded"]
    data_notice: str
    generated_from: date
    horizon_days: int
    minimum_reserve: float
    current_balance: float
    history: list[CashObservation]
    forecast: list[ForecastPoint]
    comparison: ModelComparison
    limitations: list[str]


class ScenarioRequest(BaseModel):
    name: str = Field(default="Cenário personalizado", max_length=80)
    receivables_change_pct: float = Field(default=0, ge=-80, le=100)
    outflows_change_pct: float = Field(default=0, ge=-80, le=100)
    one_off_outflow: float = Field(default=0, ge=0)
    horizon_days: int = Field(default=30, ge=7, le=90)


class ScenarioResponse(BaseModel):
    kind: Literal["scenario_simulation"] = "scenario_simulation"
    name: str
    assumptions: ScenarioRequest
    minimum_reserve: float
    points: list[ForecastPoint]
    first_reserve_breach: date | None
    disclaimer: str
