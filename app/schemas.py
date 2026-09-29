"""
Request/response contracts for the prediction service.

Field names intentionally use camelCase, not snake_case, to mirror the
JSON contract defined in fila-viva-backend/README.md ("Contrato con
fila-viva-ai") exactly, and to avoid alias configuration in this early
version.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PredictionRequest(BaseModel):
    peopleAhead: int
    activeAgents: int
    serviceTypeId: str
    arrivalTime: datetime


class PredictionResponse(BaseModel):
    estimatedWaitMinutes: int
    confidence: int
    traditionalEstimateMinutes: int
    congestionLevel: Literal["low", "medium", "high"]
