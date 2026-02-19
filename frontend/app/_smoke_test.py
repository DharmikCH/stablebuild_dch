"""Smoke test for the new main.py v6.0.0 features."""
import sys
sys.path.insert(0, '.')

import main as m

# Routes
routes = [r.path for r in m.app.routes]
assert '/score'       in routes, 'missing /score'
assert '/score/batch' in routes, 'missing /score/batch'
assert '/predict'     in routes, 'missing /predict'
assert '/health'      in routes, 'missing /health'
print('Routes:', routes)
print('CORS origins:', m.ALLOWED_ORIGINS)
print('Version:', m.app.version)

from feature_engineering import build_feature_vector_from_record
from model import load_model, DEFAULT_MODEL_PATH

model = load_model(DEFAULT_MODEL_PATH)

BASE = {k: 0.0 for k in [
    'f_monthly_income','f_income_variance','f_savings_balance','f_months_active',
    'f_total_credits','f_total_debits','f_total_transactions',
    'f_avg_credit_amount','f_avg_debit_amount','f_recurring_ratio',
    'f_gpa','f_attendance_rate','f_platform_rating','f_avg_weekly_hours',
    'f_business_years','f_avg_daily_revenue','f_land_size_acres',
    'f_subsidy_amount','f_seasonality_index',
    'f_is_student','f_is_gig','f_is_shopkeeper','f_is_rural',
]}

def quick_score(profile, **kwargs):
    rec = dict(BASE)
    rec.update(kwargs)
    X = build_feature_vector_from_record(rec)
    return m._make_response(model, X, profile)

# salaried
r = quick_score('salaried',
                f_monthly_income=8000, f_income_variance=200,
                f_savings_balance=15000, f_months_active=24,
                f_total_credits=50000, f_total_debits=35000,
                f_total_transactions=120, f_recurring_ratio=0.4)
print("Salaried -> score={} band={} factors={}".format(
    r['alternative_credit_score'], r['risk_band'], len(r['top_factors'])))
assert len(r['top_factors']) == 5

# student
r = quick_score('student',
                f_gpa=3.7, f_attendance_rate=0.9,
                f_savings_balance=5000, f_total_credits=10000,
                f_total_debits=8000, f_total_transactions=40,
                f_months_active=12, f_is_student=1.0)
print("Student   -> score={} band={} factors={}".format(
    r['alternative_credit_score'], r['risk_band'], len(r['top_factors'])))

# gig
r = quick_score('gig',
                f_platform_rating=4.2, f_avg_weekly_hours=35,
                f_savings_balance=12000, f_total_credits=45000,
                f_total_debits=30000, f_total_transactions=200,
                f_months_active=18, f_recurring_ratio=0.3, f_is_gig=1.0)
print("Gig       -> score={} band={} factors={}".format(
    r['alternative_credit_score'], r['risk_band'], len(r['top_factors'])))

# Verify top_factors structure
for f in r['top_factors']:
    assert 'label' in f
    assert f['direction'] in ('positive', 'negative')
    assert f['impact'] >= 0

print("\nAll checks passed.")
