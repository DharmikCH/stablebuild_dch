"use client";

import { useAppState } from "@/lib/app-context";
import { Button } from "@/components/ui/button";

export function Navbar() {
  const {
    setCurrentPage,
    isLoggedIn,
    setIsLoggedIn,
    setCreditScore,
    setRiskBand,
  } = useAppState();

  return (
    <header className="fixed top-4 left-1/2 z-50 w-full max-w-6xl -translate-x-1/2 px-4 animate-slide-down">
      <nav className="flex items-center justify-between rounded-full border border-border bg-card/80 px-12 py-6 shadow-sm backdrop-blur-md transition-shadow duration-300 hover:shadow-md">
        <button
          type="button"
          onClick={() => setCurrentPage("landing")}
          className="font-serif text-3xl font-bold tracking-tight text-foreground transition-all duration-200 hover:scale-105 hover:text-primary"
        >
          CreditBridge
        </button>

        <div className="flex items-center gap-5">
          {isLoggedIn ? (
            <>
              <Button
                type="button"
                variant="ghost"
                size="lg"
                className="text-lg transition-all duration-200 hover:scale-105"
                onClick={() => setCurrentPage("dashboard")}
              >
                Dashboard
              </Button>
              <Button
                type="button"
                variant="outline"
                size="lg"
                className="rounded-full text-lg transition-all duration-200 hover:scale-105 hover:bg-foreground hover:text-background"
                onClick={() => {
                  setIsLoggedIn(false);
                  setCreditScore(null);
                  setRiskBand(null);
                  setCurrentPage("landing");
                }}
              >
                Log out
              </Button>
            </>
          ) : (
            <Button
              type="button"
              variant="outline"
              size="lg"
              className="rounded-full text-lg transition-all duration-200 hover:scale-105 hover:bg-foreground hover:text-background"
              onClick={() => setCurrentPage("auth")}
            >
              Log in
            </Button>
          )}
        </div>
      </nav>
    </header>
  );
}
