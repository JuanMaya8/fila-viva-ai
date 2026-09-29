from datetime import datetime, timezone

from fastapi import FastAPI

from app.queueing import (
    confidence_score,
    congestion_factor,
    congestion_level,
    estimate_wait_minutes,
    traditional_estimate_minutes,
)
from app.schemas import PredictionRequest, PredictionResponse

app = FastAPI(
    title="Fila Viva - AI Service",
    description=(
        "Prediction service for Fila Viva. Combines a classic "
        "queueing-theory baseline with, eventually, a trained ML model. "
        "See fila-viva-backend/README.md for the full architecture."
    ),
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "fila-viva-ai",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    """
    Current version (week 3): pure queueing-theory baseline, no trained
    model yet. This is intentional: it lets fila-viva-backend integrate
    against the final contract today, and the ML model can replace the
    body of this function later without changing the API.

    TODO (next iteration):
      1. Load recent history for this serviceTypeId (see ARCHITECTURE.md,
         stage 1, "Ingesta de datos").
      2. Build the feature set described in stage 2 ("Ingenieria de
         variables"): hour of day, day of week, rolling average duration.
      3. Replace estimate_wait_minutes(...) with a call to the trained
         LightGBM model plus a quantile-regression confidence interval.
      4. Keep traditional_estimate_minutes(...) untouched: it must stay
         naive, since it is the comparison baseline shown to the person.
    """
    factor = congestion_factor(request.peopleAhead, request.activeAgents)

    estimated = estimate_wait_minutes(request.peopleAhead, request.activeAgents)
    traditional = traditional_estimate_minutes(request.peopleAhead)
    confidence = confidence_score(request.peopleAhead, request.activeAgents)

    return PredictionResponse(
        estimatedWaitMinutes=round(estimated),
        confidence=confidence,
        traditionalEstimateMinutes=round(traditional),
        congestionLevel=congestion_level(factor),
    )
