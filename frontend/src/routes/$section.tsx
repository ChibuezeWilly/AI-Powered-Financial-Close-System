import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  ArrowLeft,
  Menu,
  RefreshCw,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { apiGet, apiPost } from "../lib/api";
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
  const [selectedUserTx, setSelectedUserTx] = useState<{ user: any; transactions: TransactionRecord[] } | null>(null);
  const [docPreview, setDocPreview] = useState<{ title: string; content: string } | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const months = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09"];

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
  }, [section, selectedPeriod, searchQuery, user]);

  useEffect(() => {
    if (user && user.role !== "REGULAR_USER") {
      loadData();
    }
  }, [user, loadData]);

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
              runReconcile={runReconcile}
              actionLoading={actionLoading}
            />
          )}

          {section === "discrepancies" && (
            <DiscrepanciesSection transactions={transactions} />
          )}

          {section === "investigations" && (
            <InvestigationsSection investigations={investigations} />
          )}

          {section === "approvals" && (
            <ApprovalsSection transactions={transactions} />
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
