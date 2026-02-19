"use client"

import { useState } from "react"
import { useAppState } from "@/lib/app-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Loader2 } from "lucide-react"

function SettingsField({
  label,
  id,
  type = "text",
  placeholder,
  value,
  onChange,
}: {
  label: string
  id: string
  type?: string
  placeholder?: string
  value: string
  onChange: (val: string) => void
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
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border-border bg-background px-4 py-3"
      />
    </div>
  )
}

function SettingsCheckbox({
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

export function SettingsPage() {
  const { formData, setFormData, setCurrentPage, setCreditScore, setRiskBand, scoreHistory, setScoreHistory } = useAppState()
  const [isSaving, setIsSaving] = useState(false)

  const update = (field: string, value: string | boolean) => {
    setFormData({ ...formData, [field]: value })
  }

  const handleSave = () => {
    setIsSaving(true)
    setTimeout(() => {
      const score = Math.floor(Math.random() * 200) + 600
      let band: "Low" | "Medium" | "High"
      if (score >= 720) band = "Low"
      else if (score >= 650) band = "Medium"
      else band = "High"

      setCreditScore(score)
      setRiskBand(band)
      setScoreHistory([
        {
          date: new Date().toISOString().split("T")[0],
          score,
          riskBand: band,
        },
        ...scoreHistory,
      ])
      setIsSaving(false)
      setCurrentPage("dashboard")
    }, 2500)
  }

  return (
    <main className="min-h-screen px-4 pb-20 pt-28">
      <div className="mx-auto max-w-2xl">
        <div className="mb-10">
          <h1 className="font-serif text-3xl font-bold text-foreground md:text-4xl">
            Account Settings
          </h1>
          <p className="mt-3 text-muted-foreground">
            Update your profile details. Saving will recalculate your credit score.
          </p>
        </div>

        <div className="flex flex-col gap-10">
          {/* Personal Info */}
          <section>
            <h2 className="mb-5 text-lg font-semibold text-foreground">
              Personal Information
            </h2>
            <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
              <SettingsField
                label="Full Name"
                id="settings-fullName"
                placeholder="Enter your full name"
                value={formData.fullName}
                onChange={(val) => update("fullName", val)}
              />
              <div className="flex flex-col gap-2">
                <Label className="text-sm font-medium text-foreground">Profile Type</Label>
                <Input
                  value={profileLabels[formData.profileType] || ""}
                  readOnly
                  className="cursor-not-allowed rounded-lg border-border bg-background px-4 py-3 opacity-60"
                />
              </div>
            </div>
          </section>

          {/* Financial Info */}
          <section>
            <h2 className="mb-5 text-lg font-semibold text-foreground">
              Financial Information
            </h2>
            <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
              <SettingsField
                label="Monthly Income (INR)"
                id="settings-monthlyIncome"
                type="number"
                placeholder="e.g. 25000"
                value={formData.monthlyIncome}
                onChange={(val) => update("monthlyIncome", val)}
              />
              <SettingsField
                label="Income Stability (0-1)"
                id="settings-incomeStability"
                type="number"
                placeholder="e.g. 0.85"
                value={formData.incomeStability}
                onChange={(val) => update("incomeStability", val)}
              />
              <SettingsField
                label="Savings Balance (INR)"
                id="settings-savingsBalance"
                type="number"
                placeholder="e.g. 50000"
                value={formData.savingsBalance}
                onChange={(val) => update("savingsBalance", val)}
              />
              <SettingsField
                label="Months Active"
                id="settings-monthsActive"
                type="number"
                placeholder="e.g. 24"
                value={formData.monthsActive}
                onChange={(val) => update("monthsActive", val)}
              />
            </div>
          </section>

          {/* Profile-Specific Info */}
          <section>
            <h2 className="mb-5 text-lg font-semibold text-foreground">
              {profileLabels[formData.profileType] || "Profile"} Details
            </h2>
            <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
              {formData.profileType === "student" && (
                <>
                  <SettingsField
                    label="University Name"
                    id="settings-universityName"
                    placeholder="e.g. IIT Delhi"
                    value={formData.universityName}
                    onChange={(val) => update("universityName", val)}
                  />
                  <SettingsField
                    label="GPA"
                    id="settings-gpa"
                    type="number"
                    placeholder="e.g. 8.5"
                    value={formData.gpa}
                    onChange={(val) => update("gpa", val)}
                  />
                  <SettingsField
                    label="Year of Study"
                    id="settings-yearOfStudy"
                    type="number"
                    placeholder="e.g. 3"
                    value={formData.yearOfStudy}
                    onChange={(val) => update("yearOfStudy", val)}
                  />
                  <SettingsCheckbox
                    label="Receiving Scholarship"
                    id="settings-scholarship"
                    checked={formData.scholarship}
                    onChange={(val) => update("scholarship", val)}
                  />
                  <SettingsField
                    label="Attendance Rate (%)"
                    id="settings-attendanceRate"
                    type="number"
                    placeholder="e.g. 92"
                    value={formData.attendanceRate}
                    onChange={(val) => update("attendanceRate", val)}
                  />
                </>
              )}

              {formData.profileType === "gig-worker" && (
                <>
                  <SettingsField
                    label="Platform Name"
                    id="settings-platformName"
                    placeholder="e.g. Zomato, Uber"
                    value={formData.platformName}
                    onChange={(val) => update("platformName", val)}
                  />
                  <SettingsField
                    label="Platform Rating"
                    id="settings-platformRating"
                    type="number"
                    placeholder="e.g. 4.7"
                    value={formData.platformRating}
                    onChange={(val) => update("platformRating", val)}
                  />
                  <SettingsField
                    label="Average Weekly Hours"
                    id="settings-avgWeeklyHours"
                    type="number"
                    placeholder="e.g. 40"
                    value={formData.avgWeeklyHours}
                    onChange={(val) => update("avgWeeklyHours", val)}
                  />
                </>
              )}

              {formData.profileType === "shopkeeper" && (
                <>
                  <SettingsField
                    label="Shop Name"
                    id="settings-shopName"
                    placeholder="e.g. Gupta Stores"
                    value={formData.shopName}
                    onChange={(val) => update("shopName", val)}
                  />
                  <SettingsField
                    label="Business Years"
                    id="settings-businessYears"
                    type="number"
                    placeholder="e.g. 5"
                    value={formData.businessYears}
                    onChange={(val) => update("businessYears", val)}
                  />
                  <SettingsCheckbox
                    label="GST Registered"
                    id="settings-gstRegistered"
                    checked={formData.gstRegistered}
                    onChange={(val) => update("gstRegistered", val)}
                  />
                  <SettingsField
                    label="Average Daily Revenue (INR)"
                    id="settings-avgDailyRevenue"
                    type="number"
                    placeholder="e.g. 5000"
                    value={formData.avgDailyRevenue}
                    onChange={(val) => update("avgDailyRevenue", val)}
                  />
                </>
              )}

              {formData.profileType === "rural" && (
                <>
                  <SettingsField
                    label="Occupation"
                    id="settings-occupation"
                    placeholder="e.g. Farmer"
                    value={formData.occupation}
                    onChange={(val) => update("occupation", val)}
                  />
                  <SettingsField
                    label="Land Size (acres)"
                    id="settings-landSize"
                    type="number"
                    placeholder="e.g. 2.5"
                    value={formData.landSize}
                    onChange={(val) => update("landSize", val)}
                  />
                  <SettingsField
                    label="Crop Type"
                    id="settings-cropType"
                    placeholder="e.g. Rice, Wheat"
                    value={formData.cropType}
                    onChange={(val) => update("cropType", val)}
                  />
                  <SettingsField
                    label="Subsidy Amount (INR)"
                    id="settings-subsidyAmount"
                    type="number"
                    placeholder="e.g. 10000"
                    value={formData.subsidyAmount}
                    onChange={(val) => update("subsidyAmount", val)}
                  />
                  <SettingsField
                    label="Seasonality Index (0-1)"
                    id="settings-seasonalityIndex"
                    type="number"
                    placeholder="e.g. 0.6"
                    value={formData.seasonalityIndex}
                    onChange={(val) => update("seasonalityIndex", val)}
                  />
                </>
              )}
            </div>
          </section>

          {/* Actions */}
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <Button
              variant="outline"
              className="rounded-full px-8"
              onClick={() => setCurrentPage("dashboard")}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              className="rounded-full bg-foreground px-8 text-background hover:bg-foreground/90 disabled:opacity-70"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {"Updating & Recalculating Score..."}
                </span>
              ) : (
                "Save Changes"
              )}
            </Button>
          </div>
        </div>
      </div>
    </main>
  )
}
