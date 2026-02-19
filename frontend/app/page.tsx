"use client"

import { AppProvider, useAppState } from "@/lib/app-context"
import { Navbar } from "@/components/navbar"
import { LandingPage } from "@/components/landing-page"
import { AuthPage } from "@/components/auth-page"
import { ProfileSelectionPage } from "@/components/profile-selection-page"
import { DynamicFormPage } from "@/components/dynamic-form-page"
import { DashboardPage } from "@/components/dashboard-page"
import { SettingsPage } from "@/components/settings-page"

function PageRouter() {
  const { currentPage } = useAppState()

  switch (currentPage) {
    case "auth":
      return <AuthPage />
    case "profile-select":
      return <ProfileSelectionPage />
    case "form":
      return <DynamicFormPage />
    case "dashboard":
      return <DashboardPage />
    case "settings":
      return <SettingsPage />
    default:
      return <LandingPage />
  }
}

export default function Home() {
  return (
    <AppProvider>
      <Navbar />
      <PageRouter />
    </AppProvider>
  )
}
