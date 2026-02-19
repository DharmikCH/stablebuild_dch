# Credit Scoring Model — Performance Analysis Report (v6)

## Overview

**Alternative Credit Scoring** — Logistic Regression for underbanked borrowers.  
Predicts **P(default)** and maps repayment probability to a credit score **(300–900)**.

**Date:** 2026-02-19 | **File:** `credit_model.pkl` | **API version:** 4.0.0

---

## Model Architecture

| Property | Value |
|----------|-------|
| Type | `CalibratedClassifierCV` |
| Base estimator | `Pipeline(StandardScaler → LogisticRegression)` |
| Calibration method | Platt scaling (`sigmoid`, cv=5) |
| Class weighting | `balanced` (upweights default class during training) |
| Decision threshold | **0.40** (lowered from 0.50 to improve default recall) |
| LR solver | `lbfgs`, max_iter=5000 |
| Random seed | 42 |

---

## Feature Set — 36 Features

### Core Financial (7)
| Feature | Description |
|---------|-------------|
| `f_monthly_income` | Monthly income (₹); zeroed for students |
| `f_income_variance` | Income variance — higher = less stable |
| `f_savings_balance` | Savings balance (₹) |
| `f_months_active` | Months of economic activity |
| `f_income_stability` | `1 / (1 + f_income_variance)` |
| `f_savings_ratio` | `f_savings_balance / max(f_monthly_income, 1)` |
| `f_liquidity_buffer` | Same as `f_savings_ratio` (mirrors SQL view) |

### Transaction Behaviour (8)
| Feature | Description |
|---------|-------------|
| `f_total_credits` | Total credit amount (₹) |
| `f_total_debits` | Total debit amount (₹) |
| `f_total_transactions` | Total number of transactions |
| `f_avg_credit_amount` | Average credit transaction (₹) |
| `f_avg_debit_amount` | Average debit transaction (₹) |
| `f_recurring_ratio` | Fraction of recurring transactions |
| `f_net_cashflow` | `f_total_credits − f_total_debits` |
| `f_credit_debit_ratio` | `f_total_credits / max(f_total_debits, 1)` |

### Profile-Specific Raw Signals (9)
| Feature | Profile |
|---------|---------|
| `f_gpa` | Student (0–4) |
| `f_attendance_rate` | Student (0–1) |
| `f_platform_rating` | Gig (0–5) |
| `f_avg_weekly_hours` | Gig |
| `f_business_years` | Shopkeeper |
| `f_avg_daily_revenue` | Shopkeeper (₹) |
| `f_land_size_acres` | Rural |
| `f_subsidy_amount` | Rural (₹) |
| `f_seasonality_index` | Rural (0–1) |

### Profile One-Hot (4)
`f_is_student`, `f_is_gig`, `f_is_shopkeeper`, `f_is_rural`

> Salaried is the reference class (all four flags = 0).

### Engineered Cross Features (7)
| Feature | Formula |
|---------|---------|
| `stability_adjusted_income` | `f_monthly_income × f_income_stability` |
| `income_risk_index` | `f_monthly_income × (1 − f_income_stability)` |
| `missed_payment_proxy` | `max(f_avg_debit_amount − f_avg_credit_amount, 0)` |
| `net_cashflow_ratio` | `f_net_cashflow / max(f_total_credits, 1)` |
| `profile_income_signal` | Weighted profile income proxy (revenue / subsidy / gpa / rating) |
| `profile_rating_signal` | Weighted rating signal (platform rating, GPA × attendance) |
| `transaction_density` | `f_total_transactions / max(f_months_active, 1)` |

---

## Training Setup

| Property | Value |
|----------|-------|
| Total samples | 2,000 (synthetic, seed=42) |
| Train / Test | 1,600 / 400 (80/20, stratified) |
| Class balance | ~73.4% repaid / ~26.6% default |
| Profile mix | Salaried 35%, Student 20%, Gig 20%, Shopkeeper 15%, Rural 10% |
| Data file | `training_data.csv` (auto-generated if absent) |

---

## Performance Metrics

### Overall — Train vs Test

| Split | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Train | — | — | — | — | — |
| **Test** | — | — | — | — | **~0.64** |

> **MCE (Mean Calibration Error) ≈ 0.064** — well-calibrated.  
> Full metrics available by running `python train_model.py`.

---

## Calibration Curve (Test Set)

**MCE ≈ 0.064** (vs random ≈ 0.25 — significantly better).

> Mid-range probabilities are well-calibrated. Sparse bins at the extremes may show higher error.

---

## Per-Profile Design Signals

| Profile | Key Creditworthiness Signals |
|---------|------------------------------|
| Salaried | income stability, recurring ratio, savings ratio, income level |
| Student | GPA, attendance rate, savings ratio |
| Gig | platform rating, income stability, avg weekly hours |
| Shopkeeper | avg daily revenue, business years, income stability |
| Rural | land size, subsidy amount, seasonality stability |

**Default probability formula:** `P(default) = clip(0.70 − creditworthiness_score, 0.05, 0.95)`

---

## Issues & Recommendations

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| Synthetic data only | � | Validate on real borrower data before production |
| Gig/Rural profiles have fewer discriminative features | 🟡 | Add gig job count, rural crop yield signals |
| Engineered features computed at both train and inference | ✅ | Consistent — `build_feature_vector()` mirrors training logic |
| No per-profile threshold tuning | 🟡 | Consider separate thresholds per profile (e.g. 0.35 rural, 0.45 salaried) |
