"""
Classic queueing-theory baseline.

This is stage 3 of the AI pipeline described in the architecture (see
fila-viva-backend/README.md, section 3): a simple mathematical estimate,
used both as the "traditional" comparison value shown to the person, and
-- until a trained model exists -- as the AI estimate itself.

TODO (next iteration): replace `estimate_wait_minutes` with a call to a
trained LightGBM model plus quantile regression for the confidence
interval (see stage 6, "Inferencia en tiempo real", in the architecture).
Keep `traditional_estimate_minutes` untouched: it must stay naive on
purpose, since it is the baseline the model is compared against.
"""

from __future__ import annotations

DEFAULT_AVG_SERVICE_TIME_MINUTES = 10.8
NORMAL_PEOPLE_PER_AGENT = 2.0
MAX_CONGESTION_FACTOR = 3.0


def congestion_factor(people_ahead: int, active_agents: int) -> float:
    ratio = people_ahead / max(1, active_agents)
    factor = 1 + max(0.0, ratio - NORMAL_PEOPLE_PER_AGENT) * 0.12
    return min(factor, MAX_CONGESTION_FACTOR)


def estimate_wait_minutes(
    people_ahead: int,
    active_agents: int,
    avg_service_time_minutes: float = DEFAULT_AVG_SERVICE_TIME_MINUTES,
) -> float:
    ratio = people_ahead / max(1, active_agents)
    factor = congestion_factor(people_ahead, active_agents)
    return ratio * avg_service_time_minutes * factor


def traditional_estimate_minutes(
    people_ahead: int,
    avg_service_time_minutes: float = DEFAULT_AVG_SERVICE_TIME_MINUTES,
) -> float:
    """
    Naive estimate: position in the queue times a fixed historical
    average, ignoring how many agents are actually active. This is
    intentionally simple -- it represents the kind of calculation a
    conventional ticketing system would make, and it is what the AI
    model is measured against.
    """
    return people_ahead * avg_service_time_minutes


def confidence_score(people_ahead: int, active_agents: int) -> int:
    factor = congestion_factor(people_ahead, active_agents)
    score = 95 - people_ahead * 0.6 - (factor - 1) * 35
    return int(max(35, min(97, round(score))))


def congestion_level(factor: float) -> str:
    if factor > 1.7:
        return "high"
    if factor > 1.2:
        return "medium"
    return "low"
