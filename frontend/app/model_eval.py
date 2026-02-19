"""
Comprehensive evaluation of the credit scoring model.
Trains a fresh 80/20 split and reports:
  - Overall accuracy, precision, recall, F1, ROC-AUC
  - Calibration (MCE, Brier score)
  - Per-profile breakdown
  - Feature importance (LR coefficients)
  - Comparison: LogReg vs RandomForest baseline
"""
import sys, warnings
sys.path.insert(0, '.')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, brier_score_loss, classification_report,
    confusion_matrix
)

from feature_engineering import FEATURE_ORDER, build_feature_vector_from_record
from train_model import generate_synthetic_data

print("=" * 65)
print("  CREDIT SCORING MODEL — FULL EVALUATION REPORT")
print("=" * 65)

# ── 1. Generate / load data ────────────────────────────────────────
df = generate_synthetic_data(n=3000, seed=42)
PROFILES = ["salaried", "student", "gig", "shopkeeper", "rural"]

# Build feature matrix
records = df.to_dict(orient="records")
X_all = np.vstack([build_feature_vector_from_record(r) for r in records])
y_all = df["defaulted"].values
profiles_all = df["_profile"].values

print(f"\n Dataset: {len(df)} samples, {X_all.shape[1]} features")
print(f" Default rate: {y_all.mean():.1%}")
for p in PROFILES:
    mask = profiles_all == p
    dr = y_all[mask].mean()
    print(f"   {p:<12} n={mask.sum()}  default_rate={dr:.1%}")

# ── 2. Train/test split ────────────────────────────────────────────
X_tr, X_te, y_tr, y_te, p_tr, p_te = train_test_split(
    X_all, y_all, profiles_all, test_size=0.20, random_state=42, stratify=y_all
)

# ── 3. Build and evaluate models ───────────────────────────────────
def evaluate(name, est, X_tr, y_tr, X_te, y_te):
    est.fit(X_tr, y_tr)
    y_pred = est.predict(X_te)
    y_prob = est.predict_proba(X_te)[:, 1]
    acc  = accuracy_score(y_te, y_pred)
    prec = precision_score(y_te, y_pred, zero_division=0)
    rec  = recall_score(y_te, y_pred, zero_division=0)
    f1   = f1_score(y_te, y_pred, zero_division=0)
    auc  = roc_auc_score(y_te, y_prob)
    brier = brier_score_loss(y_te, y_prob)
    # Calibration MCE (max calibration error)
    frac_pos, mean_pred = calibration_curve(y_te, y_prob, n_bins=10, strategy="uniform")
    mce = float(np.max(np.abs(frac_pos - mean_pred)))
    return dict(name=name, acc=acc, prec=prec, rec=rec, f1=f1,
                auc=auc, brier=brier, mce=mce, est=est,
                y_pred=y_pred, y_prob=y_prob)

lr_pipe = CalibratedClassifierCV(
    Pipeline([("scaler", StandardScaler()),
              ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=42))]),
    cv=5
)
rf_pipe = CalibratedClassifierCV(
    RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42),
    cv=5
)
gb_pipe = CalibratedClassifierCV(
    GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42),
    cv=5
)

models = [
    evaluate("LogReg (current)",    lr_pipe, X_tr, y_tr, X_te, y_te),
    evaluate("RandomForest",        rf_pipe, X_tr, y_tr, X_te, y_te),
    evaluate("GradientBoosting",    gb_pipe, X_tr, y_tr, X_te, y_te),
]

# ── 4. Print comparison table ──────────────────────────────────────
print(f"\n{'─'*65}")
print(f"  MODEL COMPARISON (test set, n={len(y_te)})")
print(f"{'─'*65}")
hdr = f"  {'Model':<22} {'Acc':>6} {'Prec':>6} {'Rec':>6} {'F1':>6} {'AUC':>6} {'Brier':>6} {'MCE':>6}"
print(hdr)
print(f"  {'─'*60}")
for m in models:
    row = (f"  {m['name']:<22} "
           f"{m['acc']:>6.3f} {m['prec']:>6.3f} {m['rec']:>6.3f} "
           f"{m['f1']:>6.3f} {m['auc']:>6.3f} {m['brier']:>6.3f} {m['mce']:>6.3f}")
    print(row)

# ── 5. Current model — per-profile breakdown ───────────────────────
lr = models[0]
print(f"\n{'─'*65}")
print("  PER-PROFILE BREAKDOWN — LogReg (current model)")
print(f"{'─'*65}")
print(f"  {'Profile':<12} {'n':>4} {'Acc':>6} {'Rec(def)':>9} {'F1':>6} {'AUC':>6}")
print(f"  {'─'*50}")
for p in PROFILES:
    mask = p_te == p
    if mask.sum() == 0:
        continue
    yp = y_te[mask]; yh = lr["y_pred"][mask]; ypr = lr["y_prob"][mask]
    acc  = accuracy_score(yp, yh)
    rec  = recall_score(yp, yh, zero_division=0)
    f1   = f1_score(yp, yh, zero_division=0)
    auc  = roc_auc_score(yp, ypr) if len(np.unique(yp)) > 1 else float("nan")
    print(f"  {p:<12} {mask.sum():>4} {acc:>6.3f} {rec:>9.3f} {f1:>6.3f} {auc:>6.3f}")

# ── 6. Confusion matrix ────────────────────────────────────────────
print(f"\n  Confusion matrix (LogReg, threshold=0.40):")
cm = confusion_matrix(y_te, lr["y_pred"])
print(f"    TN={cm[0,0]} FP={cm[0,1]}  (non-defaults)")
print(f"    FN={cm[1,0]} TP={cm[1,1]}  (defaults)")
fn_rate = cm[1,0] / (cm[1,0]+cm[1,1])
fp_rate = cm[0,1] / (cm[0,0]+cm[0,1])
print(f"    Miss rate (FN/P)  = {fn_rate:.1%}  ← defaulters we approve (dangerous)")
print(f"    False alarm (FP/N)= {fp_rate:.1%}  ← good borrowers we deny")

# ── 7. Feature importance (LR coefficients) ───────────────────────
print(f"\n{'─'*65}")
print("  TOP 10 MOST IMPACTFUL FEATURES (avg LR coeff magnitude)")
print(f"{'─'*65}")
coef_sum = None
for cc in lr["est"].calibrated_classifiers_:
    c = cc.estimator.named_steps["clf"].coef_[0]
    coef_sum = c if coef_sum is None else coef_sum + c
coef_avg = coef_sum / len(lr["est"].calibrated_classifiers_)
feat_imp = sorted(zip(FEATURE_ORDER, coef_avg), key=lambda x: abs(x[1]), reverse=True)
for feat, coef in feat_imp[:10]:
    direction = "→ raises default risk" if coef > 0 else "→ lowers default risk"
    print(f"  {feat:<32} {coef:>+7.3f}  {direction}")

# ── 8. 5-fold cross-validation AUC ────────────────────────────────
print(f"\n{'─'*65}")
print("  5-FOLD CV AUC (LogReg only, full dataset)")
print(f"{'─'*65}")
lr_cv = Pipeline([("scaler", StandardScaler()),
                   ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=42))])
cv_scores = cross_val_score(lr_cv, X_all, y_all, cv=5, scoring="roc_auc")
print(f"  AUC per fold: {[round(s,3) for s in cv_scores]}")
print(f"  Mean ± std  : {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

print(f"\n{'='*65}")
print("  DONE")
print(f"{'='*65}")
