import { Link, createFileRoute } from "@tanstack/react-router";
import {
  Activity,
  ArrowRight,
  Bell,
  CircleAlert,
  FileBarChart,
  LogOut,
  Play,
  RefreshCw,
  ShieldCheck,
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
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export const Route = createFileRoute("/")({ component: Index });

type Account = { full_name: string; email: string; role: string };
type DashboardResponse = {
  period: string;
  period_status: string;
  total_transactions: number;
  reconciled: number;
  discrepancies: number;
  awaiting_approval: number;
  close_progress: number;
  unresolved_amount: number;
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

type PeriodRecord = { code: string; status: string };

const REFRESH_INTERVAL_MS = 30_000;

const monthOrder = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

const formatCurrency = (value: number, currency = "USD") =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);

const getDiscrepancyBar = (status: string, severity: string, difference: number) => {
  if (status === "RECONCILED" || status === "RESOLVED") return "bg-emerald-500";
  if (difference === 0) return "bg-emerald-500";
  if (status === "AWAITING_HUMAN_APPROVAL" || status === "APPROVED" || status === "ADJUSTMENT_PENDING")
    return "bg-violet-500";
  if (status === "AWAITING_MANAGER_APPROVAL") return "bg-yellow-500";
  if (status === "REJECTED_MANAGER" || status === "PAYMENT_REQUESTED" || status === "PAYMENT_PENDING")
    return "bg-amber-500";
  if (severity === "HIGH" || severity === "CRITICAL") return "bg-red-500";
  if (severity === "MEDIUM") return "bg-orange-400";
  return "bg-yellow-400";
};

const getStatusBadge = (status: string) => {
  const map: Record<string, string> = {
    RECONCILED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    RESOLVED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    DISCREPANCY_DETECTED: "bg-red-500/15 text-red-300 border-red-500/40",
    INVESTIGATING: "bg-orange-500/15 text-orange-300 border-orange-500/40",
    AWAITING_HUMAN_APPROVAL: "bg-violet-500/15 text-violet-300 border-violet-500/40",
    APPROVED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    ADJUSTED: "bg-teal-500/15 text-teal-300 border-teal-500/40",
    ADJUSTMENT_PENDING: "bg-sky-500/15 text-sky-300 border-sky-500/40",
    AWAITING_MANAGER_APPROVAL: "bg-yellow-500/15 text-yellow-300 border-yellow-500/40",
    REJECTED: "bg-red-500/15 text-red-300 border-red-500/40",
    REJECTED_MANAGER: "bg-rose-500/15 text-rose-300 border-rose-500/40",
    ESCALATED: "bg-orange-500/15 text-orange-300 border-orange-500/40",
    PAYMENT_REQUESTED: "bg-amber-500/15 text-amber-200 border-amber-500/40",
    PAYMENT_PENDING: "bg-amber-500/15 text-amber-200 border-amber-500/40",
    PAYMENT_RECEIVED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  };

  return map[status] ?? "bg-slate-500/15 text-slate-300 border-slate-500/40";
};

function Index() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<Account | null>(null);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [notice, setNotice] = useState("");
  const [periods, setPeriods] = useState<PeriodRecord[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string>("");
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [monthlyTrend, setMonthlyTrend] = useState<Array<{ month: string; value: number }>>([]);
  const [dataError, setDataError] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);
  const [periodActionLoading, setPeriodActionLoading] = useState<string | null>(null);
  const refreshRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { notifications, unreadCount, dismiss } = useNotifications(!!token);

  useEffect(() => {
    const saved = localStorage.getItem("financial-close-token");
    if (!saved) return;

    fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${saved}` },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((userData) => {
        setToken(saved);
        setUser(userData);
      })
      .catch(() => localStorage.removeItem("financial-close-token"));
  }, []);

  useEffect(() => {
    if (!token) return;

    const now = new Date();
    const currentPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    setSelectedPeriod((existing) => existing || currentPeriod);

    apiGet<PeriodRecord[]>("/api/v1/periods").then(setPeriods).catch(() => setPeriods([]));
  }, [token]);

  // Core data fetcher — used both by effect and the auto-refresh timer
  const fetchDashboardData = useCallback(async () => {
    if (!token || !selectedPeriod) return;
    try {
      const [dashboardData, transactionData] = await Promise.all([
        apiGet<DashboardResponse>(`/api/v1/dashboard?period=${selectedPeriod}`),
        apiGet<TransactionRecord[]>(`/api/v1/transactions?period=${selectedPeriod}`),
      ]);
      setDashboard(dashboardData);
      setTransactions(transactionData);
      setDataError("");
    } catch (error) {
      setDashboard(null);
      setTransactions([]);
      setDataError(error instanceof Error ? error.message : "Unable to load live close data.");
    }
  }, [token, selectedPeriod]);

  // Fetch on period change
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!token || !selectedPeriod) return;
    refreshRef.current = setInterval(fetchDashboardData, REFRESH_INTERVAL_MS);
    return () => {
      if (refreshRef.current) clearInterval(refreshRef.current);
    };
  }, [token, selectedPeriod, fetchDashboardData]);

  useEffect(() => {
    if (!token || !periods.length) return;
    const recentPeriods = periods.filter((period) => period.code <= selectedPeriod).slice(-5);
    Promise.all(recentPeriods.map(async (period) => ({
      month: period.code,
      value: (await apiGet<DashboardResponse>(`/api/v1/dashboard?period=${period.code}`)).close_progress,
    })))
      .then(setMonthlyTrend)
      .catch(() => setMonthlyTrend([]));
  }, [periods, selectedPeriod, token]);

  async function runReconciliation() {
    setPeriodActionLoading("reconcile");
    try {
      const result = await apiPost<{ matched: number; discrepancies: number }>(`/api/v1/periods/${selectedPeriod}/reconcile`);
      toast.success("Reconciliation complete", {
        description: `Matched: ${result.matched ?? 0} · Discrepancies: ${result.discrepancies ?? 0}`,
      });
      await fetchDashboardData();
    } catch (error) {
      toast.error("Reconciliation failed", {
        description: error instanceof Error ? error.message : "An unexpected error occurred.",
      });
    } finally {
      setPeriodActionLoading(null);
    }
  }

  async function generateReport() {
    setPeriodActionLoading("report");
    try {
      const result = await apiPost<{ period: string; transaction_count: number }>(`/api/v1/periods/${selectedPeriod}/report`);
      toast.success("Report generated", {
        description: `Period ${result.period} · ${result.transaction_count} transactions analyzed`,
      });
    } catch (error) {
      toast.error("Report generation failed", {
        description: error instanceof Error ? error.message : "An unexpected error occurred.",
      });
    } finally {
      setPeriodActionLoading(null);
    }
  }

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setNotice("");
    const form = new FormData(e.currentTarget);
    const payload =
      mode === "login"
        ? { email: form.get("email"), password: form.get("password") }
        : {
            email: form.get("email"),
            password: form.get("password"),
            full_name: form.get("full_name"),
          };

    const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/v1/auth/${mode === "login" ? "login" : "register"}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      setNotice(data.detail || "Unable to complete request.");
      return;
    }

    localStorage.setItem("financial-close-token", data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    toast.success("Signed in successfully");
  }

  async function signOut() {
    if (token) {
      await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/v1/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    }

    localStorage.removeItem("financial-close-token");
    setToken(null);
    setUser(null);
  }

  if (!user) {
    return <Auth mode={mode} setMode={setMode} submit={submit} notice={notice} />;
  }

  const nextPeriodLabel = useMemo(() => {
    const [year, monthIndex] = selectedPeriod.split("-").map(Number);
    if (!year || !monthIndex) return "Period";
    return `${monthOrder[monthIndex - 1]} ${year}`;
  }, [selectedPeriod]);

  const activePeriodStatus = periods.find((period) => period.code === selectedPeriod)?.status ?? "OPEN";
  const reconciledCount = transactions.filter((t) => ["RECONCILED", "RESOLVED"].includes(t.status)).length;
  const pendingApproval = transactions.filter((t) => t.status === "AWAITING_HUMAN_APPROVAL").length;

  const summaryData = [
    { name: "Reconciled", value: Math.max(reconciledCount, 0) },
    { name: "Open", value: Math.max(transactions.length - reconciledCount, 0) },
    { name: "Approval", value: pendingApproval },
  ];

  const severityData = [
    { name: "Low", value: transactions.filter((t) => t.severity === "LOW").length },
    { name: "Medium", value: transactions.filter((t) => t.severity === "MEDIUM").length },
    { name: "High", value: transactions.filter((t) => t.severity === "HIGH").length },
    { name: "Critical", value: transactions.filter((t) => t.severity === "CRITICAL").length },
  ];

  return (
    <main className="min-h-screen overflow-x-hidden bg-background text-foreground">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-[#0a2033] p-5 lg:block">
        <div className="mb-10 flex items-center gap-3">
          <img
            src="/logo2.jpg"
            alt="TallyFlow logo"
            className="h-10 w-10 rounded-md border border-primary/20 object-cover shadow-lg shadow-emerald-900/20"
          />
          <div>
            <p className="text-[10px] font-bold tracking-[0.22em] text-primary">TALLY FLOW</p>
            <p className="text-xs text-muted-foreground">Financial Close</p>
          </div>
        </div>

        <nav className="space-y-1 text-sm text-muted-foreground">
          {[
            "Overview",
            "Financial Close",
            "Reconciliation",
            "Transactions",
            "Discrepancies",
            "Investigations",
            "Approvals",
            "Documents",
            "Knowledge Base",
            "Accounts",
            "Ledger",
            "Reports",
            "Audit Log",
            "Settings",
          ].map((item, index) => (
            <div
              key={item}
              className={`rounded-md px-3 py-2.5 ${
                index === 1 ? "bg-primary/15 font-medium text-primary" : "hover:bg-white/5 hover:text-foreground"
              }`}
            >
              {item}
            </div>
          ))}
        </nav>
      </aside>

      <section className="lg:pl-64">
        <header className="flex h-16 items-center justify-between border-b border-border bg-[#0d2638] px-5 md:px-8">
          <div>
            <p className="text-sm font-semibold">TallyFlow</p>
            <p className="text-xs text-muted-foreground">
              {nextPeriodLabel} · <span className="text-primary">{activePeriodStatus}</span>
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 rounded-full border border-border bg-[#0a2033] px-2 py-1 text-xs text-primary">
              <Activity className="h-3.5 w-3.5" />
              AI processing online
            </div>

            {/* Notifications bell with dropdown */}
            <div className="relative">
              <button
                id="notifications-bell"
                aria-label="Notifications"
                onClick={() => setShowNotifications((v) => !v)}
                className="relative rounded-md p-1.5 text-muted-foreground hover:text-foreground"
              >
                <Bell className="h-4 w-4" />
                {unreadCount > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </span>
                )}
              </button>
              {showNotifications && (
                <div className="absolute right-0 top-10 z-50 w-80 rounded-xl border border-border bg-[#0d2638] shadow-2xl shadow-black/40">
                  <div className="flex items-center justify-between border-b border-border px-4 py-3">
                    <p className="text-xs font-bold tracking-[0.14em] text-primary">NOTIFICATIONS</p>
                    <button onClick={() => setShowNotifications(false)} className="text-muted-foreground hover:text-foreground">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <div className="max-h-72 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <p className="px-4 py-6 text-center text-sm text-muted-foreground">No recent notifications</p>
                    ) : (
                      notifications.map((n) => (
                        <div key={n.id} className="flex items-start gap-3 border-b border-border/50 px-4 py-3 last:border-0">
                          <div className={`mt-1 h-2 w-2 shrink-0 rounded-full ${n.status === "PENDING" ? "bg-amber-400" : "bg-emerald-400"}`} />
                          <div className="flex-1 text-xs">
                            <p className="font-medium text-foreground">{n.event.replaceAll("_", " ")}</p>
                            <p className="mt-0.5 text-muted-foreground">{n.message}</p>
                            <p className="mt-1 text-[10px] text-muted-foreground/60">{new Date(n.created_at).toLocaleString()}</p>
                          </div>
                          <button onClick={() => dismiss(n.id)} className="shrink-0 text-muted-foreground hover:text-foreground">
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="hidden text-right text-xs sm:block">
              <p className="font-medium text-foreground">{user.full_name}</p>
              <p className="text-primary">{user.role.replace("_", " ")}</p>
            </div>
            <button
              aria-label="Sign out"
              onClick={signOut}
              className="rounded-md border border-border p-2 text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
          <div className="mb-8 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="mb-2 text-xs font-bold tracking-[0.18em] text-primary">FINANCIAL CLOSE CONTROL CENTER</p>
              <h1 className="text-3xl font-semibold tracking-tight">{nextPeriodLabel}</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Reconciliation, evidence review, and approval workflows for the current close period.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Period action buttons */}
              <button
                id="btn-reconcile"
                disabled={!!periodActionLoading}
                onClick={runReconciliation}
                className="inline-flex items-center gap-1.5 rounded-md border border-primary/40 bg-primary/10 px-3 py-2 text-xs font-medium text-primary transition hover:bg-primary/20 disabled:opacity-50"
              >
                {periodActionLoading === "reconcile" ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                Reconcile
              </button>
              <button
                id="btn-report"
                disabled={!!periodActionLoading}
                onClick={generateReport}
                className="inline-flex items-center gap-1.5 rounded-md border border-border bg-[#0d2638] px-3 py-2 text-xs font-medium text-muted-foreground transition hover:text-foreground disabled:opacity-50"
              >
                {periodActionLoading === "report" ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <FileBarChart className="h-3.5 w-3.5" />}
                Report
              </button>
              <span className="mx-1 h-5 w-px bg-border" />
              {periods.filter((period) => period.code.startsWith(selectedPeriod.slice(0, 4))).map((period) => {
                const code = period.code;
                const month = monthOrder[Number(code.slice(-2)) - 1];
                const active = code === selectedPeriod;
                return (
                  <button
                    key={month}
                    onClick={() => setSelectedPeriod(code)}
                    className={`rounded-md border px-3 py-2 text-xs font-medium transition ${
                      active
                        ? "border-primary bg-primary/15 text-primary"
                        : "border-border bg-[#0d2638] text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {month}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Metric
              label="Transactions"
              value={String(dashboard?.total_transactions ?? transactions.length)}
              detail="Total posted during the period"
            />
            <Metric
              label="Reconciled"
              value={String(dashboard?.reconciled ?? reconciledCount)}
              detail="Matched and verified"
              accent
            />
            <Metric
              label="Discrepancies"
              value={String(dashboard?.discrepancies ?? transactions.filter((t) => t.difference !== 0).length)}
              detail="Open exceptions pending review"
              warn
            />
            <Metric
              label="Awaiting approval"
              value={String(dashboard?.awaiting_approval ?? pendingApproval)}
              detail="Human review required"
            />
          </div>
          {dataError && <p className="mb-6 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200" role="alert">{dataError}</p>}

          <div className="mb-8 grid gap-6 xl:grid-cols-[1.7fr_1fr]">
            <section className="rounded-xl border border-border bg-[#0d2638] p-5">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold tracking-[0.18em] text-primary">RECONCILIATION SUMMARY</p>
                  <h2 className="mt-1 text-xl font-semibold">Close progress</h2>
                </div>
                <div className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                  {Math.round(dashboard?.close_progress ?? 82)}%
                </div>
              </div>

              <div className="mb-6 h-3 overflow-hidden rounded-full bg-[#071a2b]">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-emerald-400 transition-all duration-700"
                  style={{ width: `${dashboard?.close_progress ?? 82}%` }}
                />
              </div>

              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1B3A4D" />
                    <XAxis dataKey="month" stroke="#8FA3B8" tickLine={false} axisLine={false} />
                    <YAxis stroke="#8FA3B8" tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0D2638", border: "1px solid #1B3A4D", borderRadius: 12 }}
                    />
                    <Bar dataKey="value" fill="#19C37D" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="rounded-xl border border-border bg-[#0d2638] p-5">
              <p className="text-xs font-bold tracking-[0.18em] text-primary">STATUS DISTRIBUTION</p>
              <div className="mt-4 h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={summaryData} dataKey="value" nameKey="name" innerRadius={48} outerRadius={72} paddingAngle={3}>
                      {summaryData.map((entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={index === 0 ? "#19C37D" : index === 1 ? "#4ADE80" : "#a78bfa"}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0D2638", border: "1px solid #1B3A4D", borderRadius: 12 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2 text-sm">
                {summaryData.map((item) => (
                  <div key={item.name} className="flex items-center justify-between text-muted-foreground">
                    <span>{item.name}</span>
                    <span className="font-medium text-foreground">{item.value}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="mb-8 grid gap-6 lg:grid-cols-2">
            <section className="rounded-xl border border-border bg-[#0d2638] p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold tracking-[0.18em] text-primary">RISK PROFILE</p>
                  <h2 className="mt-1 text-xl font-semibold">Severity distribution</h2>
                </div>
                <CircleAlert className="h-5 w-5 text-amber-400" />
              </div>

              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={severityData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1B3A4D" />
                    <XAxis dataKey="name" stroke="#8FA3B8" tickLine={false} axisLine={false} />
                    <YAxis stroke="#8FA3B8" tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0D2638", border: "1px solid #1B3A4D", borderRadius: 12 }}
                    />
                    <Line type="monotone" dataKey="value" stroke="#19C37D" strokeWidth={3} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="rounded-xl border border-border bg-[#0d2638] p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold tracking-[0.18em] text-primary">RESOLUTION WATCH</p>
                  <h2 className="mt-1 text-xl font-semibold">Outstanding amount</h2>
                </div>
                <Wallet className="h-5 w-5 text-primary" />
              </div>

              <div className="space-y-4 text-sm">
                <div className="rounded-lg border border-border bg-[#071a2b] p-4">
                  <p className="text-muted-foreground">Unresolved amount</p>
                  <p className="mt-2 text-2xl font-semibold text-primary">
                    {formatCurrency(dashboard?.unresolved_amount ?? 0)}
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-lg border border-border bg-[#071a2b] p-4">
                    <p className="text-muted-foreground">Pending approvals</p>
                    <p className="mt-2 text-xl font-semibold text-foreground">{pendingApproval}</p>
                  </div>
                  <div className="rounded-lg border border-border bg-[#071a2b] p-4">
                    <p className="text-muted-foreground">Escalations</p>
                    <p className="mt-2 text-xl font-semibold text-foreground">{Math.max(0, transactions.filter((t) => t.severity === "CRITICAL").length)}</p>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <section className="overflow-hidden rounded-xl border border-border bg-[#0d2638]">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div>
                <p className="text-xs font-bold tracking-[0.18em] text-primary">TRANSACTION TABLE</p>
                <h2 className="mt-1 text-xl font-semibold">Financial transactions</h2>
              </div>
              <button className="rounded-md border border-primary/40 bg-primary/10 px-3 py-2 text-sm font-medium text-primary">
                Export CSV
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-[1280px] w-full border-separate border-spacing-0 text-left text-sm">
                <thead className="bg-[#071a2b] text-muted-foreground">
                  <tr>
                    <th className="p-4 font-medium">Transaction</th>
                    <th className="p-4 font-medium">Date</th>
                    <th className="p-4 font-medium">Customer</th>
                    <th className="p-4 font-medium">Reference</th>
                    <th className="p-4 font-medium">Account</th>
                    <th className="p-4 font-medium">Amount</th>
                    <th className="p-4 font-medium">Expected</th>
                    <th className="p-4 font-medium">Actual</th>
                    <th className="p-4 font-medium">Difference</th>
                    <th className="p-4 font-medium">Status</th>
                    <th className="p-4 font-medium">Severity</th>
                    <th className="p-4 font-medium">Investigation</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className="border-t border-border bg-[#0d2638] hover:bg-[#102d42]">
                      <td className="p-3">
                        <Link
                          to="/transactions/$transactionId"
                          params={{ transactionId: transaction.id }}
                          className="flex items-center gap-3"
                        >
                          <span className={`h-10 w-1 rounded-full ${getDiscrepancyBar(transaction.status, transaction.severity, transaction.difference)}`} />
                          <div>
                            <div className="font-medium text-foreground">{transaction.id}</div>
                            <div className="text-xs text-muted-foreground">{transaction.discrepancy_type ?? "No discrepancy"}</div>
                          </div>
                        </Link>
                      </td>
                      <td className="p-3 text-muted-foreground">{transaction.date}</td>
                      <td className="p-3">{transaction.customer}</td>
                      <td className="p-3 text-muted-foreground">{transaction.invoice_id}</td>
                      <td className="p-3 text-muted-foreground">{transaction.account}</td>
                      <td className="p-3 font-medium text-foreground">{formatCurrency(transaction.actual_amount, transaction.currency)}</td>
                      <td className="p-3 text-muted-foreground">{formatCurrency(transaction.expected_amount, transaction.currency)}</td>
                      <td className="p-3 text-muted-foreground">{formatCurrency(transaction.actual_amount, transaction.currency)}</td>
                      <td className={`p-3 font-medium ${transaction.difference === 0 ? "text-emerald-300" : "text-red-300"}`}>
                        {formatCurrency(transaction.difference, transaction.currency)}
                      </td>
                      <td className="p-3">
                        <span className={`inline-flex rounded-full border px-2 py-1 text-[11px] font-medium ${getStatusBadge(transaction.status)}`}>
                          {transaction.status.replaceAll("_", " ")}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className="inline-flex rounded-full border border-border bg-[#071a2b] px-2 py-1 text-[11px] font-medium text-foreground">
                          {transaction.severity}
                        </span>
                      </td>
                      <td className="p-3">
                        <Link
                          to="/transactions/$transactionId"
                          params={{ transactionId: transaction.id }}
                          className="inline-flex items-center gap-1 text-primary"
                        >
                          Open details <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

function Metric({
  label,
  value,
  detail,
  accent,
  warn,
}: {
  label: string;
  value: string;
  detail: string;
  accent?: boolean;
  warn?: boolean;
}) {
  return (
    <article className="rounded-lg border border-border bg-[#0d2638] p-5">
      <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={`mt-3 text-3xl font-semibold ${accent ? "text-primary" : warn ? "text-amber-300" : ""}`}>
        {value}
      </p>
      <p className="mt-2 text-xs text-muted-foreground">{detail}</p>
    </article>
  );
}

function Auth({
  mode,
  setMode,
  submit,
  notice,
}: {
  mode: "login" | "register";
  setMode: (mode: "login" | "register") => void;
  submit: (e: React.FormEvent<HTMLFormElement>) => void;
  notice: string;
}) {
  return (
    <main className="grid min-h-screen place-items-center bg-background p-5 text-foreground">
      <form onSubmit={submit} className="w-full max-w-md rounded-xl border border-border bg-card p-7 shadow-2xl shadow-black/20">
        <div className="mb-8 flex items-center gap-3">
          <img
            src="/logo2.jpg"
            alt="TallyFlow logo"
            className="h-12 w-12 rounded-md border border-primary/20 object-cover"
          />
          <div>
            <p className="text-xs font-bold tracking-[0.16em] text-primary">TALLY FLOW</p>
            <h1 className="font-semibold">Financial close workspace</h1>
          </div>
        </div>

        <h2 className="text-2xl font-semibold">{mode === "login" ? "Welcome back" : "Create your account"}</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {mode === "login"
            ? "Sign in to your secure finance operations workspace."
            : "New accounts begin with Analyst access."}
        </p>

        <div className="mt-6 space-y-4">
          {mode === "register" && (
            <label className="block text-sm">
              Full name
              <input
                required
                name="full_name"
                className="mt-1.5 w-full rounded-md border border-border bg-[#071a2b] px-3 py-2.5 outline-none focus:border-primary"
              />
            </label>
          )}

          <label className="block text-sm">
            Work email
            <input
              required
              type="email"
              name="email"
              className="mt-1.5 w-full rounded-md border border-border bg-[#071a2b] px-3 py-2.5 outline-none focus:border-primary"
            />
          </label>

          <label className="block text-sm">
            Password
            <input
              required
              minLength={12}
              type="password"
              name="password"
              className="mt-1.5 w-full rounded-md border border-border bg-[#071a2b] px-3 py-2.5 outline-none focus:border-primary"
            />
          </label>
        </div>

        {notice && <p className="mt-4 text-sm text-red-300">{notice}</p>}

        <button className="mt-6 w-full rounded-md bg-primary px-4 py-2.5 text-sm font-bold text-[#071a2b] hover:bg-[#4ADE80]">
          {mode === "login" ? "Sign in" : "Create account"}
        </button>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          {mode === "login" ? (
            <span>
              Need access? <button type="button" className="font-medium text-primary" onClick={() => setMode("register")}>Create an account</button>
            </span>
          ) : (
            <span>
              Already have an account? <button type="button" className="font-medium text-primary" onClick={() => setMode("login")}>Sign in</button>
            </span>
          )}
        </p>

        <div className="mt-8 grid gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-primary" /> Restricted finance workspace</div>
          <div className="flex items-center gap-2"><Users className="h-4 w-4 text-primary" /> Audit-linked approval controls</div>
          <div className="flex items-center gap-2"><Activity className="h-4 w-4 text-primary" /> Investigation evidence trails</div>
        </div>
      </form>
    </main>
  );
}
