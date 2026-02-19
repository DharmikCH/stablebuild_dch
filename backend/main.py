"""
FastAPI backend for alternative credit scoring — v6.0.0

Endpoints
---------
GET  /health              → liveness + model status
GET  /                    → root info
POST /score               → primary webapp endpoint (raw form fields)
POST /score/batch         → score multiple borrowers in one request
POST /predict             → legacy; accepts pre-computed f_* columns

All scoring responses include:
  repayment_probability    float  — P(repay)
  default_probability      float  — P(default)
  alternative_credit_score int    — 300–900
  predicted_default        bool   — True when P(default) >= profile threshold
  risk_band                str    — "Low" | "Medium" | "High"
  top_factors              list   — top 5 features driving the score (label + direction)

Configuration (env vars — load from .env automatically)
---------
  ALLOWED_ORIGINS   comma-separated allowed CORS origins, default "*"
  MODEL_PATH        path to credit_model.pkl, default ./credit_model.pkl
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

# Load .env file if present (before reading os.environ below)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass  # python-dotenv not installed; rely on env vars being set externally

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from feature_engineering import FEATURE_ORDER, build_feature_vector_from_record
from model import load_model, DEFAULT_MODEL_PATH
from model_utils import probability_to_score, probability_to_risk_band

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _parse_origins(raw: str) -> list[str]:
    parts = [o.strip() for o in raw.split(",") if o.strip()]
    return parts or ["*"]


ALLOWED_ORIGINS: list[str] = _parse_origins(os.environ.get("ALLOWED_ORIGINS", "*"))
MODEL_PATH: Path = Path(os.environ.get("MODEL_PATH", str(DEFAULT_MODEL_PATH)))

PROFILE_TYPES = ["salaried", "student", "gig", "shopkeeper", "rural"]

# Per-profile P(default) thresholds.
# Lower threshold = more sensitive (catches more defaults at cost of false positives).
PROFILE_THRESHOLDS: dict[str, float] = {
    "salaried":   0.40,
    "student":    0.35,   # students have less income history; be more cautious
    "gig":        0.40,
    "shopkeeper": 0.40,
    "rural":      0.35,   # rural borrowers underrepresented; lean cautious
}

# Human-readable feature labels for the explanation field
FEATURE_LABELS: dict[str, str] = {
    "f_monthly_income":           "Monthly income",
    "f_income_variance":          "Income variance",
    "f_savings_balance":          "Savings balance",
    "f_months_active":            "Months of economic activity",
    "f_income_stability":         "Income stability",
    "f_savings_ratio":            "Savings-to-income ratio",
    "f_liquidity_buffer":         "Liquidity buffer",
    "f_total_credits":            "Total credits",
    "f_total_debits":             "Total debits",
    "f_total_transactions":       "Transaction volume",
    "f_avg_credit_amount":        "Avg credit size",
    "f_avg_debit_amount":         "Avg debit size",
    "f_recurring_ratio":          "Recurring payment rate",
    "f_net_cashflow":             "Net cashflow",
    "f_credit_debit_ratio":       "Credit-to-debit ratio",
    "f_gpa":                      "GPA",
    "f_attendance_rate":          "Attendance rate",
    "f_platform_rating":          "Platform rating",
    "f_avg_weekly_hours":         "Avg weekly hours worked",
    "f_business_years":           "Years in business",
    "f_avg_daily_revenue":        "Avg daily revenue",
    "f_land_size_acres":          "Land size (acres)",
    "f_subsidy_amount":           "Subsidy amount",
    "f_seasonality_index":        "Seasonality index",
    "f_is_student":               "Student profile",
    "f_is_gig":                   "Gig worker profile",
    "f_is_shopkeeper":            "Shopkeeper profile",
    "f_is_rural":                 "Rural/agri profile",
    "stability_adjusted_income":  "Stability-adjusted income",
    "income_risk_index":          "Income risk index",
    "missed_payment_proxy":       "Missed payment signal",
    "net_cashflow_ratio":         "Net cashflow ratio",
    "profile_income_signal":      "Profile income signal",
    "profile_rating_signal":      "Profile quality signal",
    "transaction_density":        "Transaction density",
}

# ---------------------------------------------------------------------------
# Model lifecycle
# ---------------------------------------------------------------------------

_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload model at startup; clear on shutdown."""
    try:
        _state["model"] = load_model(MODEL_PATH)
        print(f"[startup] Model loaded from {MODEL_PATH}")
    except FileNotFoundError:
        print(
            f"[startup] WARNING: model not found at {MODEL_PATH}. "
            "Run train_model.py to generate credit_model.pkl."
        )
        _state["model"] = None
    yield
    _state.clear()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Alternative Credit Scoring API",
    version="6.0.0",
    description=(
        "Scores underbanked borrowers across 5 profiles "
        "(salaried, student, gig, shopkeeper, rural) "
        "using a calibrated 35-feature logistic regression model. "
        "Returns credit score (300–900), risk band, and top scoring factors."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def get_model():
    model = _state.get("model")
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model not loaded. "
                "Run `python train_model.py` to generate credit_model.pkl."
            ),
        )
    return model


def _get_threshold(profile: str) -> float:
    return PROFILE_THRESHOLDS.get(profile, 0.40)


def _top_factors(model, X, n: int = 5) -> list[dict[str, Any]]:
    """
    Return the top-n features driving this prediction.

    Uses the logistic regression coefficients from the calibrated pipeline.
    Each factor includes:
      label     — human-readable feature name
      direction — "positive" (helps score) or "negative" (hurts score)
      impact    — absolute scaled coefficient × feature value (relative importance)
    """
    try:
        # Extract the inner LR pipeline from the CalibratedClassifierCV
        # (averaged across calibration folds)
        coef_sum = None
        for calibrated_clf in model.calibrated_classifiers_:
            lr = calibrated_clf.estimator.named_steps["clf"]
            scaler = calibrated_clf.estimator.named_steps["scaler"]
            # coefficient in original feature space = coef / scale
            coef = lr.coef_[0] / scaler.scale_
            coef_sum = coef if coef_sum is None else coef_sum + coef
        coef_avg = coef_sum / len(model.calibrated_classifiers_)

        x_flat = X.flatten()
        # impact = signed contribution to log-odds (positive coef × positive value = higher default risk)
        impacts = coef_avg * x_flat

        # Negative impact on default = positive for repayment (good factor)
        top_idx = sorted(range(len(impacts)), key=lambda i: abs(impacts[i]), reverse=True)[:n]
        factors = []
        for i in top_idx:
            name = FEATURE_ORDER[i]
            raw_impact = float(impacts[i])
            factors.append({
                "label":     FEATURE_LABELS.get(name, name),
                "direction": "negative" if raw_impact > 0 else "positive",
                "impact":    round(abs(raw_impact), 4),
            })
        return factors
    except Exception:
        return []  # graceful degradation — never let explanation failure break scoring


def _make_response(model, X, profile: str = "salaried") -> dict[str, Any]:
    """Run inference and assemble the full response."""
    proba_default = float(model.predict_proba(X)[0, 1])
    proba_repay   = 1.0 - proba_default
    threshold     = _get_threshold(profile)
    return {
        "repayment_probability":    round(proba_repay, 6),
        "default_probability":      round(proba_default, 6),
        "alternative_credit_score": probability_to_score(proba_repay),
        "predicted_default":        proba_default >= threshold,
        "risk_band":                probability_to_risk_band(proba_default),
        "top_factors":              _top_factors(model, X),
    }


def _form_to_record(body: "ScoreRequest") -> dict[str, float]:
    """Map ScoreRequest (form fields) to the f_* record dict."""
    profile = body.profile_type.lower().strip()
    return {
        "f_monthly_income":    body.monthly_income,
        "f_income_variance":   body.income_variance,
        "f_savings_balance":   body.savings_balance,
        "f_months_active":     body.months_active,
        "f_total_credits":     body.total_credits,
        "f_total_debits":      body.total_debits,
        "f_total_transactions":body.total_transactions,
        "f_avg_credit_amount": body.avg_credit_amount,
        "f_avg_debit_amount":  body.avg_debit_amount,
        "f_recurring_ratio":   body.recurring_ratio,
        "f_gpa":               body.gpa             if body.gpa             is not None else 0.0,
        "f_attendance_rate":   body.attendance_rate if body.attendance_rate is not None else 0.0,
        "f_platform_rating":   body.platform_rating  if body.platform_rating  is not None else 0.0,
        "f_avg_weekly_hours":  body.avg_weekly_hours if body.avg_weekly_hours is not None else 0.0,
        "f_business_years":    body.business_years    if body.business_years    is not None else 0.0,
        "f_avg_daily_revenue": body.avg_daily_revenue if body.avg_daily_revenue is not None else 0.0,
        "f_land_size_acres":   body.land_size_acres   if body.land_size_acres   is not None else 0.0,
        "f_subsidy_amount":    body.subsidy_amount     if body.subsidy_amount    is not None else 0.0,
        "f_seasonality_index": body.seasonality_index if body.seasonality_index is not None else 0.0,
        "f_is_student":    1.0 if profile == "student"    else 0.0,
        "f_is_gig":        1.0 if profile == "gig"        else 0.0,
        "f_is_shopkeeper": 1.0 if profile == "shopkeeper" else 0.0,
        "f_is_rural":      1.0 if profile == "rural"      else 0.0,
    }


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TopFactor(BaseModel):
    label:     str    # human-readable feature name
    direction: str    # "positive" (helps score) | "negative" (hurts score)
    impact:    float  # relative absolute impact


class ScoreResponse(BaseModel):
    repayment_probability:    float
    default_probability:      float
    alternative_credit_score: int
    predicted_default:        bool
    risk_band:                str          # "Low" | "Medium" | "High"
    top_factors:              list[TopFactor]


class ScoreRequest(BaseModel):
    """
    Primary request schema — raw webapp form fields.
    profile_type: salaried | student | gig | shopkeeper | rural
    """
    profile_type: str = Field(
        default="salaried",
        description="Borrower profile: salaried | student | gig | shopkeeper | rural",
    )
    monthly_income:    float          = Field(default=0.0, ge=0)
    income_variance:   float          = Field(default=0.0, ge=0)
    savings_balance:   float          = Field(default=0.0, ge=0)
    months_active:     float          = Field(default=0.0, ge=0)
    total_credits:     float          = Field(default=0.0, ge=0)
    total_debits:      float          = Field(default=0.0, ge=0)
    total_transactions:float          = Field(default=0.0, ge=0)
    avg_credit_amount: float          = Field(default=0.0, ge=0)
    avg_debit_amount:  float          = Field(default=0.0, ge=0)
    recurring_ratio:   float          = Field(default=0.0, ge=0, le=1)
    gpa:               Optional[float] = Field(default=None, ge=0, le=4)
    attendance_rate:   Optional[float] = Field(default=None, ge=0, le=1)
    platform_rating:   Optional[float] = Field(default=None, ge=0, le=5)
    avg_weekly_hours:  Optional[float] = Field(default=None, ge=0)
    business_years:    Optional[float] = Field(default=None, ge=0)
    avg_daily_revenue: Optional[float] = Field(default=None, ge=0)
    land_size_acres:   Optional[float] = Field(default=None, ge=0)
    subsidy_amount:    Optional[float] = Field(default=None, ge=0)
    seasonality_index: Optional[float] = Field(default=None, ge=0, le=1)


class BatchScoreRequest(BaseModel):
    """Score up to 50 borrowers in a single request."""
    borrowers: list[ScoreRequest] = Field(..., min_length=1, max_length=50)


class BatchScoreResponse(BaseModel):
    results: list[ScoreResponse]
    count:   int


class PredictRequest(BaseModel):
    """Legacy endpoint schema — pre-computed f_* columns."""
    f_monthly_income:    float = Field(default=0.0, ge=0)
    f_income_variance:   float = Field(default=0.0, ge=0)
    f_savings_balance:   float = Field(default=0.0, ge=0)
    f_months_active:     float = Field(default=0.0, ge=0)
    f_total_credits:     float = Field(default=0.0, ge=0)
    f_total_debits:      float = Field(default=0.0, ge=0)
    f_total_transactions:float = Field(default=0.0, ge=0)
    f_avg_credit_amount: float = Field(default=0.0, ge=0)
    f_avg_debit_amount:  float = Field(default=0.0, ge=0)
    f_recurring_ratio:   float = Field(default=0.0, ge=0, le=1)
    f_gpa:               float = Field(default=0.0, ge=0, le=4)
    f_attendance_rate:   float = Field(default=0.0, ge=0, le=1)
    f_platform_rating:   float = Field(default=0.0, ge=0, le=5)
    f_avg_weekly_hours:  float = Field(default=0.0, ge=0)
    f_business_years:    float = Field(default=0.0, ge=0)
    f_avg_daily_revenue: float = Field(default=0.0, ge=0)
    f_land_size_acres:   float = Field(default=0.0, ge=0)
    f_subsidy_amount:    float = Field(default=0.0, ge=0)
    f_seasonality_index: float = Field(default=0.0, ge=0, le=1)
    f_is_student:        float = Field(default=0.0, ge=0, le=1)
    f_is_gig:            float = Field(default=0.0, ge=0, le=1)
    f_is_shopkeeper:     float = Field(default=0.0, ge=0, le=1)
    f_is_rural:          float = Field(default=0.0, ge=0, le=1)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    """Liveness check. Returns model_loaded = true when ready to score."""
    return {
        "status":       "ok",
        "model_loaded": _state.get("model") is not None,
        "version":      app.version,
    }


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "message": "Alternative Credit Scoring API",
        "version": app.version,
        "docs":    "/docs",
        "health":  "/health",
    }


@app.post("/score", response_model=ScoreResponse, tags=["scoring"])
def score(body: ScoreRequest) -> dict[str, Any]:
    """
    **Primary webapp endpoint.**

    Send raw form fields — no `f_*` prefix needed, no feature engineering required.
    The API automatically:
    - Derives one-hot profile flags from `profile_type`
    - Computes all engineered features internally
    - Returns credit score (300–900), risk band, and top 5 scoring factors
    """
    profile = body.profile_type.lower().strip()
    if profile not in PROFILE_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"profile_type must be one of {PROFILE_TYPES}. Got: '{profile}'",
        )
    try:
        model  = get_model()
        record = _form_to_record(body)
        X      = build_feature_vector_from_record(record)
        return _make_response(model, X, profile)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/score/batch", response_model=BatchScoreResponse, tags=["scoring"])
def score_batch(body: BatchScoreRequest) -> dict[str, Any]:
    """
    Score up to 50 borrowers in a single request.
    Each item in `borrowers` uses the same schema as `POST /score`.
    Results are returned in the same order as the input list.
    """
    model   = get_model()
    results = []
    for borrower in body.borrowers:
        profile = borrower.profile_type.lower().strip()
        if profile not in PROFILE_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid profile_type '{profile}' in batch item.",
            )
        record = _form_to_record(borrower)
        X      = build_feature_vector_from_record(record)
        results.append(_make_response(model, X, profile))
    return {"results": results, "count": len(results)}


@app.post("/predict", response_model=ScoreResponse, tags=["scoring"])
def predict(body: PredictRequest) -> dict[str, Any]:
    """
    Legacy endpoint — accepts pre-computed `f_*` feature columns.
    Prefer `POST /score` for all new webapp integrations.
    """
    try:
        model = get_model()
        X     = build_feature_vector_from_record(body.model_dump())
        return _make_response(model, X, "salaried")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
