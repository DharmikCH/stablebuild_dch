"use client"

import { useAppState } from "@/lib/app-context"
import { GraduationCap, Briefcase, Store, Wheat } from "lucide-react"

const profiles = [
  {
    id: "student" as const,
    icon: GraduationCap,
    title: "Student",
    description: "University or college student building credit for the first time.",
  },
  {
    id: "gig-worker" as const,
    icon: Briefcase,
    title: "Gig Worker",
    description: "Freelancer or platform-based worker with variable income streams.",
  },
  {
    id: "shopkeeper" as const,
    icon: Store,
    title: "Shopkeeper",
    description: "Small business owner running a local shop or retail business.",
  },
  {
    id: "rural" as const,
    icon: Wheat,
    title: "Rural Individual",
    description: "Farmer or rural worker with agriculture-based income.",
  },
]

export function ProfileSelectionPage() {
  const { setCurrentPage, formData, setFormData } = useAppState()

  const handleSelect = (profileType: typeof profiles[number]["id"]) => {
    setFormData({ ...formData, profileType })
    setCurrentPage("form")
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 pt-20">
      <div className="w-full max-w-2xl">
        <div className="mb-10 text-center">
          <h1 className="font-serif text-3xl font-bold text-foreground md:text-4xl">
            Select Your Profile Type
          </h1>
          <p className="mt-3 text-muted-foreground">
            Choose the category that best describes your financial profile.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {profiles.map((profile) => (
            <button
              key={profile.id}
              onClick={() => handleSelect(profile.id)}
              className="group flex flex-col items-start rounded-2xl border border-border bg-card p-6 text-left transition-all hover:border-primary/30 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 transition-colors group-hover:bg-primary/20">
                <profile.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">
                {profile.title}
              </h3>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                {profile.description}
              </p>
            </button>
          ))}
        </div>
      </div>
    </main>
  )
}
