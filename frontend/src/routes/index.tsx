import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bell,
  CheckCircle2,
  ChevronDown,
  Clock,
  Eye,
  FileText,
  Filter,
  Layers,
  LogOut,
  Menu,
  Play,
  RefreshCw,
  Search,
  Shield,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  UserCheck,
  Users,
  Wallet,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { apiGet, apiPost } from "../lib/api";
import { useNotifications } from "../hooks/useNotifications";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export const Route = createFileRoute("/")({ component: Index });

type Account = { id: number; full_name: string; email: string; role: string };

type KPIResponse = {
  discrepancies: number;
  awaiting_approval: number;
  reconciled: number;
  investigations: number;
  resolution_watch_amount: number;
  total_transactions: number;
  current_period: string;
};

type InsightResponse = {
  period: string;
  summary: string;
  risks: string[];
  recommendations: string[];
};

type TransactionRecord = {
  id: string;
  period: string;
  date: string;
  customer: string;
  invoice_id: string;
  payment_id: string | null;
  account: string;
  currency: string;
  expected_amount: number;
  actual_amount: number;
  difference: number;
  discrepancy_type: string | null;
  severity: string;
  status: string;
  root_cause: string | null;
  recommendation: string | null;
  confidence: number | null;
};

type SearchResultItem = {
  source: string;
  kind: string;
  id: string;
  title: string;
  content?: string;
  location?: string;
  score?: number;
};

const navigationItems = [
  { label: "Overview", path: "/" },
  { label: "Financial Close", path: "/financial-close" },
  { label: "Reconciliation", path: "/reconciliation" },
  { label: "Transactions", path: "/transactions" },
  { label: "Discrepancies", path: "/discrepancies" },
  { label: "Investigations", path: "/investigations" },
  { label: "Approvals", path: "/approvals" },
  { label: "Documents", path: "/documents" },
  { label: "Reconciled", path: "/reconciled" },
  { label: "User Accounts", path: "/accounts" },
];

const months = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09"];

const formatCurrency = (val: number, cur = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: cur, maximumFractionDigits: 2 }).format(val);

const getStatusBadge = (status: string) => {
  const map: Record<string, string> = {
    RECONCILED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    RESOLVED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    DISCREPANCY_DETECTED: "bg-red-500/15 text-red-300 border-red-500/40",
    INVESTIGATING: "bg-orange-500/15 text-orange-300 border-orange-500/40 animate-pulse",
    AWAITING_HUMAN_APPROVAL: "bg-violet-500/15 text-violet-300 border-violet-500/40",
    AWAITING_MANAGER_APPROVAL: "bg-yellow-500/15 text-yellow-300 border-yellow-500/40",
    APPROVED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    REJECTED: "bg-red-500/15 text-red-300 border-red-500/40",
    ESCALATED: "bg-orange-500/15 text-orange-300 border-orange-500/40",
  };
  return map[status] ?? "bg-slate-500/15 text-slate-300 border-slate-500/40";
};

function Index() {
  const navigate = useNavigate();

  // Auth & Token with NO auth flash
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<Account | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // App State
  const [selectedPeriod, setSelectedPeriod] = useState<string>("2026-09");
  const [kpis, setKpis] = useState<KPIResponse | null>(null);
  const [insights, setInsights] = useState<InsightResponse | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Unified 3-Source Search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [excludedSources, setExcludedSources] = useState<string[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Customer Portal State
  const [portalTxs, setPortalTxs] = useState<TransactionRecord[]>([]);
  const [portalTotal, setPortalTotal] = useState(0);
  const [portalOffset, setPortalOffset] = useState(0);
  const [portalLoadingMore, setPortalLoadingMore] = useState(false);

  // Auth Modal State
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authPortal, setAuthPortal] = useState<"regular" | "admin">("regular");
  const [authNotice, setAuthNotice] = useState("");

  const { notifications, unreadCount, dismiss } = useNotifications(!!token);

  // Authenticate without flash
  useEffect(() => {
    const saved = localStorage.getItem("financial-close-token");
    if (!saved) {
      setIsCheckingAuth(false);
      return;
    }
    fetch(`${import.meta.env["VITE_API_URL"] || "http://localhost:8000"}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${saved}` },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((userData) => {
        setToken(saved);
        setUser(userData);
      })
      .catch(() => {
        localStorage.removeItem("financial-close-token");
        setToken(null);
        setUser(null);
      })
      .finally(() => setIsCheckingAuth(false));
  }, []);

  // Fetch admin dashboard data
  const fetchAdminData = useCallback(async () => {
    if (!token || user?.role === "REGULAR_USER") return;
    try {
      const [kpiData, txData] = await Promise.all([
        apiGet<KPIResponse>("/api/v1/workspace/kpis"),
        apiGet<TransactionRecord[]>(`/api/v1/transactions?period=${selectedPeriod}`),
      ]);
      setKpis(kpiData);
      setTransactions(txData);
    } catch (err) {
      console.error("Dashboard data load failed", err);
    }
  }, [token, user, selectedPeriod]);

  // Fetch AI insights
  const fetchInsights = useCallback(async () => {
    if (!token || user?.role === "REGULAR_USER") return;
    setInsightsLoading(true);
    try {
      const data = await apiGet<InsightResponse>(`/api/v1/workspace/insights?period=${selectedPeriod}`);
      setInsights(data);
    } catch (err) {
      console.error("Insights load failed", err);
    } finally {
      setInsightsLoading(false);
    }
  }, [token, user, selectedPeriod]);

  // Fetch customer portal transactions
  const fetchPortalData = useCallback(
    async (offset = 0, append = false) => {
      if (!token || user?.role !== "REGULAR_USER") return;
      if (append) setPortalLoadingMore(true);
      try {
        const data = await apiGet<{
          transactions: TransactionRecord[];
          total: number;
          offset: number;
          has_more: boolean;
        }>(`/api/v1/portal/transactions?period=${selectedPeriod}&limit=20&offset=${offset}`);
        if (append) {
          setPortalTxs((prev) => [...prev, ...data.transactions]);
        } else {
          setPortalTxs(data.transactions);
        }
        setPortalTotal(data.total);
        setPortalOffset(offset);
      } catch (err) {
        console.error("Portal transactions load failed", err);
      } finally {
        setPortalLoadingMore(false);
      }
    },
    [token, user, selectedPeriod]
  );

  useEffect(() => {
    if (user?.role === "REGULAR_USER") {
      fetchPortalData(0, false);
    } else if (user) {
      fetchAdminData();
      fetchInsights();
    }
  }, [user, selectedPeriod, fetchAdminData, fetchInsights, fetchPortalData]);

  // 3-Source Search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      const query = new URLSearchParams({ q: searchQuery.trim() });
      excludedSources.forEach((s) => query.append("exclude", s));
      const res = await apiGet<{ results: SearchResultItem[] }>(`/api/v1/workspace/search?${query}`);
      setSearchResults(res.results || []);
    } catch (err) {
      toast.error("Search failed");
    } finally {
      setSearchLoading(false);
    }
  };

  const toggleSourceExclusion = (source: string) => {
    setExcludedSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    );
  };

  // Sign out
  const handleSignOut = async () => {
    if (token) {
      try {
        await apiPost("/api/v1/auth/logout");
      } catch (e) {}
    }
    localStorage.removeItem("financial-close-token");
    setToken(null);
    setUser(null);
    toast.success("Signed out");
  };

  // Auth Submit
  const handleAuthSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setAuthNotice("");
    const form = new FormData(e.currentTarget);
    const email = form.get("email");
    const password = form.get("password");
    const full_name = form.get("full_name");
    const role = form.get("role") || (authPortal === "regular" ? "REGULAR_USER" : "ANALYST");

    const endpoint = authMode === "login" ? "/api/v1/auth/portal-login" : "/api/v1/auth/portal-register";
    const payload =
      authMode === "login"
        ? { email, password, portal: authPortal }
        : { email, password, full_name, role, portal: authPortal };

    try {
      const data = await apiPost<{ access_token: string; user: Account }>(endpoint, payload);
      localStorage.setItem("financial-close-token", data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      toast.success("Authentication successful");
    } catch (err) {
      setAuthNotice(err instanceof Error ? err.message : "Authentication failed");
    }
  };

  // Loading state (no flash)
  if (isCheckingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#071A2B]">
        <div className="flex flex-col items-center gap-3">
          <img src="/logo2.jpg" alt="TallyFlow" className="h-12 w-12 rounded-xl border border-primary/30 object-cover shadow-lg animate-pulse" />
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-xs font-bold tracking-widest text-primary">INITIALIZING TALLYFLOW...</p>
        </div>
      </div>
    );
  }

  // Not authenticated -> Render Login / Register
  if (!user) {
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
              <input
                required
                minLength={8}
                type="password"
                name="password"
                placeholder="••••••••••••"
                className="mt-1 w-full rounded-xl border border-border bg-[#071a2b] px-3.5 py-2.5 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
              />
            </label>
          </div>

          {authNotice && (
            <p className="mt-3.5 rounded-lg border border-red-500/30 bg-red-950/40 p-2.5 text-xs font-medium text-red-300">
              {authNotice}
            </p>
          )}

          <button
            type="submit"
            className="mt-5 w-full rounded-xl bg-primary py-2.5 text-xs font-bold text-[#071a2b] shadow hover:bg-[#4ADE80]"
          >
            {authMode === "login" ? "Sign In" : "Create Account"}
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

  // REGULAR USER PORTAL VIEW
  if (user.role === "REGULAR_USER") {
    const totalVolume = portalTxs.reduce((acc, t) => acc + t.actual_amount, 0);

    return (
      <div className="min-h-screen bg-[#071A2B] text-foreground">
        <header className="flex h-16 items-center justify-between border-b border-border bg-[#0a2033] px-6 md:px-12">
          <div className="flex items-center gap-3">
            <img src="/logo2.jpg" alt="Logo" className="h-8 w-8 rounded-lg border border-primary/30 object-cover" />
            <div>
              <span className="text-[10px] font-bold tracking-widest text-primary">TALLY FLOW</span>
              <p className="text-xs font-semibold text-white">Customer Account Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden text-right sm:block">
              <p className="text-xs font-bold text-white">{user.full_name}</p>
              <p className="text-[11px] text-muted-foreground">{user.email}</p>
            </div>
            <button
              onClick={handleSignOut}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-[#071a2b] px-3.5 py-1.5 text-xs font-semibold text-muted-foreground hover:text-white"
            >
              <LogOut className="h-3.5 w-3.5" /> Sign out
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-6xl p-6 md:p-10 space-y-6">
          <div className="rounded-2xl border border-primary/20 bg-gradient-to-r from-[#0a2033] to-[#0d2638] p-6 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-[11px] font-bold text-primary">
                  VERIFIED ACCOUNT
                </span>
                <h2 className="mt-2 text-2xl font-bold text-white">Welcome, {user.full_name}</h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  Here is your transaction ledger and balance overview. Showing active month by default.
                </p>
              </div>
              <div className="rounded-xl border border-border bg-[#071a2b] p-4 text-right">
                <p className="text-xs text-muted-foreground">Total Account Volume</p>
                <p className="text-2xl font-bold text-emerald-400">{formatCurrency(totalVolume)}</p>
              </div>
            </div>
          </div>

          {/* Month Selector Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            <span className="text-xs font-bold text-muted-foreground">SELECT MONTH:</span>
            {months.map((m) => (
              <button
                key={m}
                onClick={() => setSelectedPeriod(m)}
                className={`rounded-xl px-4 py-1.5 text-xs font-bold transition ${
                  selectedPeriod === m
                    ? "bg-primary text-[#071a2b] shadow"
                    : "border border-border bg-[#0a2033] text-muted-foreground hover:text-white"
                }`}
              >
                {new Date(`${m}-01`).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
              </button>
            ))}
          </div>

          {/* Transactions List (20 items with Show More) */}
          <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
            <div className="flex items-center justify-between border-b border-border bg-[#0d2638] px-6 py-3.5">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Transactions ({portalTxs.length} of {portalTotal} records)
              </span>
              <span className="text-xs text-primary font-medium">Period: {selectedPeriod}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="px-6 py-3 font-semibold">Date</th>
                    <th className="px-6 py-3 font-semibold">Transaction ID</th>
                    <th className="px-6 py-3 font-semibold">Invoice ID</th>
                    <th className="px-6 py-3 font-semibold">Account</th>
                    <th className="px-6 py-3 font-semibold text-right">Amount</th>
                    <th className="px-6 py-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {portalTxs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                        No transactions found for this period.
                      </td>
                    </tr>
                  ) : (
                    portalTxs.map((tx) => (
                      <tr
                        key={tx.id}
                        onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                        className="cursor-pointer transition hover:bg-white/5"
                      >
                        <td className="px-6 py-3.5 text-muted-foreground">{tx.date}</td>
                        <td className="px-6 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                        <td className="px-6 py-3.5 font-mono text-muted-foreground">{tx.invoice_id}</td>
                        <td className="px-6 py-3.5 text-muted-foreground">{tx.account}</td>
                        <td className="px-6 py-3.5 text-right font-bold text-white">{formatCurrency(tx.actual_amount)}</td>
                        <td className="px-6 py-3.5">
                          <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${getStatusBadge(tx.status)}`}>
                            {tx.status.replaceAll("_", " ")}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Show More Button */}
            {portalTxs.length < portalTotal && (
              <div className="border-t border-border p-4 text-center">
                <button
                  onClick={() => fetchPortalData(portalOffset + 20, true)}
                  disabled={portalLoadingMore}
                  className="rounded-xl border border-primary/30 bg-primary/10 px-6 py-2 text-xs font-bold text-primary hover:bg-primary hover:text-[#071a2b] disabled:opacity-50"
                >
                  {portalLoadingMore ? "Loading more..." : "Show More Transactions"}
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    );
  }

  // FINANCE ADMIN PLATFORM VIEW
  return (
    <div className="min-h-screen bg-[#071A2B] text-foreground">
      {/* Mobile Sidebar with scrollbar-none and hidden scrollbar width */}
      {mobileSidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setMobileSidebarOpen(false)}
          className="fixed inset-0 z-50 bg-black/70 md:hidden"
        />
      )}
      <aside
        aria-label="Mobile navigation"
        style={{ scrollbarWidth: "none" }}
        className={`fixed inset-y-0 right-0 z-60 w-64 border-l border-border bg-[#0a2033] p-5 shadow-2xl transition-transform duration-200 scrollbar-none md:hidden ${
          mobileSidebarOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo2.jpg" alt="Logo" className="h-8 w-8 rounded-lg border border-primary/30 object-cover" />
            <span className="text-xs font-bold tracking-widest text-primary">TALLY FLOW</span>
          </div>
          <button onClick={() => setMobileSidebarOpen(false)} className="rounded p-1 text-muted-foreground hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav style={{ scrollbarWidth: "none" }} className="space-y-1 overflow-y-auto scrollbar-none text-sm">
          {navigationItems.map((item) => (
            <Link
              key={item.label}
              to={item.path === "/" ? "/" : "/$section"}
              params={item.path === "/" ? undefined : { section: item.path.slice(1) }}
              onClick={() => setMobileSidebarOpen(false)}
              className={`block rounded-lg px-3 py-2.5 font-medium transition ${
                item.path === "/"
                  ? "bg-primary/20 text-primary border border-primary/30"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Desktop Sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-[#0a2033] p-5 lg:block">
        <div className="mb-8 flex items-center gap-3">
          <img src="/logo2.jpg" alt="Logo" className="h-9 w-9 rounded-lg border border-primary/30 object-cover shadow" />
          <div>
            <p className="text-[10px] font-bold tracking-[0.2em] text-primary">TALLY FLOW</p>
            <p className="text-xs font-medium text-muted-foreground">Close Platform</p>
          </div>
        </div>
        <nav className="space-y-1 text-sm font-medium">
          {navigationItems.map((item) => (
            <Link
              key={item.label}
              to={item.path === "/" ? "/" : "/$section"}
              params={item.path === "/" ? undefined : { section: item.path.slice(1) }}
              className={`block rounded-lg px-3 py-2.5 transition ${
                item.path === "/"
                  ? "bg-primary/20 text-primary border border-primary/30 shadow-sm"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main Panel */}
      <div className="lg:pl-64">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-[#0a2033]/90 px-5 backdrop-blur md:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="rounded-lg border border-border bg-card p-2 text-muted-foreground hover:text-white lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div>
              <p className="text-sm font-bold text-white">TallyFlow Operations</p>
              <p className="text-xs text-muted-foreground">
                Period: <span className="font-semibold text-primary">{selectedPeriod}</span> · Role:{" "}
                <span className="font-semibold text-white">{user.role}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-primary/30 bg-[#071a2b] px-3 py-1 text-xs font-medium text-primary">
              <Sparkles className="h-3.5 w-3.5" /> Hugging Face Inference Online
            </div>

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative rounded-lg border border-border bg-[#071a2b] p-2 text-muted-foreground hover:text-white"
              >
                <Bell className="h-4 w-4" />
                {unreadCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[9px] font-bold text-white">
                    {unreadCount}
                  </span>
                )}
              </button>
              {showNotifications && (
                <div className="absolute right-0 top-12 z-50 w-80 rounded-2xl border border-border bg-[#0d2638] p-4 shadow-2xl">
                  <div className="flex items-center justify-between border-b border-border pb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-primary">Notifications</span>
                    <button onClick={() => setShowNotifications(false)} className="text-muted-foreground hover:text-white">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <div className="mt-2 max-h-64 space-y-2 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <p className="py-4 text-center text-xs text-muted-foreground">No new notifications</p>
                    ) : (
                      notifications.map((n) => (
                        <div key={n.id} className="flex items-start justify-between rounded-lg bg-black/20 p-2 text-xs">
                          <div>
                            <p className="font-semibold text-white">{n.event.replaceAll("_", " ")}</p>
                            <p className="text-muted-foreground">{n.message}</p>
                          </div>
                          <button onClick={() => dismiss(n.id)} className="text-muted-foreground hover:text-white">
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={handleSignOut}
              className="inline-flex items-center gap-1 rounded-xl border border-border bg-[#071a2b] px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-white"
            >
              <LogOut className="h-3.5 w-3.5" /> Sign out
            </button>
          </div>
        </header>

        <main className="p-5 md:p-8 space-y-6">
          {/* REAL-TIME KPI CARDS (Served from DB) */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Discrepancies */}
            <Link
              to="/$section"
              params={{ section: "discrepancies" }}
              className="group rounded-2xl border border-border bg-[#0a2033] p-5 shadow transition hover:border-rose-500/50 hover:bg-[#0d2638]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">Discrepancies Detected</span>
                <AlertTriangle className="h-4 w-4 text-rose-400" />
              </div>
              <p className="mt-2 text-3xl font-bold text-white group-hover:text-rose-400">
                {kpis?.discrepancies ?? "..."}
              </p>
              <p className="mt-1 flex items-center gap-1 text-[11px] text-rose-400">
                Action required <ArrowRight className="h-3 w-3" />
              </p>
            </Link>

            {/* Awaiting Approval */}
            <Link
              to="/$section"
              params={{ section: "approvals" }}
              className="group rounded-2xl border border-border bg-[#0a2033] p-5 shadow transition hover:border-yellow-500/50 hover:bg-[#0d2638]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">Awaiting Approval</span>
                <Clock className="h-4 w-4 text-yellow-400" />
              </div>
              <p className="mt-2 text-3xl font-bold text-white group-hover:text-yellow-400">
                {kpis?.awaiting_approval ?? "..."}
              </p>
              <p className="mt-1 flex items-center gap-1 text-[11px] text-yellow-400">
                Sign-off pending <ArrowRight className="h-3 w-3" />
              </p>
            </Link>

            {/* Reconciled */}
            <Link
              to="/$section"
              params={{ section: "reconciled" }}
              className="group rounded-2xl border border-border bg-[#0a2033] p-5 shadow transition hover:border-emerald-500/50 hover:bg-[#0d2638]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">Reconciled Accounts</span>
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              </div>
              <p className="mt-2 text-3xl font-bold text-white group-hover:text-emerald-400">
                {kpis?.reconciled ?? "..."}
              </p>
              <p className="mt-1 flex items-center gap-1 text-[11px] text-emerald-400">
                Verified zero variance <ArrowRight className="h-3 w-3" />
              </p>
            </Link>

            {/* Resolution Watch */}
            <Link
              to="/$section"
              params={{ section: "discrepancies" }}
              className="group rounded-2xl border border-border bg-[#0a2033] p-5 shadow transition hover:border-primary/50 hover:bg-[#0d2638]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">Resolution Watch Amount</span>
                <Wallet className="h-4 w-4 text-primary" />
              </div>
              <p className="mt-2 text-3xl font-bold text-primary">
                {kpis ? formatCurrency(kpis.resolution_watch_amount) : "..."}
              </p>
              <p className="mt-1 flex items-center gap-1 text-[11px] text-primary">
                Total variance pool <ArrowRight className="h-3 w-3" />
              </p>
            </Link>
          </div>

          {/* OVERVIEW AI INSIGHTS (HF Inference Llama-3.3-70B) */}
          <div className="rounded-2xl border border-primary/30 bg-gradient-to-r from-[#0d2638] via-[#0a2033] to-[#0a2033] p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary animate-pulse" />
                <h2 className="text-sm font-bold text-white">AI Executive Close Intelligence</h2>
                <span className="rounded-full border border-primary/30 bg-primary/10 px-2.5 py-0.5 text-[10px] font-bold text-primary">
                  HF Inference
                </span>
              </div>
              <button
                onClick={fetchInsights}
                disabled={insightsLoading}
                className="flex items-center gap-1 text-xs text-primary hover:underline disabled:opacity-50"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${insightsLoading ? "animate-spin" : ""}`} /> Regenerate
              </button>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-5 md:grid-cols-3">
              <div className="md:col-span-1 space-y-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase">Executive Summary</p>
                <p className="text-xs leading-relaxed text-slate-200">
                  {insights?.summary || "Analyzing period ledger data via Hugging Face inference..."}
                </p>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold text-rose-400 uppercase">Top Variance Risks</p>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {(insights?.risks || ["Unapproved discounts on enterprise invoices", "Duplicate payment runs pending authorization"]).map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-rose-400 mt-0.5">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold text-emerald-400 uppercase">Recommended Actions</p>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {(insights?.recommendations || ["Escalate transactions >$250 variance to Finance Manager", "Enforce FIN-042 documentation before close"]).map((rec, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-emerald-400 mt-0.5">✓</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* UNIFIED 3-SOURCE SEARCH */}
          <div className="rounded-2xl border border-border bg-[#0a2033] p-5 shadow">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-sm font-bold text-white">Unified 3-Source Intelligence Search</h3>
                <p className="text-xs text-muted-foreground">
                  Simultaneously queries PostgreSQL tables, Pinecone 1024-d vectors, and BM25 knowledge index.
                </p>
              </div>
              {/* Source toggles */}
              <div className="flex items-center gap-3 text-xs">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!excludedSources.includes("postgres")}
                    onChange={() => toggleSourceExclusion("postgres")}
                    className="accent-primary"
                  />
                  <span className="text-slate-300">PostgreSQL</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!excludedSources.includes("pinecone")}
                    onChange={() => toggleSourceExclusion("pinecone")}
                    className="accent-primary"
                  />
                  <span className="text-slate-300">Pinecone (1024-d)</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!excludedSources.includes("bm25")}
                    onChange={() => toggleSourceExclusion("bm25")}
                    className="accent-primary"
                  />
                  <span className="text-slate-300">BM25 Keywords</span>
                </label>
              </div>
            </div>

            <form onSubmit={handleSearch} className="mt-3 flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search accounts, invoices, policies, or semantic keywords..."
                  className="w-full rounded-xl border border-border bg-[#071a2b] py-2 pl-9 pr-4 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
                />
              </div>
              <button
                type="submit"
                disabled={searchLoading}
                className="rounded-xl bg-primary px-5 py-2 text-xs font-bold text-[#071a2b] hover:bg-[#4ADE80] disabled:opacity-50"
              >
                {searchLoading ? "Searching..." : "Search"}
              </button>
            </form>

            {searchResults.length > 0 && (
              <div className="mt-4 max-h-72 divide-y divide-border/40 overflow-y-auto rounded-xl border border-border bg-[#071a2b] p-2">
                {searchResults.map((item, idx) => (
                  <div key={idx} className="flex items-start justify-between p-2.5 text-xs hover:bg-white/5">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{item.title}</span>
                        <span className="rounded bg-black/40 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
                          {item.id}
                        </span>
                      </div>
                      <p className="text-muted-foreground line-clamp-1">{item.content}</p>
                    </div>
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                        item.source === "pinecone"
                          ? "bg-violet-950 text-violet-300 border border-violet-800"
                          : item.source === "bm25"
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                      }`}
                    >
                      {item.source}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* RECENT TRANSACTIONS TABLE (Clicking row opens solo detail page) */}
          <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
            <div className="flex flex-wrap items-center justify-between border-b border-border bg-[#0d2638] px-6 py-3.5 gap-3">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Transactions Overview ({selectedPeriod})
                </h3>
                <p className="text-[11px] text-muted-foreground">
                  Click ANY row to open its solo investigation page directly.
                </p>
              </div>

              {/* Month tabs */}
              <div className="flex items-center gap-1 rounded-xl border border-border bg-[#071a2b] p-1">
                {months.map((m) => (
                  <button
                    key={m}
                    onClick={() => setSelectedPeriod(m)}
                    className={`rounded-lg px-3 py-1 text-xs font-bold transition ${
                      selectedPeriod === m ? "bg-primary text-[#071a2b]" : "text-muted-foreground hover:text-white"
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="px-6 py-3 font-semibold">Date</th>
                    <th className="px-6 py-3 font-semibold">Transaction ID</th>
                    <th className="px-6 py-3 font-semibold">Customer</th>
                    <th className="px-6 py-3 font-semibold">Invoice ID</th>
                    <th className="px-6 py-3 font-semibold text-right">Expected</th>
                    <th className="px-6 py-3 font-semibold text-right">Actual</th>
                    <th className="px-6 py-3 font-semibold text-right">Variance</th>
                    <th className="px-6 py-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {transactions.slice(0, 15).map((tx) => (
                    <tr
                      key={tx.id}
                      onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                      className="cursor-pointer transition hover:bg-white/5"
                    >
                      <td className="px-6 py-3.5 text-muted-foreground">{tx.date}</td>
                      <td className="px-6 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                      <td className="px-6 py-3.5 font-medium text-white">{tx.customer}</td>
                      <td className="px-6 py-3.5 font-mono text-muted-foreground">{tx.invoice_id}</td>
                      <td className="px-6 py-3.5 text-right text-muted-foreground">{formatCurrency(tx.expected_amount)}</td>
                      <td className="px-6 py-3.5 text-right font-medium text-white">{formatCurrency(tx.actual_amount)}</td>
                      <td className={`px-6 py-3.5 text-right font-bold ${tx.difference !== 0 ? "text-rose-400" : "text-emerald-400"}`}>
                        {tx.difference !== 0 ? formatCurrency(tx.difference) : "$0.00"}
                      </td>
                      <td className="px-6 py-3.5">
                        <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${getStatusBadge(tx.status)}`}>
                          {tx.status.replaceAll("_", " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
