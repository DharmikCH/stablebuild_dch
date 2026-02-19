"use client"

import { useState } from "react"
import { useAppState } from "@/lib/app-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"

export function AuthPage() {
  const { setCurrentPage, setIsLoggedIn, setUserName, users, setUsers } = useAppState()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isSignUp, setIsSignUp] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (isSignUp) {
      // Sign up - requires email and password to be filled
      if (!email || !password) {
        setError("Please fill in all fields")
        return
      }

      // Check if email already exists
      if (users.some(user => user.email === email)) {
        setError("Email already registered. Please sign in instead.")
        return
      }

      // Create new user
      const name = email.split("@")[0] || "User"
      const newUser = {
        email,
        password,
        userName: name.charAt(0).toUpperCase() + name.slice(1)
      }
      setUsers([...users, newUser])

      setUserName(newUser.userName)
      setIsLoggedIn(true)
      setCurrentPage("profile-select")
    } else {
      // Sign in - validate credentials against registered users
      if (!email || !password) {
        setError("Please fill in all fields")
        return
      }

      const user = users.find(u => u.email === email && u.password === password)

      if (user) {
        setUserName(user.userName)
        setIsLoggedIn(true)
        setCurrentPage("dashboard")
      } else {
        setError("Invalid email or password. Please check and try again.")
      }
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 pt-32 pb-20">
      <div className="w-full max-w-md animate-scale-in">
        <div className="rounded-2xl border border-border bg-card p-8 shadow-sm transition-shadow duration-300 hover:shadow-md">
          <div className="mb-8 text-center">
            <h1 className="font-serif text-3xl font-bold text-foreground">
              {isSignUp ? "Create Account" : "Welcome back"}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {isSignUp
                ? "Sign up to discover your alternative credit score"
                : "Sign in to access your credit dashboard"}
            </p>
          </div>

          {error && (
            <Alert className="mb-5 border-red-200 bg-red-50">
              <AlertDescription className="text-sm text-red-800">
                {error}
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <Label htmlFor="email" className="text-sm font-medium text-foreground">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="rounded-lg border-border bg-background px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-primary/20 focus:border-primary/40"
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="password" className="text-sm font-medium text-foreground">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="rounded-lg border-border bg-background px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-primary/20 focus:border-primary/40"
              />
            </div>

            <Button
              type="submit"
              size="lg"
              className="mt-2 w-full rounded-full bg-foreground py-6 text-base font-medium text-background transition-all duration-300 hover:scale-[1.02] hover:bg-foreground/90 hover:shadow-lg active:scale-[0.98]"
            >
              Continue
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
            <button
              onClick={() => setIsSignUp(!isSignUp)}
              className="font-medium text-foreground underline underline-offset-4 transition-colors duration-200 hover:text-primary"
            >
              {isSignUp ? "Sign in" : "Sign up"}
            </button>
          </p>
        </div>
      </div>
    </main>
  )
}
