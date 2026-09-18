import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck,
  FileCode,
  FileText,
  Filter,
  Layers,
  Menu,
  Play,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
  UserCheck,
  Users,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { apiGet, apiPost } from "../lib/api";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export const Route = createFileRoute("/$section")({ component: SectionRoute });

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
  user?: { id: number; full_name: string; email: string } | null;
};

type InvestigationRecord = {
  id: string;
  transaction_id: string;
  status: string;
  root_cause: string | null;
  recommendation: string | null;
  confidence: number | null;
  timeline: string[];
};

type DocumentRecord = {
  id: string;
  filename: string;
  document_type: string;
  file_path: string;
  status: string;
  accounting_period?: string;
  records_created?: number;
  created_at: string;
};

type UserRecord = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  transaction_count: number;
  total_balance: number;
};

type AccountRecord = {
  id: string;
  code: string;
  name: string;
  account_type: string;
  normal_balance: string;
  is_active: boolean;
  transaction_count: number;
  total_balance: number;
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
  { label: "Accounts", path: "/accounts" },
];

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

const getSeverityBadge = (sev: string) => {
  const map: Record<string, string> = {
    CRITICAL: "bg-red-950 text-red-300 border-red-800",
    HIGH: "bg-rose-950/80 text-rose-300 border-rose-700/60",
    MEDIUM: "bg-amber-950/80 text-amber-300 border-amber-700/60",
    LOW: "bg-sky-950/80 text-sky-300 border-sky-700/60",
    NONE: "bg-emerald-950/80 text-emerald-300 border-emerald-700/60",
  };
  return map[sev] ?? "bg-slate-800 text-slate-400 border-slate-700";
};

function SectionRoute() {
  const { section } = Route.useParams();
  const navigate = useNavigate();

  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [investigations, setInvestigations] = useState<InvestigationRecord[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [accounts, setAccounts] = useState<AccountRecord[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState("2026-09");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedUserTx, setSelectedUserTx] = useState<{ user: any; transactions: TransactionRecord[] } | null>(null);
  const [docPreview, setDocPreview] = useState<{ title: string; content: string } | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const months = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09"];

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (section === "transactions") {
        const query = new URLSearchParams({ period: selectedPeriod });
        if (searchQuery.trim()) query.append("q", searchQuery.trim());
        const data = await apiGet<TransactionRecord[]>(`/api/v1/transactions?${query}`);
        setTransactions(data);
      } else if (section === "reconciliation" || section === "financial-close") {
        const data = await apiGet<{ transactions: TransactionRecord[] }>("/api/v1/workspace/reconciliation-current");
        setTransactions(data.transactions || []);
      } else if (section === "discrepancies") {
        const data = await apiGet<TransactionRecord[]>("/api/v1/workspace/discrepancies");
        setTransactions(data);
      } else if (section === "investigations") {
        const data = await apiGet<InvestigationRecord[]>("/api/v1/workspace/investigations");
        setInvestigations(data);
      } else if (section === "approvals") {
        const data = await apiGet<TransactionRecord[]>("/api/v1/workspace/approvals");
        setTransactions(data);
      } else if (section === "reconciled") {
        const data = await apiGet<TransactionRecord[]>(`/api/v1/workspace/reconciled?period=${selectedPeriod}`);
        setTransactions(data);
      } else if (section === "documents") {
        const q = searchQuery.trim() ? `?q=${encodeURIComponent(searchQuery.trim())}` : "";
        const data = await apiGet<DocumentRecord[]>(`/api/v1/workspace/documents${q}`);
        setDocuments(data);
      } else if (section === "accounts") {
        const q = searchQuery.trim() ? `?q=${encodeURIComponent(searchQuery.trim())}` : "";
        const data = await apiGet<AccountRecord[]>(`/api/v1/workspace/accounts${q}`);
        setAccounts(data);
      }
    } catch (err) {
      toast.error(`Failed to load ${section}`, {
        description: err instanceof Error ? err.message : "Error connecting to service.",
      });
    } finally {
      setLoading(false);
    }
  }, [section, selectedPeriod, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const runReconcile = async () => {
    setActionLoading("reconcile");
    try {
      const res = await apiPost<{ matched: number; discrepancies: number }>("/api/v1/periods/2026-09/reconcile");
      toast.success("Period 2026-09 Reconciled", {
        description: `Matched: ${res.matched ?? 0} · Discrepancies: ${res.discrepancies ?? 0}`,
      });
      loadData();
    } catch (err) {
      toast.error("Reconciliation failed", {
        description: err instanceof Error ? err.message : "Unexpected error",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const viewAccountTransactions = async (accountId: string) => {
    try {
      const data = await apiGet<{ account: any; transactions: TransactionRecord[] }>(
        `/api/v1/workspace/accounts/${accountId}/transactions`
      );
      setSelectedUserTx({
        user: {
          id: data.account.id,
          full_name: `${data.account.code} - ${data.account.name}`,
          email: `${data.account.account_type} (${data.account.normal_balance})`,
          role: data.account.account_type.toUpperCase(),
          total_balance: data.account.total_balance,
        },
        transactions: data.transactions,
      });
    } catch (err) {
      toast.error("Failed to load account transactions");
    }
  };

  const viewUserTransactions = async (userId: number) => {
    try {
      const data = await apiGet<{ user: any; transactions: TransactionRecord[] }>(
        `/api/v1/workspace/users/${userId}/transactions`
      );
      setSelectedUserTx(data);
    } catch (err) {
      toast.error("Failed to load user transactions");
    }
  };

  const previewDocument = async (doc: DocumentRecord) => {
    if (doc.filename.toLowerCase().startsWith("inv-")) {
      const invId = doc.filename.split("_")[0];
      try {
        const res = await apiGet<{ content: string }>(`/api/v1/evidence/${invId}`);
        setDocPreview({ title: doc.filename, content: res.content });
        return;
      } catch (e) {}
    }
    setDocPreview({
      title: doc.filename,
      content: `Document ID: ${doc.id}\nType: ${doc.document_type}\nLocation: ${doc.file_path}\nStatus: ${doc.status}\nCreated: ${new Date(doc.created_at).toLocaleString()}`,
    });
  };

  const filteredTxs = transactions.filter((t) => {
    if (!searchQuery.trim() || section === "transactions") return true;
    const q = searchQuery.toLowerCase();
    return (
      t.customer.toLowerCase().includes(q) ||
      t.id.toLowerCase().includes(q) ||
      t.invoice_id.toLowerCase().includes(q) ||
      t.account.toLowerCase().includes(q)
    );
  });

  const reconciliationChartData = [
    { label: "Matched", count: transactions.filter((transaction) => ["RECONCILED", "RESOLVED"].includes(transaction.status)).length },
    { label: "Variance", count: transactions.filter((transaction) => transaction.difference !== 0).length },
    { label: "Pending", count: transactions.filter((transaction) => transaction.difference === 0 && !["RECONCILED", "RESOLVED"].includes(transaction.status)).length },
  ];

  return (
    <div className="min-h-screen bg-[#071A2B] text-foreground">
      {/* Mobile Sidebar */}
      {mobileNavOpen && (
        <button
          type="button"
          aria-label="Close menu"
          onClick={() => setMobileNavOpen(false)}
          className="fixed inset-0 z-50 bg-black/70 md:hidden"
        />
      )}
      <aside
        aria-label="Mobile navigation"
        style={{ scrollbarWidth: "none" }}
        className={`fixed inset-y-0 right-0 z-60 w-64 border-l border-border bg-[#0a2033] p-5 shadow-2xl transition-transform duration-200 scrollbar-none md:hidden ${
          mobileNavOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo2.jpg" alt="Logo" className="h-7 w-7 rounded border border-primary/30 object-cover" />
            <span className="text-xs font-bold tracking-widest text-primary">TALLY FLOW</span>
          </div>
          <button onClick={() => setMobileNavOpen(false)} className="rounded p-1 text-muted-foreground hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav style={{ scrollbarWidth: "none" }} className="space-y-1 overflow-y-auto scrollbar-none text-sm">
          {navigationItems.map((item) => (
            <Link
              key={item.label}
              to={item.path === "/" ? "/" : "/$section"}
              params={item.path === "/" ? undefined : { section: item.path.slice(1) }}
              onClick={() => setMobileNavOpen(false)}
              className={`block rounded-lg px-3 py-2.5 font-medium transition ${
                (item.path.slice(1) || "/") === (section || "/")
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
            <p className="text-xs font-medium text-muted-foreground">Financial Close Engine</p>
          </div>
        </div>
        <nav className="space-y-1 text-sm font-medium">
          {navigationItems.map((item) => (
            <Link
              key={item.label}
              to={item.path === "/" ? "/" : "/$section"}
              params={item.path === "/" ? undefined : { section: item.path.slice(1) }}
              className={`block rounded-lg px-3 py-2.5 transition ${
                (item.path.slice(1) || "/") === (section || "/")
                  ? "bg-primary/20 text-primary border border-primary/30 shadow-sm"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="lg:pl-64">
        {/* Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-[#0a2033]/90 px-5 backdrop-blur md:px-8">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-base font-bold capitalize text-white md:text-lg">
                {section.replace("-", " ")}
              </h1>
              <p className="text-xs text-muted-foreground">
                Financial Close Platform · Period <span className="font-semibold text-primary">{selectedPeriod}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileNavOpen(true)}
              className="rounded-lg border border-border bg-card p-2 text-muted-foreground hover:text-white lg:hidden"
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-[#071a2b] px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:bg-card hover:text-white"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
            </Link>
            <button
              onClick={loadData}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-[#071a2b] px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-white"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
        </header>

        <main className="p-5 md:p-8 space-y-6">
          {/* SECTION: TRANSACTIONS */}
          {section === "transactions" && (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                {/* Month switcher tabs */}
                <div className="flex items-center gap-1.5 rounded-xl border border-border bg-[#0a2033] p-1.5">
                  {months.map((m) => {
                    const label = new Date(`${m}-01`).toLocaleDateString("en-US", { month: "short", year: "numeric" });
                    return (
                      <button
                        key={m}
                        onClick={() => setSelectedPeriod(m)}
                        className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
                          selectedPeriod === m
                            ? "bg-primary text-[#071a2b] shadow"
                            : "text-muted-foreground hover:text-white"
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>

                <div className="relative min-w-[240px]">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by customer, ID, invoice..."
                    className="w-full rounded-xl border border-border bg-[#0a2033] py-2 pl-9 pr-4 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-[#0a2033] p-5 shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-white">Reconciliation Status</h3>
                    <p className="text-xs text-muted-foreground">Invoice matching results for the active period</p>
                  </div>
                  <BarChart3 className="h-4 w-4 text-primary" />
                </div>
                <div className="mt-4 h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={reconciliationChartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid stroke="#1B3A4D" vertical={false} />
                      <XAxis dataKey="label" tick={{ fill: "#8FA3B8", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis allowDecimals={false} tick={{ fill: "#8FA3B8", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip cursor={{ fill: "rgba(255,255,255,0.04)" }} contentStyle={{ background: "#0d2638", border: "1px solid #1B3A4D", borderRadius: 12, color: "#F5F7FA" }} />
                      <Bar dataKey="count" fill="#19C37D" radius={[5, 5, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
                <div className="border-b border-border bg-[#0d2638] px-5 py-3">
                  <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    All Transactions for {selectedPeriod} ({transactions.length} records)
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Click any transaction row to open its full evidence graph and investigation details.
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border/60 text-muted-foreground">
                        <th className="px-5 py-3 font-semibold">Date</th>
                        <th className="px-5 py-3 font-semibold">Transaction ID</th>
                        <th className="px-5 py-3 font-semibold">Customer</th>
                        <th className="px-5 py-3 font-semibold">Invoice ID</th>
                        <th className="px-5 py-3 font-semibold text-right">Expected</th>
                        <th className="px-5 py-3 font-semibold text-right">Actual</th>
                        <th className="px-5 py-3 font-semibold text-right">Difference</th>
                        <th className="px-5 py-3 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {transactions.length === 0 ? (
                        <tr>
                          <td colSpan={8} className="px-5 py-8 text-center text-muted-foreground">
                            {loading ? "Loading transactions..." : "No transactions found for this period."}
                          </td>
                        </tr>
                      ) : (
                        transactions.map((tx) => (
                          <tr
                            key={tx.id}
                            onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                            className="cursor-pointer transition hover:bg-white/5"
                          >
                            <td className="whitespace-nowrap px-5 py-3.5 text-muted-foreground">{tx.date}</td>
                            <td className="whitespace-nowrap px-5 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                            <td className="px-5 py-3.5 font-medium text-white">{tx.customer}</td>
                            <td className="whitespace-nowrap px-5 py-3.5 font-mono text-muted-foreground">{tx.invoice_id}</td>
                            <td className="whitespace-nowrap px-5 py-3.5 text-right text-muted-foreground">{formatCurrency(tx.expected_amount)}</td>
                            <td className="whitespace-nowrap px-5 py-3.5 text-right font-medium text-white">{formatCurrency(tx.actual_amount)}</td>
                            <td className={`whitespace-nowrap px-5 py-3.5 text-right font-bold ${tx.difference !== 0 ? "text-rose-400" : "text-emerald-400"}`}>
                              {tx.difference !== 0 ? formatCurrency(tx.difference) : "$0.00"}
                            </td>
                            <td className="whitespace-nowrap px-5 py-3.5">
                              <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(tx.status)}`}>
                                {tx.status.replaceAll("_", " ")}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* SECTION: RECONCILIATION */}
          {(section === "reconciliation" || section === "financial-close") && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-primary/30 bg-gradient-to-r from-emerald-950/40 via-[#0a2033] to-[#0a2033] p-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <div className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
                      <Clock className="h-3.5 w-3.5" /> CURRENT CLOSE PERIOD: SEPTEMBER 2026 (2026-09)
                    </div>
                    <h2 className="mt-2 text-xl font-bold text-white">Period Ready for Reconciliation</h2>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Only the active month is presented for financial close reconciliation according to policy FIN-009.
                    </p>
                  </div>
                  <button
                    onClick={runReconcile}
                    disabled={actionLoading === "reconcile"}
                    className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold text-[#071a2b] shadow hover:bg-[#4ADE80] disabled:opacity-50"
                  >
                    <Play className="h-4 w-4" /> {actionLoading === "reconcile" ? "Reconciling..." : "Run Period Reconciliation"}
                  </button>
                </div>

                <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="rounded-xl border border-border/60 bg-[#071a2b]/60 p-4">
                    <p className="text-xs text-muted-foreground">Total Transactions in Period</p>
                    <p className="mt-1 text-2xl font-bold text-white">{transactions.length}</p>
                  </div>
                  <div className="rounded-xl border border-emerald-500/30 bg-[#071a2b]/60 p-4">
                    <p className="text-xs text-emerald-400">Matched & Reconciled</p>
                    <p className="mt-1 text-2xl font-bold text-emerald-400">
                      {transactions.filter((t) => ["RECONCILED", "RESOLVED"].includes(t.status)).length}
                    </p>
                  </div>
                  <div className="rounded-xl border border-rose-500/30 bg-[#071a2b]/60 p-4">
                    <p className="text-xs text-rose-400">Discrepancies Flagged</p>
                    <p className="mt-1 text-2xl font-bold text-rose-400">
                      {transactions.filter((t) => t.difference !== 0).length}
                    </p>
                  </div>
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
                <div className="border-b border-border bg-[#0d2638] px-5 py-3">
                  <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    September 2026 Transactions ({transactions.length} items)
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border/60 text-muted-foreground">
                        <th className="px-5 py-3 font-semibold">Date</th>
                        <th className="px-5 py-3 font-semibold">Transaction ID</th>
                        <th className="px-5 py-3 font-semibold">Customer</th>
                        <th className="px-5 py-3 font-semibold">Invoice ID</th>
                        <th className="px-5 py-3 font-semibold text-right">Expected</th>
                        <th className="px-5 py-3 font-semibold text-right">Actual</th>
                        <th className="px-5 py-3 font-semibold text-right">Variance</th>
                        <th className="px-5 py-3 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {transactions.map((tx) => (
                        <tr
                          key={tx.id}
                          onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                          className="cursor-pointer transition hover:bg-white/5"
                        >
                          <td className="px-5 py-3.5 text-muted-foreground">{tx.date}</td>
                          <td className="px-5 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                          <td className="px-5 py-3.5 font-medium text-white">{tx.customer}</td>
                          <td className="px-5 py-3.5 font-mono text-muted-foreground">{tx.invoice_id}</td>
                          <td className="px-5 py-3.5 text-right text-muted-foreground">{formatCurrency(tx.expected_amount)}</td>
                          <td className="px-5 py-3.5 text-right font-medium text-white">{formatCurrency(tx.actual_amount)}</td>
                          <td className={`px-5 py-3.5 text-right font-bold ${tx.difference !== 0 ? "text-rose-400" : "text-emerald-400"}`}>
                            {formatCurrency(tx.difference)}
                          </td>
                          <td className="px-5 py-3.5">
                            <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(tx.status)}`}>
                              {tx.status.replaceAll("_", " ")}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* SECTION: DISCREPANCIES */}
          {section === "discrepancies" && (
            <div className="space-y-5">
              <div className="rounded-2xl border border-rose-500/30 bg-[#0a2033] p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-white">Discrepancy Resolution Watch</h2>
                    <p className="text-xs text-muted-foreground">
                      All accounts and transactions requiring active reconciliation, investigation, or managerial approval.
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Unresolved Total</p>
                    <p className="text-xl font-bold text-rose-400">
                      {formatCurrency(transactions.reduce((acc, t) => acc + Math.abs(t.difference), 0))}
                    </p>
                  </div>
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border/60 text-muted-foreground">
                        <th className="px-5 py-3 font-semibold">Transaction ID</th>
                        <th className="px-5 py-3 font-semibold">Customer</th>
                        <th className="px-5 py-3 font-semibold">Discrepancy Type</th>
                        <th className="px-5 py-3 font-semibold">Severity</th>
                        <th className="px-5 py-3 font-semibold text-right">Variance</th>
                        <th className="px-5 py-3 font-semibold">Status</th>
                        <th className="px-5 py-3 font-semibold text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {filteredTxs.map((tx) => (
                        <tr
                          key={tx.id}
                          onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                          className="cursor-pointer transition hover:bg-white/5"
                        >
                          <td className="px-5 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                          <td className="px-5 py-3.5 font-medium text-white">{tx.customer}</td>
                          <td className="px-5 py-3.5 text-muted-foreground">
                            {tx.discrepancy_type?.replaceAll("_", " ") || "Variance Detected"}
                          </td>
                          <td className="px-5 py-3.5">
                            <span className={`inline-flex rounded border px-2 py-0.5 text-[10px] font-bold ${getSeverityBadge(tx.severity)}`}>
                              {tx.severity}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-right font-bold text-rose-400">
                            {formatCurrency(tx.difference)}
                          </td>
                          <td className="px-5 py-3.5">
                            <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(tx.status)}`}>
                              {tx.status.replaceAll("_", " ")}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <span className="inline-flex items-center gap-1 text-primary hover:underline">
                              Investigate <ArrowRight className="h-3 w-3" />
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* SECTION: INVESTIGATIONS */}
          {section === "investigations" && (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">LangGraph AI Investigations</h2>
                  <p className="text-xs text-muted-foreground">
                    Multi-node autonomous agents running root-cause analysis via Hugging Face Inference Providers.
                  </p>
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
                  <Sparkles className="h-3.5 w-3.5" /> Model: meta-llama/Llama-3.3-70B-Instruct
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {investigations.map((inv) => (
                  <div
                    key={inv.id}
                    className="flex flex-col justify-between rounded-2xl border border-border bg-[#0a2033] p-5 transition hover:border-primary/50"
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm font-bold text-primary">{inv.id}</span>
                        <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(inv.status)}`}>
                          {inv.status}
                        </span>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Linked Transaction</p>
                        <p className="font-mono text-xs font-bold text-white">{inv.transaction_id}</p>
                      </div>
                      {inv.root_cause && (
                        <div className="rounded-xl border border-border/60 bg-[#071a2b] p-3 text-xs">
                          <p className="font-semibold text-white">Root Cause Hypothesis</p>
                          <p className="mt-1 text-muted-foreground">{inv.root_cause}</p>
                        </div>
                      )}
                      {inv.recommendation && (
                        <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-3 text-xs text-emerald-300">
                          <p className="font-semibold">AI Recommendation</p>
                          <p className="mt-1">{inv.recommendation}</p>
                        </div>
                      )}
                      {inv.confidence !== null && (
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>Confidence Score</span>
                          <span className="font-bold text-white">{(inv.confidence * 100).toFixed(0)}%</span>
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: inv.transaction_id } })}
                      className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl border border-primary/30 bg-primary/10 py-2.5 text-xs font-bold text-primary hover:bg-primary hover:text-[#071a2b]"
                    >
                      Inspect Evidence Graph & Act <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION: APPROVALS */}
          {section === "approvals" && (
            <div className="space-y-5">
              <div>
                <h2 className="text-lg font-bold text-white">Financial Approval Queue</h2>
                <p className="text-xs text-muted-foreground">
                  Human-in-the-loop sign-offs for adjustments, discounts, and payments governed by FIN-010 matrix.
                </p>
              </div>

              <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border/60 text-muted-foreground">
                        <th className="px-5 py-3 font-semibold">Transaction</th>
                        <th className="px-5 py-3 font-semibold">Customer</th>
                        <th className="px-5 py-3 font-semibold">Discrepancy</th>
                        <th className="px-5 py-3 font-semibold text-right">Variance</th>
                        <th className="px-5 py-3 font-semibold">Required Approver</th>
                        <th className="px-5 py-3 font-semibold text-right">Decision</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {transactions.map((tx) => (
                        <tr
                          key={tx.id}
                          onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                          className="cursor-pointer transition hover:bg-white/5"
                        >
                          <td className="px-5 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                          <td className="px-5 py-3.5 font-medium text-white">{tx.customer}</td>
                          <td className="px-5 py-3.5 text-muted-foreground">{tx.discrepancy_type || "Variance"}</td>
                          <td className="px-5 py-3.5 text-right font-bold text-rose-400">{formatCurrency(tx.difference)}</td>
                          <td className="px-5 py-3.5 font-semibold text-yellow-300">
                            {tx.status === "AWAITING_MANAGER_APPROVAL" ? "Finance Manager" : "Finance Admin / Analyst"}
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <span className="inline-flex rounded-lg bg-primary/20 px-3 py-1 font-bold text-primary hover:bg-primary hover:text-[#071a2b]">
                              Review & Decide
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* SECTION: RECONCILED */}
          {section === "reconciled" && (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">Reconciled Accounts</h2>
                  <p className="text-xs text-muted-foreground">
                    Historical verified transactions with balanced accounts and zero variance.
                  </p>
                </div>
                <div className="flex items-center gap-1.5 rounded-xl border border-border bg-[#0a2033] p-1.5">
                  {months.map((m) => (
                    <button
                      key={m}
                      onClick={() => setSelectedPeriod(m)}
                      className={`rounded-lg px-3 py-1 text-xs font-bold ${
                        selectedPeriod === m ? "bg-primary text-[#071a2b]" : "text-muted-foreground"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border/60 text-muted-foreground">
                        <th className="px-5 py-3 font-semibold">Date</th>
                        <th className="px-5 py-3 font-semibold">Transaction ID</th>
                        <th className="px-5 py-3 font-semibold">Customer</th>
                        <th className="px-5 py-3 font-semibold">Account</th>
                        <th className="px-5 py-3 font-semibold text-right">Amount</th>
                        <th className="px-5 py-3 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {transactions.map((tx) => (
                        <tr
                          key={tx.id}
                          onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                          className="cursor-pointer transition hover:bg-white/5"
                        >
                          <td className="px-5 py-3.5 text-muted-foreground">{tx.date}</td>
                          <td className="px-5 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                          <td className="px-5 py-3.5 font-medium text-white">{tx.customer}</td>
                          <td className="px-5 py-3.5 text-muted-foreground">{tx.account}</td>
                          <td className="px-5 py-3.5 text-right font-medium text-emerald-400">{formatCurrency(tx.actual_amount)}</td>
                          <td className="px-5 py-3.5">
                            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-500/15 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300">
                              <CheckCircle2 className="h-3 w-3" /> Reconciled
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* SECTION: DOCUMENTS */}
          {section === "documents" && (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-white">Document Intelligence & Corporate Policies</h2>
                  <p className="text-xs text-muted-foreground">
                    Search and review financial governance policies, close procedures, and customer invoices.
                  </p>
                </div>
                <div className="relative min-w-[260px]">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search documents and policies..."
                    className="w-full rounded-xl border border-border bg-[#0a2033] py-2 pl-9 pr-4 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    onClick={() => previewDocument(doc)}
                    className="cursor-pointer space-y-3 rounded-2xl border border-border bg-[#0a2033] p-5 transition hover:border-primary/50 hover:bg-[#0c2439]"
                  >
                    <div className="flex items-center justify-between">
                      <FileText className="h-6 w-6 text-primary" />
                      <span className="rounded-full border border-border bg-[#071a2b] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                        {doc.document_type}
                      </span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">{doc.filename}</h3>
                      <p className="mt-1 truncate font-mono text-[11px] text-muted-foreground">{doc.file_path}</p>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                      <span>Status: {doc.status}</span>
                      <span className="text-primary hover:underline">View content →</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION: ACCOUNTS (General Ledger Accounts from accounts table) */}
          {section === "accounts" && (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-white">General Ledger Accounts</h2>
                  <p className="text-xs text-muted-foreground">
                    Inspect chart of accounts, balances, account types, and assigned transaction volume.
                  </p>
                </div>
                <div className="relative min-w-[260px]">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search accounts by code, name, type..."
                    className="w-full rounded-xl border border-border bg-[#0a2033] py-2 pl-9 pr-4 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border/60 text-muted-foreground">
                        <th className="px-5 py-3 font-semibold">Account Code</th>
                        <th className="px-5 py-3 font-semibold">Account Name</th>
                        <th className="px-5 py-3 font-semibold">Account Type</th>
                        <th className="px-5 py-3 font-semibold">Normal Balance</th>
                        <th className="px-5 py-3 font-semibold">Status</th>
                        <th className="px-5 py-3 font-semibold text-right">Transactions</th>
                        <th className="px-5 py-3 font-semibold text-right">Total Balance</th>
                        <th className="px-5 py-3 font-semibold text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {accounts.map((acct) => (
                        <tr key={acct.id} className="transition hover:bg-white/5">
                          <td className="px-5 py-3.5 font-mono text-muted-foreground">{acct.code}</td>
                          <td className="px-5 py-3.5 font-bold text-white">{acct.name}</td>
                          <td className="px-5 py-3.5 text-muted-foreground">{acct.account_type}</td>
                          <td className="px-5 py-3.5">
                            <span
                              className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${
                                acct.account_type === "Asset"
                                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                                  : acct.account_type === "Liability"
                                  ? "border-rose-500/40 bg-rose-500/10 text-rose-300"
                                  : acct.account_type === "Revenue"
                                  ? "border-sky-500/40 bg-sky-500/10 text-sky-300"
                                  : "border-yellow-500/40 bg-yellow-500/10 text-yellow-300"
                              }`}
                            >
                              {acct.normal_balance?.toUpperCase() || acct.account_type}
                            </span>
                          </td>
                          <td className="px-5 py-3.5">
                            <span className="inline-flex items-center gap-1 text-emerald-400">
                              <CheckCircle2 className="h-3 w-3" /> {acct.is_active ? "Active" : "Inactive"}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-right font-medium text-white">{acct.transaction_count}</td>
                          <td className="px-5 py-3.5 text-right font-bold text-emerald-400">
                            {formatCurrency(acct.total_balance)}
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <button
                              onClick={() => viewAccountTransactions(acct.id)}
                              className="inline-flex rounded-lg border border-primary/30 bg-primary/10 px-3 py-1 font-semibold text-primary hover:bg-primary hover:text-[#071a2b]"
                            >
                              View Records
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* User Transactions Modal */}
      {selectedUserTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-3xl rounded-2xl border border-border bg-[#0d2638] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div>
                <h3 className="text-base font-bold text-white">
                  Transactions for {selectedUserTx.user.full_name} ({selectedUserTx.user.email})
                </h3>
                <p className="text-xs text-muted-foreground">
                  Role: <span className="font-semibold text-primary">{selectedUserTx.user.role}</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedUserTx(null)}
                className="rounded-lg p-1 text-muted-foreground hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 max-h-96 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="py-2">Date</th>
                    <th className="py-2">ID</th>
                    <th className="py-2">Customer</th>
                    <th className="py-2 text-right">Amount</th>
                    <th className="py-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {selectedUserTx.transactions.map((tx) => (
                    <tr
                      key={tx.id}
                      onClick={() => {
                        setSelectedUserTx(null);
                        navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } });
                      }}
                      className="cursor-pointer hover:bg-white/5"
                    >
                      <td className="py-2.5 text-muted-foreground">{tx.date}</td>
                      <td className="py-2.5 font-mono text-primary font-bold">{tx.id}</td>
                      <td className="py-2.5 text-white">{tx.customer}</td>
                      <td className="py-2.5 text-right font-medium text-emerald-400">{formatCurrency(tx.actual_amount)}</td>
                      <td className="py-2.5">
                        <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold ${getStatusBadge(tx.status)}`}>
                          {tx.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Document Preview Modal */}
      {docPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-border bg-[#0d2638] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <h3 className="font-bold text-white">{docPreview.title}</h3>
              <button onClick={() => setDocPreview(null)} className="rounded-lg p-1 text-muted-foreground hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <pre className="mt-4 max-h-[480px] overflow-y-auto whitespace-pre-wrap rounded-xl border border-border bg-[#071a2b] p-4 text-xs font-mono text-slate-300">
              {docPreview.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
