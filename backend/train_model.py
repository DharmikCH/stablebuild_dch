"""
Train the credit scoring model — supports both real CSV data and synthetic data.
Saves credit_model.pkl.

Features: 36 total — aligned with the `feature_columns` SQL view and FEATURE_ORDER.
  7  core financial  (f_monthly_income … f_liquidity_buffer)
  8  transaction behaviour  (f_total_credits … f_credit_debit_ratio)
  9  profile-specific signals  (f_gpa … f_seasonality_index)
  4  profile one-hot  (f_is_student … f_is_rural)
  7  engineered cross features  (stability_adjusted_income … transaction_density)

Data source:
  - If training_data.csv exists, it is loaded (must have `defaulted` column).
  - Otherwise, synthetic data is generated automatically.

Split: 80% train / 20% test (stratified).
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, roc_auc_score, classification_report,
)

from feature_engineering import FEATURE_ORDER
from model import train_and_save, evaluate_calibration

RANDOM_SEED = 42
N_SAMPLES   = 2000
TEST_SIZE   = 0.20
DATA_PATH   = Path(__file__).resolve().parent / "training_data.csv"

PROFILE_WEIGHTS = {
    "salaried":   0.35,
    "student":    0.20,
    "gig":        0.20,
    "shopkeeper": 0.15,
    "rural":      0.10,
}


def _assign_profiles(n: int, rng: np.random.Generator) -> np.ndarray:
    profiles = list(PROFILE_WEIGHTS.keys())
    weights  = list(PROFILE_WEIGHTS.values())
    return rng.choice(profiles, size=n, p=weights)


def generate_synthetic_data(n: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate synthetic training data that matches the current FEATURE_ORDER (36 features).

    Strategy: label-conditioned generation.
      1. Assign profiles and decide default labels first (based on target rates).
      2. Draw features *conditioned* on the label — defaulters get measurably
         worse financial indicators than repayers.
      3. Compute derived/engineered columns using the same logic as
         build_feature_vector() for train/inference consistency.
    """
    rng            = np.random.default_rng(seed)
    profile_labels = _assign_profiles(n, rng)

    is_student    = (profile_labels == "student").astype(float)
    is_gig        = (profile_labels == "gig").astype(float)
    is_shopkeeper = (profile_labels == "shopkeeper").astype(float)
    is_rural      = (profile_labels == "rural").astype(float)
    is_salaried   = (profile_labels == "salaried").astype(float)

    # ── 1. Decide default labels FIRST (target rates per profile) ──────────────
    # Realistic default rates for India's underbanked segments
    TARGET_DEFAULT_RATE = {
        "salaried":   0.15,
        "student":    0.25,
        "gig":        0.30,
        "shopkeeper": 0.22,
        "rural":      0.28,
    }
    defaulted = np.zeros(n, dtype=int)
    for profile, rate in TARGET_DEFAULT_RATE.items():
        mask = profile_labels == profile
        n_profile = mask.sum()
        defaulted[mask] = (rng.uniform(0, 1, n_profile) < rate).astype(int)

    is_default = defaulted.astype(bool)

    # ── 2. Core financial — conditioned on label ───────────────────────────────
    # Good borrowers: higher income, lower variance, more savings, longer tenure
    # Defaulters: lower income, higher variance, less savings
    f_monthly_income = np.where(
        is_student, 0.0,
        np.where(is_default,
                 rng.uniform(1500, 6000, n),    # defaulters: lower income
                 rng.uniform(4000, 12000, n))   # repayers: higher income
    )
    f_income_variance = np.where(
        is_default,
        rng.uniform(2000, 8000, n),   # defaulters: high variance (unstable)
        rng.uniform(100, 2500, n)     # repayers: low variance (stable)
    )
    f_savings_balance = np.where(
        is_default,
        rng.uniform(0, 10000, n),     # defaulters: low savings
        rng.uniform(5000, 50000, n)   # repayers: healthy savings
    )
    f_months_active = np.where(
        is_default,
        rng.integers(3, 24, n).astype(float),   # defaulters: shorter history
        rng.integers(12, 60, n).astype(float)   # repayers: longer history
    )

    # derived (mirror build_feature_vector logic)
    f_income_stability  = 1.0 / (1.0 + f_income_variance)
    f_savings_ratio     = f_savings_balance / np.maximum(f_monthly_income, 1.0)
    f_liquidity_buffer  = f_savings_ratio   # same as view

    # ── 3. Transaction behaviour — conditioned on label ────────────────────────
    f_total_credits = np.where(
        is_default,
        rng.uniform(1000, 30000, n),    # defaulters: lower credits
        rng.uniform(20000, 80000, n)    # repayers: healthy credits
    )
    f_total_debits = np.where(
        is_default,
        rng.uniform(5000, 40000, n),    # defaulters: debits often exceed credits
        rng.uniform(5000, 50000, n)     # repayers: balanced debits
    )
    f_total_transactions = np.where(
        is_default,
        rng.integers(10, 150, n).astype(float),   # defaulters: fewer transactions
        rng.integers(50, 500, n).astype(float)     # repayers: more active
    )
    f_avg_credit_amount = f_total_credits / np.maximum(f_total_transactions * 0.5, 1.0)
    f_avg_debit_amount  = f_total_debits  / np.maximum(f_total_transactions * 0.5, 1.0)
    f_recurring_ratio = np.where(
        is_default,
        rng.beta(2, 5, n),    # defaulters: fewer recurring payments
        rng.beta(4, 2, n)     # repayers: more regular payments
    )
    f_net_cashflow       = f_total_credits - f_total_debits
    f_credit_debit_ratio = f_total_credits / np.maximum(f_total_debits, 1.0)

    # ── 4. Profile-specific raw signals — conditioned on label ─────────────────
    # Student
    f_gpa = np.where(
        is_student,
        np.where(is_default,
                 rng.uniform(1.5, 2.8, n),    # defaulting students: low GPA
                 rng.uniform(2.8, 4.0, n)),   # repaying students: high GPA
        0.0
    )
    f_attendance_rate = np.where(
        is_student,
        np.where(is_default,
                 rng.beta(2, 4, n),     # defaulters: poor attendance (~0.33)
                 rng.beta(5, 1.5, n)),  # repayers: good attendance (~0.77)
        0.0
    )

    # Gig
    f_platform_rating = np.where(
        is_gig,
        np.where(is_default,
                 rng.uniform(1.0, 3.2, n),    # defaulters: low ratings
                 rng.uniform(3.5, 5.0, n)),   # repayers: high ratings
        0.0
    )
    f_avg_weekly_hours = np.where(
        is_gig,
        np.where(is_default,
                 rng.uniform(10, 25, n),      # defaulters: less hours
                 rng.uniform(25, 60, n)),      # repayers: more hours
        0.0
    )

    # Shopkeeper
    f_business_years = np.where(
        is_shopkeeper,
        np.where(is_default,
                 rng.integers(1, 5, n).astype(float),     # defaulters: new business
                 rng.integers(3, 20, n).astype(float)),   # repayers: established
        0.0
    )
    f_avg_daily_revenue = np.where(
        is_shopkeeper,
        np.where(is_default,
                 rng.uniform(500, 5000, n),     # defaulters: low revenue
                 rng.uniform(4000, 15000, n)),  # repayers: good revenue
        0.0
    )

    # Rural
    f_land_size_acres = np.where(
        is_rural,
        np.where(is_default,
                 rng.uniform(0.5, 3.0, n),    # defaulters: small holdings
                 rng.uniform(2.0, 10.0, n)),  # repayers: larger holdings
        0.0
    )
    f_subsidy_amount = np.where(
        is_rural,
        np.where(is_default,
                 rng.uniform(0, 1500, n),     # defaulters: little subsidy
                 rng.uniform(1000, 5000, n)), # repayers: more subsidy
        0.0
    )
    f_seasonality_index = np.where(
        is_rural,
        np.where(is_default,
                 rng.beta(2, 5, n),    # defaulters: volatile seasons
                 rng.beta(5, 2, n)),   # repayers: stable seasons
        0.0
    )

    # ── 5. Engineered cross features ──────────────────────────────────────────
    stability_adjusted_income = f_monthly_income * f_income_stability
    income_risk_index         = f_monthly_income * (1.0 - f_income_stability)
    missed_payment_proxy      = np.maximum(f_avg_debit_amount - f_avg_credit_amount, 0.0)
    net_cashflow_ratio        = f_net_cashflow / np.maximum(f_total_credits, 1.0)

    profile_income_signal = (
        f_avg_daily_revenue * is_shopkeeper
        + f_subsidy_amount  * is_rural
        + f_gpa             * is_student
        + f_platform_rating * is_gig
    )
    profile_rating_signal = (
        f_platform_rating   * is_gig
        + f_gpa             * is_student
        + f_attendance_rate * is_student
        + f_avg_weekly_hours * is_gig
    )
    transaction_density = f_total_transactions / np.maximum(f_months_active, 1.0)

    df = pd.DataFrame({
        # core financial (7)
        "f_monthly_income":           f_monthly_income,
        "f_income_variance":          f_income_variance,
        "f_savings_balance":          f_savings_balance,
        "f_months_active":            f_months_active,
        "f_income_stability":         f_income_stability,
        "f_savings_ratio":            f_savings_ratio,
        "f_liquidity_buffer":         f_liquidity_buffer,
        # transaction behaviour (8)
        "f_total_credits":            f_total_credits,
        "f_total_debits":             f_total_debits,
        "f_total_transactions":       f_total_transactions,
        "f_avg_credit_amount":        f_avg_credit_amount,
        "f_avg_debit_amount":         f_avg_debit_amount,
        "f_recurring_ratio":          f_recurring_ratio,
        "f_net_cashflow":             f_net_cashflow,
        "f_credit_debit_ratio":       f_credit_debit_ratio,
        # profile-specific raw signals (9)
        "f_gpa":                      f_gpa,
        "f_attendance_rate":          f_attendance_rate,
        "f_platform_rating":          f_platform_rating,
        "f_avg_weekly_hours":         f_avg_weekly_hours,
        "f_business_years":           f_business_years,
        "f_avg_daily_revenue":        f_avg_daily_revenue,
        "f_land_size_acres":          f_land_size_acres,
        "f_subsidy_amount":           f_subsidy_amount,
        "f_seasonality_index":        f_seasonality_index,
        # profile one-hot (4)
        "f_is_student":               is_student,
        "f_is_gig":                   is_gig,
        "f_is_shopkeeper":            is_shopkeeper,
        "f_is_rural":                 is_rural,
        # engineered cross features (7)
        "stability_adjusted_income":  stability_adjusted_income,
        "income_risk_index":          income_risk_index,
        "missed_payment_proxy":       missed_payment_proxy,
        "net_cashflow_ratio":         net_cashflow_ratio,
        "profile_income_signal":      profile_income_signal,
        "profile_rating_signal":      profile_rating_signal,
        "transaction_density":        transaction_density,
        # label + profile tag
        "defaulted":                  defaulted,
        "_profile":                   profile_labels,
    })
    return df


def evaluate_split(model, X, y, label: str) -> dict:
    preds = model.predict(X)
    proba = model.predict_proba(X)[:, 1]
    return {
        "label":     label,
        "n":         len(y),
        "accuracy":  round(accuracy_score(y, preds), 4),
        "precision": round(precision_score(y, preds, zero_division=0), 4),
        "recall":    round(recall_score(y, preds, zero_division=0), 4),
        "f1":        round(f1_score(y, preds, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y, proba), 4),
    }


def main() -> None:
    if DATA_PATH.exists():
        print(f"Loading training data from {DATA_PATH} ...")
        df = pd.read_csv(DATA_PATH)
        print(f"Loaded {len(df)} rows from CSV")
    else:
        print(f"{DATA_PATH} not found — generating {N_SAMPLES} synthetic samples ...")
        df = generate_synthetic_data(n=N_SAMPLES, seed=RANDOM_SEED)
        df.to_csv(DATA_PATH, index=False)
        print(f"Synthetic data saved to {DATA_PATH}")

    print(f"Class balance — defaulted: {df['defaulted'].mean():.2%}")

    X = df[FEATURE_ORDER].values.astype(np.float64)
    y = df["defaulted"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    print(f"Split: {len(X_train)} train / {len(X_test)} test  (80/20, stratified)")

    print("Training StandardScaler + LogisticRegression pipeline...")
    model, _, path = train_and_save(X_train, y_train)
    print(f"Model saved -> {path}\n")

    print("=" * 58)
    print("  PERFORMANCE METRICS")
    print("=" * 58)
    for split in [
        evaluate_split(model, X_train, y_train, "Train"),
        evaluate_split(model, X_test,  y_test,  "Test "),
    ]:
        print(f"\n  [{split['label']}]  n={split['n']}")
        print(f"    Accuracy  : {split['accuracy']:.4f}")
        print(f"    Precision : {split['precision']:.4f}")
        print(f"    Recall    : {split['recall']:.4f}")
        print(f"    F1        : {split['f1']:.4f}")
        print(f"    ROC-AUC   : {split['roc_auc']:.4f}")

    print("\n  [Test — Classification Report]")
    print(classification_report(
        y_test, model.predict(X_test),
        target_names=["Repaid (0)", "Default (1)"]
    ))

    # Per-profile metrics on test set
    df_test = df.iloc[
        train_test_split(range(len(df)), test_size=TEST_SIZE,
                         random_state=RANDOM_SEED, stratify=y)[1]
    ]
    print("  [Per-Profile Test Metrics]")
    print(f"  {'Profile':<13} {'Acc':>6}  {'F1':>6}  {'n':>5}")
    print(f"  {'-'*35}")
    for name in ["salaried", "student", "gig", "shopkeeper", "rural"]:
        mask = df_test["_profile"] == name
        if mask.sum() == 0:
            continue
        Xi = df_test.loc[mask, FEATURE_ORDER].values.astype(np.float64)
        yi = df_test.loc[mask, "defaulted"].values
        pi = model.predict(Xi)
        acc = accuracy_score(yi, pi)
        f1  = f1_score(yi, pi, zero_division=0)
        print(f"  {name:<13} {acc:>6.4f}  {f1:>6.4f}  {mask.sum():>5}")

    print("=" * 58)

    # Calibration curve on test set
    frac_pos, mean_prob = evaluate_calibration(model, X_test, y_test, n_bins=10)
    mce = float(np.mean(np.abs(frac_pos - mean_prob)))
    print(f"\n  [Calibration Curve — Test Set]  (MCE = {mce:.4f})")
    print(f"  {'Mean P(default)':>16}  {'Actual rate':>12}")
    for mp, fp in zip(mean_prob, frac_pos):
        bar = "#" * int(fp * 20)
        print(f"  {mp:>16.3f}  {fp:>12.3f}  |{bar}")
    print("  MCE (mean |predicted - actual|):", round(mce, 4))
    print("  (Perfect calibration = 0.0; random = ~0.25)")
    print("=" * 58)


if __name__ == "__main__":
    main()
