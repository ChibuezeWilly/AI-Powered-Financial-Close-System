import { Eye, EyeOff } from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";
import { apiPost } from "../../lib/api";

export type Account = { id: number; full_name: string; email: string; role: string };

interface AuthModalProps {
  onSuccess: (token: string, user: Account) => void;
}

export function AuthModal({ onSuccess }: AuthModalProps) {
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authPortal, setAuthPortal] = useState<"admin" | "regular">("regular");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [authNotice, setAuthNotice] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAuthSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setAuthNotice("");
    const form = new FormData(e.currentTarget);
    const email = form.get("email") as string;
    const password = form.get("password") as string;
    const confirmPassword = form.get("confirm_password") as string;
    const full_name = form.get("full_name") as string;
    const role = (form.get("role") as string) || (authPortal === "regular" ? "REGULAR_USER" : "ANALYST");

    if (authMode === "register" && password !== confirmPassword) {
      setAuthNotice("Passwords do not match");
      return;
    }

    setLoading(true);
    const endpoint =
      authMode === "login"
        ? authPortal === "admin"
          ? "/api/v1/auth/admin/login"
          : "/api/v1/auth/users_login"
        : authPortal === "admin"
          ? "/api/v1/auth/admin/register"
          : "/api/v1/auth/users_register";

    const payload =
      authMode === "login"
        ? { email, password }
        : { email, password, full_name, role };

    try {
      const data = await apiPost<{ access_token: string; user: Account }>(endpoint, payload);
      localStorage.setItem("financial-close-token", data.access_token);
      toast.success("Authentication successful");
      onSuccess(data.access_token, data.user);
    } catch (err) {
      setAuthNotice(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center bg-[#071A2B] p-5 text-foreground">
      <form
        onSubmit={handleAuthSubmit}
        className="w-full max-w-md rounded-2xl border border-border bg-[#0a2033] p-7 shadow-2xl shadow-black/40"
      >
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo2.jpg" alt="Logo" className="h-10 w-10 rounded-lg border border-primary/30 object-cover" />
            <div>
              <p className="text-[10px] font-bold tracking-[0.2em] text-primary">TALLY FLOW</p>
              <h1 className="text-sm font-bold text-white">Financial Close System</h1>
            </div>
          </div>
          <div className="flex items-center rounded-lg border border-border bg-[#071a2b] p-1 text-xs">
            <button
              type="button"
              onClick={() => {
                setAuthPortal("regular");
                setAuthNotice("");
              }}
              className={`rounded-md px-2.5 py-1 font-semibold transition ${
                authPortal === "regular" ? "bg-primary text-[#071a2b]" : "text-muted-foreground hover:text-white"
              }`}
            >
              Customer
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthPortal("admin");
                setAuthNotice("");
              }}
              className={`rounded-md px-2.5 py-1 font-semibold transition ${
                authPortal === "admin" ? "bg-primary text-[#071a2b]" : "text-muted-foreground hover:text-white"
              }`}
            >
              Admin
            </button>
          </div>
        </div>

        <h2 className="text-xl font-bold text-white">
          {authMode === "login"
            ? `${authPortal === "admin" ? "Admin" : "Customer"} Sign In`
            : `Create ${authPortal === "admin" ? "Admin" : "Customer"} Account`}
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          {authPortal === "admin"
            ? "Reconciliation, AI investigations, document intelligence & financial approvals."
            : "Review your invoices, statements, and monthly transaction activity."}
        </p>

        <div className="mt-5 space-y-3.5">
          {authMode === "register" && (
            <>
              <label className="block text-xs font-semibold text-slate-300">
                Full Name
                <input
                  required
                  name="full_name"
                  placeholder="Jane Doe"
                  className="mt-1 w-full rounded-xl border border-border bg-[#071a2b] px-3.5 py-2.5 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
                />
              </label>
              {authPortal === "admin" && (
                <label className="block text-xs font-semibold text-slate-300">
                  Admin Role (governs LangGraph actions & approvals)
                  <select
                    name="role"
                    defaultValue="FINANCE_ADMIN"
                    className="mt-1 w-full rounded-xl border border-border bg-[#071a2b] px-3.5 py-2.5 text-xs text-white outline-none focus:border-primary"
                  >
                    <option value="ANALYST">Financial Analyst (Run Investigations)</option>
                    <option value="FINANCE_ADMIN">Finance Admin (Run Decisions & Adjustments)</option>
                    <option value="FINANCE_MANAGER">Finance Manager (Discount & Matrix Sign-off)</option>
                    <option value="ADMIN">Platform Administrator (Full Access)</option>
                  </select>
                </label>
              )}
            </>
          )}

          <label className="block text-xs font-semibold text-slate-300">
            Email Address
            <input
              required
              type="email"
              name="email"
              placeholder={authPortal === "admin" ? "admin@example.com" : "user@example.com"}
              className="mt-1 w-full rounded-xl border border-border bg-[#071a2b] px-3.5 py-2.5 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
            />
          </label>

          <label className="block text-xs font-semibold text-slate-300">
            Password
            <div className="relative mt-1">
              <input
                required
                minLength={8}
                type={showPassword ? "text" : "password"}
                name="password"
                placeholder="••••••••••••"
                className="w-full rounded-xl border border-border bg-[#071a2b] px-3.5 py-2.5 pr-10 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
              />
              <button
                type="button"
                aria-label={showPassword ? "Hide password" : "Show password"}
                onClick={() => setShowPassword((visible) => !visible)}
                className="absolute right-2 top-2 text-muted-foreground hover:text-white"
              >
                {showPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
              </button>
            </div>
          </label>

          {authMode === "register" && (
            <label className="block text-xs font-semibold text-slate-300">
              Confirm Password
              <div className="relative mt-1">
                <input
                  required
                  minLength={8}
                  type={showConfirmPassword ? "text" : "password"}
                  name="confirm_password"
                  placeholder="••••••••••••"
                  className="w-full rounded-xl border border-border bg-[#071a2b] px-3.5 py-2.5 pr-10 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
                />
                <button
                  type="button"
                  aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                  onClick={() => setShowConfirmPassword((visible) => !visible)}
                  className="absolute right-2 top-2 text-muted-foreground hover:text-white"
                >
                  {showConfirmPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </button>
              </div>
            </label>
          )}
        </div>

        {authNotice && (
          <p className="mt-3.5 rounded-lg border border-red-500/30 bg-red-950/40 p-2.5 text-xs font-medium text-red-300">
            {authNotice}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="mt-5 w-full rounded-xl bg-primary py-2.5 text-xs font-bold text-[#071a2b] shadow hover:bg-[#4ADE80] disabled:opacity-50"
        >
          {loading ? "Please wait..." : authMode === "login" ? "Sign In" : "Create Account"}
        </button>

        <p className="mt-4 text-center text-xs text-muted-foreground">
          {authMode === "login" ? "Don't have an account yet?" : "Already registered?"}{" "}
          <button
            type="button"
            className="font-bold text-primary hover:underline"
            onClick={() => {
              setAuthMode(authMode === "login" ? "register" : "login");
              setAuthNotice("");
            }}
          >
            {authMode === "login" ? "Register here" : "Sign in here"}
          </button>
        </p>
      </form>
    </main>
  );
}
