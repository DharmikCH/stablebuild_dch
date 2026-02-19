"""Build ordered numpy feature vector for credit scoring model.

Feature design — aligned with the `feature_columns` SQL view
--------------------------------------------------------------
Inputs come directly from the view's `f_*` columns (or equivalent
raw DB fields computed by the view).

Groups
------
Core financial (7):
    f_monthly_income, f_income_variance, f_savings_balance,
    f_months_active, f_income_stability, f_savings_ratio,
    f_liquidity_buffer

Transaction behaviour (8):
    f_total_credits, f_total_debits, f_total_transactions,
    f_avg_credit_amount, f_avg_debit_amount, f_recurring_ratio,
    f_net_cashflow, f_credit_debit_ratio

Profile-specific raw signals (10):
    f_gpa, f_attendance_rate,               ← student
    f_platform_rating, f_avg_weekly_hours,  ← gig
    f_business_years, f_avg_daily_revenue,  ← shopkeeper
    f_land_size_acres, f_subsidy_amount,    ← rural
    f_seasonality_index,                    ← rural
    (9 signals total — seasonality is shared rural slot)

Profile one-hot (4):
    f_is_student, f_is_gig, f_is_shopkeeper, f_is_rural

Engineered cross features (7):
    stability_adjusted_income, income_risk_index,
    missed_payment_proxy, net_cashflow_ratio,
    profile_income_signal, profile_rating_signal,
    transaction_density

Total = 36 features.
"""

import numpy as np
from typing import Any


# Canonical 36-feature order — must match training exactly
FEATURE_ORDER = [
    # ── core financial (7) ──────────────────────────────────────────────────
    "f_monthly_income",
    "f_income_variance",
    "f_savings_balance",
    "f_months_active",
    "f_income_stability",
    "f_savings_ratio",
    "f_liquidity_buffer",
    # ── transaction behaviour (8) ────────────────────────────────────────────
    "f_total_credits",
    "f_total_debits",
    "f_total_transactions",
    "f_avg_credit_amount",
    "f_avg_debit_amount",
    "f_recurring_ratio",
    "f_net_cashflow",
    "f_credit_debit_ratio",
    # ── profile-specific raw signals (9) ─────────────────────────────────────
    "f_gpa",
    "f_attendance_rate",
    "f_platform_rating",
    "f_avg_weekly_hours",
    "f_business_years",
    "f_avg_daily_revenue",
    "f_land_size_acres",
    "f_subsidy_amount",
    "f_seasonality_index",
    # ── profile one-hot (4) ──────────────────────────────────────────────────
    "f_is_student",
    "f_is_gig",
    "f_is_shopkeeper",
    "f_is_rural",
    # ── engineered cross features (7) ────────────────────────────────────────
    "stability_adjusted_income",
    "income_risk_index",
    "missed_payment_proxy",
    "net_cashflow_ratio",
    "profile_income_signal",
    "profile_rating_signal",
    "transaction_density",
]


def build_feature_vector(
    # ── core financial ────────────────────────────────────────────────────
    f_monthly_income: float = 0.0,
    f_income_variance: float = 0.0,
    f_savings_balance: float = 0.0,
    f_months_active: float = 0.0,
    # ── transaction behaviour ─────────────────────────────────────────────
    f_total_credits: float = 0.0,
    f_total_debits: float = 0.0,
    f_total_transactions: float = 0.0,
    f_avg_credit_amount: float = 0.0,
    f_avg_debit_amount: float = 0.0,
    f_recurring_ratio: float = 0.0,
    # ── profile-specific raw signals ──────────────────────────────────────
    f_gpa: float = 0.0,
    f_attendance_rate: float = 0.0,
    f_platform_rating: float = 0.0,
    f_avg_weekly_hours: float = 0.0,
    f_business_years: float = 0.0,
    f_avg_daily_revenue: float = 0.0,
    f_land_size_acres: float = 0.0,
    f_subsidy_amount: float = 0.0,
    f_seasonality_index: float = 0.0,
    # ── profile one-hot ───────────────────────────────────────────────────
    f_is_student: float = 0.0,
    f_is_gig: float = 0.0,
    f_is_shopkeeper: float = 0.0,
    f_is_rural: float = 0.0,
) -> np.ndarray:
    """
    Build a 1D numpy feature array in fixed order for the model.

    All inputs correspond directly to columns in the `feature_columns` SQL view.
    Derived features (income_stability, savings_ratio, liquidity_buffer,
    net_cashflow, credit_debit_ratio) are computed here from raw DB fields
    when the full view row is not available — otherwise pass them directly.

    Returns:
        np.ndarray: shape (1, 36) float64, same order as FEATURE_ORDER.
    """
    # ── cast inputs ──────────────────────────────────────────────────────────
    f_monthly_income    = float(f_monthly_income)
    f_income_variance   = float(f_income_variance)
    f_savings_balance   = float(f_savings_balance)
    f_months_active     = float(f_months_active)
    f_total_credits     = float(f_total_credits)
    f_total_debits      = float(f_total_debits)
    f_total_transactions = float(f_total_transactions)
    f_avg_credit_amount = float(f_avg_credit_amount)
    f_avg_debit_amount  = float(f_avg_debit_amount)
    f_recurring_ratio   = float(f_recurring_ratio)
    f_gpa               = float(f_gpa)
    f_attendance_rate   = float(f_attendance_rate)
    f_platform_rating   = float(f_platform_rating)
    f_avg_weekly_hours  = float(f_avg_weekly_hours)
    f_business_years    = float(f_business_years)
    f_avg_daily_revenue = float(f_avg_daily_revenue)
    f_land_size_acres   = float(f_land_size_acres)
    f_subsidy_amount    = float(f_subsidy_amount)
    f_seasonality_index = float(f_seasonality_index)
    # one-hot flags — already float from parameter type; no cast needed
    f_is_student        = float(f_is_student)  # noqa: ensure float
    f_is_gig            = float(f_is_gig)
    f_is_shopkeeper     = float(f_is_shopkeeper)
    f_is_rural          = float(f_is_rural)

    # ── derived view columns (mirror SQL view logic) ─────────────────────────
    # Income stability: 1 / (1 + variance)  → higher variance = less stable
    f_income_stability  = 1.0 / (1.0 + f_income_variance)

    # Savings ratio and liquidity buffer (both = savings / income, per view)
    f_savings_ratio     = f_savings_balance / max(f_monthly_income, 1.0)
    f_liquidity_buffer  = f_savings_ratio  # intentionally same as view

    # Net cashflow and credit-to-debit ratio
    f_net_cashflow      = f_total_credits - f_total_debits
    f_credit_debit_ratio = f_total_credits / max(f_total_debits, 1.0)

    # ── engineered cross features ────────────────────────────────────────────
    # Stability-adjusted income (replaces old stability_adjusted_income)
    stability_adjusted_income = f_monthly_income * f_income_stability

    # Income risk index
    income_risk_index = f_monthly_income * (1.0 - f_income_stability)

    # Missed-payment proxy: debit concentration on avg large debits vs credits
    # (real missed_payments column absent in view; proxy via debit/credit gap)
    missed_payment_proxy = max(f_avg_debit_amount - f_avg_credit_amount, 0.0)

    # Net cashflow as ratio of total credits (health of cash position)
    net_cashflow_ratio = f_net_cashflow / max(f_total_credits, 1.0)

    # Profile income signal: whichever profile-specific income proxy is active
    profile_income_signal = (
        f_avg_daily_revenue * f_is_shopkeeper   # shopkeeper daily revenue
        + f_subsidy_amount  * f_is_rural        # rural subsidy
        + f_gpa             * f_is_student      # student academic strength proxy
        + f_platform_rating * f_is_gig          # gig rating as income quality proxy
    )

    # Profile rating/quality signal
    profile_rating_signal = (
        f_platform_rating  * f_is_gig
        + f_gpa            * f_is_student
        + f_attendance_rate * f_is_student
        + f_avg_weekly_hours * f_is_gig
    )

    # Transaction density: transactions per month active
    transaction_density = f_total_transactions / max(f_months_active, 1.0)

    features = np.array(
        [
            # core financial (7)
            f_monthly_income,
            f_income_variance,
            f_savings_balance,
            f_months_active,
            f_income_stability,
            f_savings_ratio,
            f_liquidity_buffer,
            # transaction behaviour (8)
            f_total_credits,
            f_total_debits,
            f_total_transactions,
            f_avg_credit_amount,
            f_avg_debit_amount,
            f_recurring_ratio,
            f_net_cashflow,
            f_credit_debit_ratio,
            # profile-specific raw signals (9)
            f_gpa,
            f_attendance_rate,
            f_platform_rating,
            f_avg_weekly_hours,
            f_business_years,
            f_avg_daily_revenue,
            f_land_size_acres,
            f_subsidy_amount,
            f_seasonality_index,
            # profile one-hot (4)
            f_is_student,
            f_is_gig,
            f_is_shopkeeper,
            f_is_rural,
            # engineered cross features (7)
            stability_adjusted_income,
            income_risk_index,
            missed_payment_proxy,
            net_cashflow_ratio,
            profile_income_signal,
            profile_rating_signal,
            transaction_density,
        ],
        dtype=np.float64,
    )
    return features.reshape(1, -1)


def build_feature_vector_from_record(record: dict[str, Any]) -> np.ndarray:
    """
    Build feature vector from a dict (e.g. request body or DataFrame row).
    All keys match the `f_` prefixed column names from the feature_columns view.
    """
    return build_feature_vector(
        # core financial
        f_monthly_income    =float(record.get("f_monthly_income", 0.0)),
        f_income_variance   =float(record.get("f_income_variance", 0.0)),
        f_savings_balance   =float(record.get("f_savings_balance", 0.0)),
        f_months_active     =float(record.get("f_months_active", 0.0)),
        # transaction behaviour
        f_total_credits     =float(record.get("f_total_credits", 0.0)),
        f_total_debits      =float(record.get("f_total_debits", 0.0)),
        f_total_transactions=float(record.get("f_total_transactions", 0.0)),
        f_avg_credit_amount =float(record.get("f_avg_credit_amount", 0.0)),
        f_avg_debit_amount  =float(record.get("f_avg_debit_amount", 0.0)),
        f_recurring_ratio   =float(record.get("f_recurring_ratio", 0.0)),
        # profile-specific raw signals
        f_gpa               =float(record.get("f_gpa", 0.0)),
        f_attendance_rate   =float(record.get("f_attendance_rate", 0.0)),
        f_platform_rating   =float(record.get("f_platform_rating", 0.0)),
        f_avg_weekly_hours  =float(record.get("f_avg_weekly_hours", 0.0)),
        f_business_years    =float(record.get("f_business_years", 0.0)),
        f_avg_daily_revenue =float(record.get("f_avg_daily_revenue", 0.0)),
        f_land_size_acres   =float(record.get("f_land_size_acres", 0.0)),
        f_subsidy_amount    =float(record.get("f_subsidy_amount", 0.0)),
        f_seasonality_index =float(record.get("f_seasonality_index", 0.0)),
        # profile one-hot
        f_is_student        =float(record.get("f_is_student", 0.0)),
        f_is_gig            =float(record.get("f_is_gig", 0.0)),
        f_is_shopkeeper     =float(record.get("f_is_shopkeeper", 0.0)),
        f_is_rural          =float(record.get("f_is_rural", 0.0)),
    )
