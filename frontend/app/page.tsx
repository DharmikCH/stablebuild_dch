"use client"

import { useEffect } from "react"
import { AppProvider, useAppState } from "@/lib/app-context"
import { Navbar } from "@/components/navbar"
import { LandingPage } from "@/components/landing-page"
import { AuthPage } from "@/components/auth-page"
import { ProfileSelectionPage } from "@/components/profile-selection-page"
import { DynamicFormPage } from "@/components/dynamic-form-page"
import { DashboardPage } from "@/components/dashboard-page"
import { SettingsPage } from "@/components/settings-page"

const PROTECTED_PAGES = ["profile-select", "form", "dashboard", "settings"]

function PageRouter() {
  const { currentPage, isLoggedIn, setCurrentPage } = useAppState()

  // Redirect to auth if not logged in and landing on a protected page
  useEffect(() => {
    if (!isLoggedIn && PROTECTED_PAGES.includes(currentPage)) {
      setCurrentPage("auth")
    }
  }, [isLoggedIn, currentPage, setCurrentPage])

  // Don't render protected pages when not logged in (avoid flash before redirect)
  if (!isLoggedIn && PROTECTED_PAGES.includes(currentPage)) {
    return <AuthPage />
  }

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
