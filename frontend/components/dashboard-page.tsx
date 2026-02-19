"use client"

import { useState, useEffect } from "react"
import { useAppState } from "@/lib/app-context"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { TrendingUp, Wallet, Clock, Settings, ArrowUp, ArrowDown } from "lucide-react"

function ScoreSkeleton() {
  return (
    <div className="flex flex-col items-center gap-4">
      <Skeleton className="h-6 w-48" />
      <Skeleton className="h-32 w-32 rounded-full" />
      <Skeleton className="h-6 w-24" />
      <Skeleton className="h-4 w-36" />
    </div>
  )
}

export function DashboardPage() {
  const { userName, creditScore, riskBand, topFactors, formData, scoreHistory, setCurrentPage } = useAppState()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 800)
    return () => clearTimeout(timer)
  }, [])

  const bandColor =
    riskBand === "Low"
      ? "bg-emerald-100 text-emerald-800"
      : riskBand === "Medium"
        ? "bg-amber-100 text-amber-800"
        : "bg-red-100 text-red-800"

  const stability = parseFloat(formData.incomeStability) || null
  const savingsBalance = parseFloat(formData.savingsBalance) || null
  const monthsActive = parseFloat(formData.monthsActive) || null

  const stats = [
    {
      icon: TrendingUp,
      label: "Income Stability",
      value: stability != null ? `${Math.round(stability * 100)}%` : "---",
    },
    {
      icon: Wallet,
      label: "Savings Balance",
      value: savingsBalance != null ? `₹${savingsBalance.toLocaleString("en-IN")}` : "---",
    },
    {
      icon: Clock,
      label: "Economic Activity",
      value: monthsActive != null ? `${monthsActive} mo` : "---",
    },
  ]

  return (
    <main className="min-h-screen px-4 pb-20 pt-28">
      <div className="mx-auto max-w-3xl">
        {/* Top Bar */}
        <div className="mb-10 flex items-center justify-between">
          <div>
            <h1 className="font-serif text-2xl font-bold text-foreground md:text-3xl">
              Welcome back, {userName}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Here is your credit score overview.
            </p>
          </div>
        </div>

        {/* Main Score Display */}
        <div className="mb-8 rounded-2xl border border-border bg-card p-10 text-center shadow-sm">
          {isLoading ? (
            <ScoreSkeleton />
          ) : (
            <>
              <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
                Your Alternative Credit Score
              </p>
              <div className="mt-6 flex items-center justify-center">
                <div className="flex h-40 w-40 items-center justify-center rounded-full border-4 border-primary/20 bg-primary/5">
                  <span className="font-serif text-6xl font-bold text-foreground">
                    {creditScore ?? "---"}
                  </span>
                </div>
              </div>
              {riskBand && (
                <div className="mt-6">
                  <Badge className={`rounded-full px-4 py-1 text-sm font-medium ${bandColor}`}>
                    {riskBand} Risk
                  </Badge>
                </div>
              )}
            </>
          )}
        </div>

        {/* Stat Cards */}
        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-2xl border border-border bg-card p-6 shadow-sm"
            >
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                <stat.icon className="h-5 w-5 text-primary" />
              </div>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
              <div className="mt-1">
                {isLoading ? (
                  <Skeleton className="h-6 w-20" />
                ) : (
                  <p className="text-lg font-semibold text-foreground">{stat.value}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Top Factors */}
        {!isLoading && topFactors.length > 0 && (
          <div className="mb-8 rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-foreground">
              What drives your score
            </h2>
            <div className="flex flex-col gap-3">
              {topFactors.map((factor, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-xl bg-secondary/50 px-4 py-3"
                >
                  <span className="text-sm text-foreground">{factor.label}</span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-medium ${
                        factor.direction === "positive"
                          ? "text-emerald-600"
                          : "text-red-500"
                      }`}
                    >
                      {factor.direction === "positive" ? "▲ Helps" : "▼ Hurts"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="mb-8">
          <Button
            variant="outline"
            className="w-full rounded-xl"
            onClick={() => setCurrentPage("settings")}
          >
            <Settings className="mr-2 h-4 w-4" />
            Edit Account Settings
          </Button>
        </div>

        {/* Score History */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            Score History
          </h2>
          {isLoading ? (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : scoreHistory.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground">
              No score history available yet.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {scoreHistory.slice(0, 5).map((entry, index) => {
                const entryBandColor =
                  entry.riskBand === "Low"
                    ? "bg-emerald-100 text-emerald-800"
                    : entry.riskBand === "Medium"
                      ? "bg-amber-100 text-amber-800"
                      : "bg-red-100 text-red-800"
                return (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-xl bg-secondary/50 px-5 py-3"
                  >
                    <span className="text-sm text-muted-foreground">{entry.date}</span>
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-foreground">{entry.score}</span>
                      <Badge className={`rounded-full px-3 py-0.5 text-xs font-medium ${entryBandColor}`}>
                        {entry.riskBand}
                      </Badge>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
