"use client";

import { useAppState } from "@/lib/app-context";
import { Button } from "@/components/ui/button";
import { Shield, Brain, Users } from "lucide-react";

const features = [
  {
    icon: Shield,
    title: "Inclusive Scoring",
    description:
      "Credit scoring that goes beyond traditional metrics, assessing real-world financial behavior for every Indian.",
  },
  {
    icon: Brain,
    title: "AI-Powered Model",
    description:
      "Leveraging machine learning to analyze alternative data points and generate accurate, fair credit scores.",
  },
  {
    icon: Users,
    title: "Built for Everyone",
    description:
      "Designed for students, gig workers, shopkeepers & rural individuals who are underserved by traditional banks.",
  },
];

export function LandingPage() {
  const { setCurrentPage } = useAppState();

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="flex min-h-screen flex-col items-center justify-center px-4 pt-32 pb-20 text-center">
        <div className="mx-auto max-w-3xl">
          <h1 className="animate-slide-up text-balance font-serif text-5xl font-bold leading-tight tracking-tight text-foreground md:text-7xl">
            Alternative Credit Score for the New India
          </h1>
          <p className="animate-slide-up stagger-2 mx-auto mt-6 max-w-xl text-balance text-lg leading-relaxed text-muted-foreground">
            Streamline financial inclusion with AI-powered credit scoring for
            every individual, tailored by CreditBridge.
          </p>
          <div className="animate-slide-up stagger-3 flex justify-center gap-4 pt-10">
            <Button
              size="lg"
              className="rounded-full bg-foreground px-8 py-6 text-base font-medium text-background transition-all duration-300 hover:scale-105 hover:bg-foreground/90 hover:shadow-lg active:scale-95"
              onClick={() => setCurrentPage("auth")}
            >
              Get Your Credit Score
            </Button>
          </div>
        </div>
      </section>

      {/* Subtle gradient line between hero and features */}
      <div className="mx-auto w-full max-w-2xl px-4">
        <div className="h-px w-full bg-gradient-to-r from-transparent via-border to-transparent" />
      </div>

      {/* Features Section */}
      <section className="px-4 py-24">
        <div className="mx-auto max-w-5xl text-center">
          <h2 className="font-serif text-3xl font-bold text-foreground md:text-4xl">
            <span className="text-balance">Why CreditBridge is different</span>
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-balance text-muted-foreground">
            We use alternative data to assess creditworthiness where traditional
            systems fall short.
          </p>

          <div className="mt-16 grid gap-8 md:grid-cols-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className={`animate-slide-up group rounded-2xl border border-border bg-card p-8 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-primary/20 stagger-${index + 1}`}
                >
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 transition-all duration-300 group-hover:bg-primary/20 group-hover:scale-110">
                    <Icon className="h-6 w-6 text-primary transition-transform duration-300 group-hover:-translate-y-0.5" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">
                    {feature.title}
                  </h3>
                  <p className="mt-2 leading-relaxed text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance font-serif text-3xl font-bold text-foreground md:text-4xl">
            Ready to discover your credit potential?
          </h2>
          <p className="text-balance mt-4 text-muted-foreground">
            Join thousands of Indians building their financial future with
            CreditBridge.
          </p>
          <div className="flex justify-center pt-8">
            <Button
              size="lg"
              className="rounded-full bg-foreground px-8 py-6 text-base font-medium text-background transition-all duration-300 hover:scale-105 hover:bg-foreground/90 hover:shadow-lg active:scale-95"
              onClick={() => setCurrentPage("auth")}
            >
              Start for free
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border px-4 py-8">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <span className="font-serif text-sm font-semibold text-foreground">
            CreditBridge
          </span>
          <span className="text-sm text-muted-foreground">
            {"2026 CreditBridge. All rights reserved."}
          </span>
        </div>
      </footer>
    </main>
  );
}
