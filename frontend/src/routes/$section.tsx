import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  ArrowLeft,
  Bell,
  Menu,
  LogOut,
  RefreshCw,
  Sparkles,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { apiGet, apiPost, clearToken } from "../lib/api";
import { useNotifications } from "../hooks/useNotifications";
import { AdminSidebar, navigationItems } from "../components/admin/AdminSidebar";
import { UnauthorizedView } from "../components/common/UnauthorizedView";
import { TransactionsSection } from "../components/admin/sections/TransactionsSection";
import { ReconciliationSection } from "../components/admin/sections/ReconciliationSection";
import { DiscrepanciesSection } from "../components/admin/sections/DiscrepanciesSection";
import { InvestigationsSection } from "../components/admin/sections/InvestigationsSection";
import { ApprovalsSection } from "../components/admin/sections/ApprovalsSection";
import { ReconciledSection } from "../components/admin/sections/ReconciledSection";
import { DocumentsSection } from "../components/admin/sections/DocumentsSection";
import { AccountsSection } from "../components/admin/sections/AccountsSection";
import {
  AccountRecord,
  DocumentRecord,
  InvestigationRecord,
  TransactionRecord,
  UserRecord,
  formatCurrency,
  getStatusBadge,
} from "../components/admin/sections/types";

export const Route = createFileRoute("/$section")({ component: SectionRoute });

type UserAccount = { id: number; full_name: string; email: string; role: string };

function SectionRoute() {
  const { section } = Route.useParams();
  const navigate = useNavigate();

  const [user, setUser] = useState<UserAccount | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [investigations, setInvestigations] = useState<InvestigationRecord[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [accounts, setAccounts] = useState<AccountRecord[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState("2026-09");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedUserTx, setSelectedUserTx] = useState<any | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);

  const [docPreview, setDocPreview] = useState<{ title: string; content: string } | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const months = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09"];
  const { notifications, unreadCount, dismiss } = useNotifications(!!user);

  // Authenticate and fetch user role
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
        setUser(userData);
      })
      .catch(() => {
        localStorage.removeItem("financial-close-token");
        setUser(null);
      })
      .finally(() => setIsCheckingAuth(false));
  }, []);

  const loadData = useCallback(async () => {
    if (!user || user.role === "REGULAR_USER") return;
    setLoading(true);
    try {
      if (section === "transactions") {
        const query = new URLSearchParams({ period: selectedPeriod });
        if (searchQuery.trim()) query.append("q", searchQuery.trim());
        const data = await apiGet<TransactionRecord[]>(`/api/v1/transactions?${query}`);
        setTransactions(data);
      } else if (section === "reconciliation" || section === "financial-close") {
        const data = await apiGet<{ transactions: TransactionRecord[] }>(`/api/v1/workspace/reconciliation-current?period=${selectedPeriod}`);
        setTransactions(data.transactions || []);
      } else if (section === "discrepancies") {
        const data = await apiGet<TransactionRecord[]>(`/api/v1/workspace/discrepancies?period=${selectedPeriod}`);
        setTransactions(data);
      } else if (section === "investigations") {
        const data = await apiGet<InvestigationRecord[]>("/api/v1/workspace/investigations");
        setInvestigations(data);
      } else if (section === "approvals") {
        const data = await apiGet<TransactionRecord[]>(`/api/v1/workspace/approvals?period=${selectedPeriod}`);
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
  }, [section, selectedPeriod, searchQuery, user]);

  useEffect(() => {
    if (user && user.role !== "REGULAR_USER") {
      loadData();
    }
  }, [user, loadData]);

  const runReconcile = async () => {
    setActionLoading("reconcile");
    try {
      const res = await apiPost<{ matched: number; discrepancies: number }>(`/api/v1/periods/${selectedPeriod}/reconcile`);
      toast.success(`Period ${selectedPeriod} Reconciled`, {
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
      const data = await apiGet<{
        account: any;
        customer: any;
        transactions: TransactionRecord[];
        documents: any[];
        ledger_entries: any[];
        summary: any;
      }>(`/api/v1/workspace/accounts/${accountId}/transactions`);
      setSelectedUserTx(data);
    } catch (err) {
      toast.error("Failed to load account transactions");
    }
  };

  const handleSignOut = async () => {
    try {
      await apiPost("/api/v1/auth/logout");
    } catch {
      // Local session cleanup still happens if the backend is unavailable.
    } finally {
      clearToken();
      window.location.assign("/");
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

  if (isCheckingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#071A2B]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-xs font-bold tracking-widest text-primary">AUTHENTICATING...</p>
        </div>
      </div>
    );
  }

  // Regular user attempting to access admin sections -> UNAUTHORIZED
  if (!user || user.role === "REGULAR_USER") {
    return (
      <div className="min-h-screen bg-[#071A2B] text-foreground">
        <header className="flex h-16 items-center justify-between border-b border-border bg-[#0a2033] px-6 md:px-12">
          <div className="flex items-center gap-3">
            <img src="/logo2.jpg" alt="Logo" className="h-8 w-8 rounded-lg border border-primary/30 object-cover" />
            <div>
              <span className="text-[10px] font-bold tracking-widest text-primary">TALLY FLOW</span>
              <p className="text-xs font-semibold text-white">Financial Close Platform</p>
            </div>
          </div>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-[#071a2b] px-3.5 py-1.5 text-xs font-semibold text-muted-foreground hover:text-white"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Return Home
          </Link>
        </header>
        <UnauthorizedView userRole={user?.role || "GUEST"} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#071A2B] text-foreground">
      <AdminSidebar
        currentPath={`/${section}`}
        mobileOpen={mobileNavOpen}
        setMobileOpen={setMobileNavOpen}
      />

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
            <div className="hidden items-center gap-2 rounded-full border border-primary/30 bg-[#071a2b] px-2 py-1 text-xs font-medium text-primary sm:flex">
              <Sparkles className="h-3.5 w-3.5" /> Inference Online
            </div>
            <button
              onClick={() => setMobileNavOpen(true)}
              className="rounded-lg border border-border bg-card p-2 text-muted-foreground hover:text-white lg:hidden"
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            
            <button
              onClick={loadData}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-[#071a2b] px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-white"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative rounded-lg border border-border bg-[#071a2b] p-2 text-muted-foreground hover:text-white"
                aria-label="Notifications"
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
                    <button onClick={() => setShowNotifications(false)} className="text-muted-foreground hover:text-white" aria-label="Close notifications">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <div className="mt-2 max-h-64 space-y-2 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <p className="py-4 text-center text-xs text-muted-foreground">No new notifications</p>
                    ) : (
                      notifications.map((notification) => (
                        <div key={notification.id} className="flex items-start justify-between rounded-lg bg-black/20 p-2 text-xs">
                          <div>
                            <p className="font-semibold text-white">{notification.event.replaceAll("_", " ")}</p>
                            <p className="text-muted-foreground">{notification.message}</p>
                          </div>
                          <button onClick={() => dismiss(notification.id)} className="text-muted-foreground hover:text-white" aria-label="Dismiss notification">
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            <span className="hidden text-xs font-semibold text-white md:inline">{user.role}</span>
            <button
              onClick={handleSignOut}
              className="hidden items-center gap-1.5 rounded-md border border-border bg-primary/10 px-3.5 py-2 text-xs font-semibold text-primary sm:inline-flex"
            >
              <LogOut className="h-3.5 w-3.5" /> Sign out
            </button>
          </div>
        </header>

        <main className="p-5 md:p-8 space-y-6">
          <Link
              to="/"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-[#071a2b] px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:bg-card hover:text-white"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
            </Link>
          {(["financial-close", "reconciliation", "discrepancies", "approvals"] as string[]).includes(section) && (
            <div className="flex w-full items-center gap-1 overflow-x-auto rounded-xl border border-border bg-[#071a2b] p-1.5">
              {months.map((month) => (
                <button
                  key={month}
                  onClick={() => setSelectedPeriod(month)}
                  className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-bold transition ${
                    selectedPeriod === month
                      ? "bg-primary text-[#071a2b] shadow"
                      : "text-muted-foreground hover:text-white"
                  }`}
                >
                  {new Date(`${month}-01`).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
                </button>
              ))}
            </div>
          )}
          {section === "transactions" && (
            <TransactionsSection
              transactions={transactions}
              selectedPeriod={selectedPeriod}
              setSelectedPeriod={setSelectedPeriod}
              months={months}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              loading={loading}
            />
          )}

          {(section === "reconciliation" || section === "financial-close") && (
            <ReconciliationSection
              transactions={transactions}
              selectedPeriod={selectedPeriod}
              runReconcile={runReconcile}
              actionLoading={actionLoading}
            />
          )}

          {section === "discrepancies" && (
            <DiscrepanciesSection transactions={transactions} selectedPeriod={selectedPeriod} />
          )}

          {section === "investigations" && (
            <InvestigationsSection investigations={investigations} />
          )}

          {section === "approvals" && (
            <ApprovalsSection transactions={transactions} selectedPeriod={selectedPeriod} />
          )}

          {section === "reconciled" && (
            <ReconciledSection
              transactions={transactions}
              selectedPeriod={selectedPeriod}
              setSelectedPeriod={setSelectedPeriod}
              months={months}
            />
          )}

          {section === "documents" && (
            <DocumentsSection
              documents={documents}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              previewDocument={previewDocument}
            />
          )}

          {section === "accounts" && (
            <AccountsSection
              accounts={accounts}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              viewAccountTransactions={viewAccountTransactions}
            />
          )}
        </main>
      </div>

      {/* Rich Account Review & Detailed Records Modal */}
      {selectedUserTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-4xl rounded-2xl border border-border bg-[#0d2638] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header & Customer Profile */}
            <div className="border-b border-border bg-[#0a2033] p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-md border border-primary/40 bg-primary/10 px-2 py-0.5 font-mono text-[10px] font-bold text-primary">
                      ACCOUNT {selectedUserTx.account?.code || selectedUserTx.user?.id}
                    </span>
                    <span className="rounded-md border border-purple-500/40 bg-purple-500/10 px-2 py-0.5 font-mono text-[10px] font-bold text-purple-300">
                      {selectedUserTx.customer?.customer_tier || "Enterprise Tier"}
                    </span>
                    <span className="rounded-md border border-border bg-[#071a2b] px-2 py-0.5 text-[10px] font-bold text-muted-foreground">
                      Terms: {selectedUserTx.customer?.payment_terms || "NET30"}
                    </span>
                  </div>
                  <h3 className="mt-1.5 text-lg font-bold text-white">
                    {selectedUserTx.account?.name || selectedUserTx.user?.full_name}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Customer: <span className="font-semibold text-slate-200">{selectedUserTx.customer?.legal_name || selectedUserTx.customer?.name || "Corporate Customer"}</span> · Email: <span className="text-primary">{selectedUserTx.customer?.contact_email || selectedUserTx.user?.email}</span>
                  </p>
                </div>
                <button
                  onClick={() => setSelectedUserTx(null)}
                  className="rounded-xl border border-border bg-[#071a2b] p-2 text-muted-foreground hover:border-primary hover:text-white transition"
                  title="Close modal"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* KPI Strip */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-xl border border-border bg-[#071a2b] p-3">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground">Total Money Spent</div>
                  <div className="mt-0.5 font-mono text-sm font-bold text-emerald-400">
                    {formatCurrency(selectedUserTx.customer?.total_spent ?? selectedUserTx.user?.total_balance ?? 0)}
                  </div>
                </div>
                <div className="rounded-xl border border-border bg-[#071a2b] p-3">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground">Credit Limit</div>
                  <div className="mt-0.5 font-mono text-sm font-bold text-white">
                    {formatCurrency(selectedUserTx.customer?.credit_limit ?? 50000)}
                  </div>
                </div>
                <div className="rounded-xl border border-border bg-[#071a2b] p-3">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground">Transactions</div>
                  <div className="mt-0.5 font-mono text-sm font-bold text-white">
                    {selectedUserTx.transactions?.length ?? 0} Records
                  </div>
                </div>
                <div className="rounded-xl border border-border bg-[#071a2b] p-3">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground">Discrepancies</div>
                  <div className="mt-0.5 font-mono text-sm font-bold text-rose-400">
                    {selectedUserTx.summary?.discrepancies_count ?? selectedUserTx.transactions?.filter(t => t.difference !== 0).length ?? 0} ({formatCurrency(selectedUserTx.summary?.total_variance ?? 0)})
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Body: Transaction & Ledger Explorer */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* 1. Transactions List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    Assigned Transactions ({selectedUserTx.transactions?.length || 0})
                  </h4>
                  <span className="text-[11px] text-primary">Click any row to open and investigate</span>
                </div>
                <div className="overflow-hidden rounded-xl border border-border bg-[#071a2b]">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border/80 text-muted-foreground bg-[#0a2033]">
                        <th className="px-4 py-2.5">Date</th>
                        <th className="px-4 py-2.5">Transaction ID</th>
                        <th className="px-4 py-2.5">Customer / Invoice</th>
                        <th className="px-4 py-2.5 text-right">Actual Amount</th>
                        <th className="px-4 py-2.5 text-right">Difference</th>
                        <th className="px-4 py-2.5">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {selectedUserTx.transactions?.map((tx) => (
                        <tr
                          key={tx.id}
                          onClick={() => {
                            setSelectedUserTx(null);
                            navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } });
                          }}
                          className="cursor-pointer transition hover:bg-white/5"
                        >
                          <td className="px-4 py-2.5 font-mono text-muted-foreground">{tx.date}</td>
                          <td className="px-4 py-2.5 font-mono font-bold text-primary">{tx.id}</td>
                          <td className="px-4 py-2.5 text-white">
                            <div>{tx.customer}</div>
                            {tx.invoice_id && <div className="font-mono text-[10px] text-muted-foreground">{tx.invoice_id}</div>}
                          </td>
                          <td className="px-4 py-2.5 text-right font-medium text-emerald-400 font-mono">
                            {formatCurrency(tx.actual_amount)}
                          </td>
                          <td className="px-4 py-2.5 text-right font-mono">
                            <span className={tx.difference !== 0 ? "font-bold text-rose-400" : "text-muted-foreground"}>
                              {tx.difference !== 0 ? formatCurrency(tx.difference) : "$0.00"}
                            </span>
                          </td>
                          <td className="px-4 py-2.5">
                            <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold ${getStatusBadge(tx.status)}`}>
                              {tx.status.replaceAll("_", " ")}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 2. General Ledger Entries */}
              {selectedUserTx.ledger_entries && selectedUserTx.ledger_entries.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    General Ledger Journals ({selectedUserTx.ledger_entries.length} Postings)
                  </h4>
                  <div className="overflow-hidden rounded-xl border border-border bg-[#071a2b]">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-border/80 text-muted-foreground bg-[#0a2033]">
                          <th className="px-4 py-2">Posted Date</th>
                          <th className="px-4 py-2">Account Code</th>
                          <th className="px-4 py-2">Description / Ref</th>
                          <th className="px-4 py-2 text-right">Debit</th>
                          <th className="px-4 py-2 text-right">Credit</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/40">
                        {selectedUserTx.ledger_entries.map((le: any) => (
                          <tr key={le.id}>
                            <td className="px-4 py-2 font-mono text-muted-foreground">{le.posted_date}</td>
                            <td className="px-4 py-2 font-mono text-primary">{le.account_code}</td>
                            <td className="px-4 py-2 text-slate-200">
                              <div>{le.description}</div>
                              <div className="font-mono text-[10px] text-muted-foreground">Ref: {le.reference}</div>
                            </td>
                            <td className="px-4 py-2 text-right font-mono text-white">{le.debit > 0 ? formatCurrency(le.debit) : "—"}</td>
                            <td className="px-4 py-2 text-right font-mono text-white">{le.credit > 0 ? formatCurrency(le.credit) : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 3. Associated Documents */}
              {selectedUserTx.documents && selectedUserTx.documents.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    Associated Documents ({selectedUserTx.documents.length})
                  </h4>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {selectedUserTx.documents.map((doc: any) => (
                      <div
                        key={doc.id}
                        onClick={() => previewDocument(doc)}
                        className="cursor-pointer rounded-xl border border-border bg-[#071a2b] p-3 transition hover:border-primary/50"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white text-xs">{doc.filename}</span>
                          <span className="rounded bg-white/10 px-2 py-0.5 text-[9px] uppercase font-bold text-primary">
                            {doc.document_type}
                          </span>
                        </div>
                        <p className="mt-1 truncate font-mono text-[10px] text-muted-foreground">{doc.file_path}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Document Preview Modal */}
      {docPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-3xl rounded-2xl border border-border bg-[#0d2638] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-primary">DOCUMENT INTELLIGENCE</span>
                <h3 className="text-base font-bold text-white">{docPreview.title}</h3>
              </div>
              <button
                onClick={() => setDocPreview(null)}
                className="rounded-xl border border-border bg-[#071a2b] p-2 text-muted-foreground hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <pre className="mt-4 max-h-[500px] overflow-y-auto whitespace-pre-wrap rounded-xl border border-border bg-[#071a2b] p-4 text-xs font-mono text-slate-200 leading-relaxed">
              {docPreview.content}
            </pre>
          </div>
        </div>
      )}

    </div>
  );
}
