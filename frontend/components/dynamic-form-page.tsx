"use client"

import { useState } from "react"
import { useAppState } from "@/lib/app-context"
import { calculateScore } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Loader2, AlertCircle } from "lucide-react"

function FormField({
  label,
  id,
  type = "text",
  placeholder,
  value,
  onChange,
  readOnly = false,
}: {
  label: string
  id: string
  type?: string
  placeholder?: string
  value: string
  onChange?: (val: string) => void
  readOnly?: boolean
}) {
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id} className="text-sm font-medium text-foreground">
        {label}
      </Label>
      <Input
        id={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        readOnly={readOnly}
        className={`rounded-lg border-border bg-background px-4 py-3 ${
          readOnly ? "cursor-not-allowed opacity-60" : ""
        }`}
      />
    </div>
  )
}

function CheckboxField({
  label,
  id,
  checked,
  onChange,
}: {
  label: string
  id: string
  checked: boolean
  onChange: (val: boolean) => void
}) {
  return (
    <div className="flex items-center gap-3">
      <Checkbox
        id={id}
        checked={checked}
        onCheckedChange={(val) => onChange(val === true)}
      />
      <Label htmlFor={id} className="text-sm font-medium text-foreground cursor-pointer">
        {label}
      </Label>
    </div>
  )
}

const profileLabels: Record<string, string> = {
  student: "Student",
  "gig-worker": "Gig Worker",
  shopkeeper: "Shopkeeper",
  rural: "Rural Individual",
}

export function DynamicFormPage() {
  const { setCurrentPage, formData, setFormData, setCreditScore, setRiskBand, setTopFactors, scoreHistory, setScoreHistory } = useAppState()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const update = (field: string, value: string | boolean) => {
    setFormData({ ...formData, [field]: value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    // Map frontend profile type to API value (backend expects: salaried | student | gig | shopkeeper | rural)
    const profileMap: Record<string, string> = {
      "gig-worker": "gig",
      student: "student",
      shopkeeper: "shopkeeper",
      rural: "rural",
      salaried: "salaried",
    }
    const profile = profileMap[formData.profileType] ?? "salaried"

    const num = (v: string, fallback = 0) => {
      const n = parseFloat(v)
      return Number.isFinite(n) ? n : fallback
    }
    const clamp = (value: number, min: number, max: number) =>
      Math.max(min, Math.min(max, value))

    // Income stability (0–1) → income variance: variance = (1/stability) - 1
    const stability = clamp(num(formData.incomeStability, 0.5), 0.01, 1)
    const income_variance = Math.max(0, (1 / stability) - 1)

    // GPA: form uses Indian 10-point scale → normalise to 0–4 (backend: ge=0, le=4)
    const gpa = clamp((num(formData.gpa) / 10) * 4, 0, 4)
    // Attendance rate: form percentage → 0–1 (backend: ge=0, le=1)
    const attendance_rate = clamp(num(formData.attendanceRate) / 100, 0, 1)
    // Platform rating (backend: ge=0, le=5)
    const platform_rating = clamp(num(formData.platformRating), 0, 5)
    // Seasonality index (backend: ge=0, le=1)
    const seasonality_index = clamp(num(formData.seasonalityIndex), 0, 1)

    // Build payload matching backend ScoreRequest exactly to avoid 422 validation errors
    const payload = {
      profile_type: profile,
      monthly_income: Math.max(0, num(formData.monthlyIncome)),
      income_variance,
      savings_balance: Math.max(0, num(formData.savingsBalance)),
      months_active: Math.max(0, num(formData.monthsActive)),
      total_credits: 0,
      total_debits: 0,
      total_transactions: 0,
      avg_credit_amount: 0,
      avg_debit_amount: 0,
      recurring_ratio: 0,
      gpa: profile === "student" ? gpa : undefined,
      attendance_rate: profile === "student" ? attendance_rate : undefined,
      platform_rating: profile === "gig" ? platform_rating : undefined,
      avg_weekly_hours: profile === "gig" ? Math.max(0, num(formData.avgWeeklyHours)) : undefined,
      business_years: profile === "shopkeeper" ? Math.max(0, num(formData.businessYears)) : undefined,
      avg_daily_revenue: profile === "shopkeeper" ? Math.max(0, num(formData.avgDailyRevenue)) : undefined,
      land_size_acres: profile === "rural" ? Math.max(0, num(formData.landSize)) : undefined,
      subsidy_amount: profile === "rural" ? Math.max(0, num(formData.subsidyAmount)) : undefined,
      seasonality_index: profile === "rural" ? seasonality_index : undefined,
    }

    try {
      const result = await calculateScore(payload)

      setCreditScore(result.alternative_credit_score)
      setRiskBand(result.risk_band)
      setTopFactors(result.top_factors)
      setScoreHistory([
        {
          date: new Date().toISOString().split("T")[0],
          score: result.alternative_credit_score,
          riskBand: result.risk_band,
        },
        ...scoreHistory,
      ])
      setCurrentPage("dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reach the scoring API. Is it running?")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen px-4 pb-20 pt-28">
      <div className="mx-auto max-w-2xl">
        <div className="mb-10">
          <h1 className="font-serif text-3xl font-bold text-foreground md:text-4xl">
            Complete Your Profile
          </h1>
          <p className="mt-3 text-muted-foreground">
            Fill in your details so we can calculate your alternative credit score.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-10">
          {/* Section 1: Personal Information */}
          <section>
            <h2 className="mb-5 text-lg font-semibold text-foreground">
              Personal Information
            </h2>
            <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
              <FormField
                label="Full Name"
                id="fullName"
                placeholder="Enter your full name"
                value={formData.fullName}
                onChange={(val) => update("fullName", val)}
              />
              <FormField
                label="Profile Type"
                id="profileType"
                value={profileLabels[formData.profileType] || ""}
                readOnly
              />
            </div>
          </section>

          {/* Section 2: Financial Information */}
          <section>
            <h2 className="mb-5 text-lg font-semibold text-foreground">
              Financial Information
            </h2>
            <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
              <FormField
                label="Monthly Income (INR)"
                id="monthlyIncome"
                type="number"
                placeholder="e.g. 25000"
                value={formData.monthlyIncome}
                onChange={(val) => update("monthlyIncome", val)}
              />
              <FormField
                label="Income Stability (0-1)"
                id="incomeStability"
                type="number"
                placeholder="e.g. 0.85"
                value={formData.incomeStability}
                onChange={(val) => update("incomeStability", val)}
              />
              <FormField
                label="Savings Balance (INR)"
                id="savingsBalance"
                type="number"
                placeholder="e.g. 50000"
                value={formData.savingsBalance}
                onChange={(val) => update("savingsBalance", val)}
              />
              <FormField
                label="Months Active"
                id="monthsActive"
                type="number"
                placeholder="e.g. 24"
                value={formData.monthsActive}
                onChange={(val) => update("monthsActive", val)}
              />
            </div>
          </section>

          {/* Section 3: Profile-Specific Information */}
          <section>
            <h2 className="mb-5 text-lg font-semibold text-foreground">
              {profileLabels[formData.profileType] || "Profile"} Details
            </h2>
            <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
              {formData.profileType === "student" && (
                <>
                  <FormField
                    label="University Name"
                    id="universityName"
                    placeholder="e.g. IIT Delhi"
                    value={formData.universityName}
                    onChange={(val) => update("universityName", val)}
                  />
                  <FormField
                    label="GPA"
                    id="gpa"
                    type="number"
                    placeholder="e.g. 8.5"
                    value={formData.gpa}
                    onChange={(val) => update("gpa", val)}
                  />
                  <FormField
                    label="Year of Study"
                    id="yearOfStudy"
                    type="number"
                    placeholder="e.g. 3"
                    value={formData.yearOfStudy}
                    onChange={(val) => update("yearOfStudy", val)}
                  />
                  <CheckboxField
                    label="Receiving Scholarship"
                    id="scholarship"
                    checked={formData.scholarship}
                    onChange={(val) => update("scholarship", val)}
                  />
                  <FormField
                    label="Attendance Rate (%)"
                    id="attendanceRate"
                    type="number"
                    placeholder="e.g. 92"
                    value={formData.attendanceRate}
                    onChange={(val) => update("attendanceRate", val)}
                  />
                </>
              )}

              {formData.profileType === "gig-worker" && (
                <>
                  <FormField
                    label="Platform Name"
                    id="platformName"
                    placeholder="e.g. Zomato, Uber"
                    value={formData.platformName}
                    onChange={(val) => update("platformName", val)}
                  />
                  <FormField
                    label="Platform Rating"
                    id="platformRating"
                    type="number"
                    placeholder="e.g. 4.7"
                    value={formData.platformRating}
                    onChange={(val) => update("platformRating", val)}
                  />
                  <FormField
                    label="Average Weekly Hours"
                    id="avgWeeklyHours"
                    type="number"
                    placeholder="e.g. 40"
                    value={formData.avgWeeklyHours}
                    onChange={(val) => update("avgWeeklyHours", val)}
                  />
                </>
              )}

              {formData.profileType === "shopkeeper" && (
                <>
                  <FormField
                    label="Shop Name"
                    id="shopName"
                    placeholder="e.g. Gupta Stores"
                    value={formData.shopName}
                    onChange={(val) => update("shopName", val)}
                  />
                  <FormField
                    label="Business Years"
                    id="businessYears"
                    type="number"
                    placeholder="e.g. 5"
                    value={formData.businessYears}
                    onChange={(val) => update("businessYears", val)}
                  />
                  <CheckboxField
                    label="GST Registered"
                    id="gstRegistered"
                    checked={formData.gstRegistered}
                    onChange={(val) => update("gstRegistered", val)}
                  />
                  <FormField
                    label="Average Daily Revenue (INR)"
                    id="avgDailyRevenue"
                    type="number"
                    placeholder="e.g. 5000"
                    value={formData.avgDailyRevenue}
                    onChange={(val) => update("avgDailyRevenue", val)}
                  />
                </>
              )}

              {formData.profileType === "rural" && (
                <>
                  <FormField
                    label="Occupation"
                    id="occupation"
                    placeholder="e.g. Farmer"
                    value={formData.occupation}
                    onChange={(val) => update("occupation", val)}
                  />
                  <FormField
                    label="Land Size (acres)"
                    id="landSize"
                    type="number"
                    placeholder="e.g. 2.5"
                    value={formData.landSize}
                    onChange={(val) => update("landSize", val)}
                  />
                  <FormField
                    label="Crop Type"
                    id="cropType"
                    placeholder="e.g. Rice, Wheat"
                    value={formData.cropType}
                    onChange={(val) => update("cropType", val)}
                  />
                  <FormField
                    label="Subsidy Amount (INR)"
                    id="subsidyAmount"
                    type="number"
                    placeholder="e.g. 10000"
                    value={formData.subsidyAmount}
                    onChange={(val) => update("subsidyAmount", val)}
                  />
                  <FormField
                    label="Seasonality Index (0-1)"
                    id="seasonalityIndex"
                    type="number"
                    placeholder="e.g. 0.6"
                    value={formData.seasonalityIndex}
                    onChange={(val) => update("seasonalityIndex", val)}
                  />
                </>
              )}
            </div>
          </section>

          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <Button
            type="submit"
            size="lg"
            disabled={isLoading}
            className="w-full rounded-full bg-foreground py-6 text-base font-medium text-background hover:bg-foreground/90 disabled:opacity-70"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                Calculating Score...
              </span>
            ) : (
              "Generate Credit Score"
            )}
          </Button>
        </form>
      </div>
    </main>
  )
}
