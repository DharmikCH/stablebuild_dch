"""Utilities for mapping model outputs to human-readable scores and bands."""

from typing import Union


def probability_to_score(probability: Union[float, int]) -> int:
    """
    Map repayment probability to alternative credit score (300–900).
    score = 300 + (probability × 600), clamped to [300, 900].
    """
    p = float(probability)
    score = 300.0 + (p * 600.0)
    return int(max(300, min(900, round(score))))


def probability_to_risk_band(p_default: Union[float, int]) -> str:
    """
    Map P(default) to a risk band label.

    Bands:
        Low    — P(default) < 0.30
        Medium — 0.30 ≤ P(default) < 0.55
        High   — P(default) ≥ 0.55
    """
    p = float(p_default)
    if p < 0.30:
        return "Low"
    elif p < 0.55:
        return "Medium"
    else:
        return "High"
