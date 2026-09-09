from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cashflow import build_forecast, build_scenario
from .models import ForecastResponse, ScenarioRequest, ScenarioResponse

app = FastAPI(title="Cash Flow Intelligence", version="0.4.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.4.0", "forecasting": "temporal-backtest"}


@app.get("/cash-flow/forecast", response_model=ForecastResponse)
def forecast(horizon_days: int = 30) -> ForecastResponse:
    return build_forecast(horizon_days)


@app.post("/cash-flow/scenarios", response_model=ScenarioResponse)
def simulate_scenario(payload: ScenarioRequest) -> ScenarioResponse:
    return build_scenario(payload)
