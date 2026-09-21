import { Link, createFileRoute } from "@tanstack/react-router";
import {
  ArrowLeft,
  CheckCircle2,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { apiGet, apiPost } from "../../lib/api";
import { UnauthorizedView } from "../../components/common/UnauthorizedView";
import {
  AuditTrail,
  TransactionDetail,
  getStatusColor,
} from "../../components/transaction-detail/types";
import { ConfirmDecisionModal } from "../../components/transaction-detail/ConfirmDecisionModal";
import { TransactionHeader } from "../../components/transaction-detail/TransactionHeader";
import { TransactionSummarySection } from "../../components/transaction-detail/TransactionSummarySection";
import { FinancialRelationshipSection } from "../../components/transaction-detail/FinancialRelationshipSection";
import { AgentFindingsSection } from "../../components/transaction-detail/AgentFindingsSection";
import { EvidenceSection } from "../../components/transaction-detail/EvidenceSection";
import { InvestigationTimelineSection } from "../../components/transaction-detail/InvestigationTimelineSection";
import { RecommendationAndApprovalSection } from "../../components/transaction-detail/RecommendationAndApprovalSection";

export const Route = createFileRoute("/transactions/$transactionId")({
  component: TransactionDetailRoute,
});

const AUTO_REFRESH_MS = 15_000;

type UserAccount = { id: number; full_name: string; email: string; role: string };

function TransactionDetailRoute() {
  const { transactionId } = Route.useParams();
  const [user, setUser] = useState<UserAccount | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  const [transaction, setTransaction] = useState<TransactionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [reason, setReason] = useState("");
  const [actionNotice, setActionNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [investigating, setInvestigating] = useState(false);
  const [sourceDocument, setSourceDocument] = useState<{ name: string; content: string } | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [auditTrail, setAuditTrail] = useState<AuditTrail | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{ decision: "approved" | "rejected"; open: boolean }>({ decision: "approved", open: false });
  const refreshRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auth check
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

  const loadTransaction = useCallback(async () => {
    if (!localStorage.getItem("financial-close-token")) return null;
    const [detail, audit] = await Promise.all([
      apiGet<TransactionDetail>(`/api/v1/transactions/${transactionId}`),
      apiGet<AuditTrail>(`/api/v1/transactions/${transactionId}/audit`),
    ]);
    setTransaction(detail);
    setAuditTrail(audit);
    return detail;
  }, [transactionId]);

  // Initial load
  useEffect(() => {
    if (!user || user.role === "REGULAR_USER") return;
    loadTransaction()
      .then(() => setLoading(false))
      .catch(() => setLoading(false));
    return undefined;
  }, [user, loadTransaction]);

  // Auto-refresh while investigation is in progress
  useEffect(() => {
    const investigationActive = transaction?.investigation?.status &&
      ["PENDING", "RUNNING"].includes(transaction.investigation.status);
    const needsRefresh = investigationActive ||
      ["INVESTIGATING", "ADJUSTMENT_PENDING"].includes(transaction?.status ?? "");

    if (!needsRefresh) {
      if (refreshRef.current) clearInterval(refreshRef.current);
      return;
    }

    refreshRef.current = setInterval(() => {
      loadTransaction().catch(() => { /* silent background refresh */ });
    }, AUTO_REFRESH_MS);

    return () => {
      if (refreshRef.current) clearInterval(refreshRef.current);
    };
  }, [transaction?.investigation?.status, transaction?.status, loadTransaction]);

  function requestDecision(decision: "approved" | "rejected") {
    if (reason.trim().length < 3) {
      setActionNotice("Please add a decision reason of at least three characters.");
      return;
    }
    setConfirmDialog({ decision, open: true });
  }

  async function executeDecision() {
    const decision = confirmDialog.decision;
    setConfirmDialog({ decision, open: false });
    if (!localStorage.getItem("financial-close-token") || !transaction) return;

    setSubmitting(true);
    setActionNotice("");
    try {
      const endpoint = transaction.status === "AWAITING_MANAGER_APPROVAL" ? "manager-decision" : "decision";
      const result = await apiPost<{ status: string; message?: string; journal_entry?: string }>(
        `/api/v1/transactions/${transaction.id}/${endpoint}`,
        { decision, reason: reason.trim() },
        endpoint === "decision" ? { "Idempotency-Key": `${transaction.id}:${decision}:${Date.now()}` } : undefined,
      );
      await loadTransaction();

      if (decision === "approved") {
        toast.success("Adjustment approved", {
          description: result.journal_entry
            ? `Journal ${result.journal_entry} posted. Transaction resolved.`
            : `Transaction is now ${String(result.status).replaceAll("_", " ")}.`,
        });
      } else {
        toast.warning("Transaction escalated", {
          description: "Escalated to Finance Manager for authorization.",
        });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "The decision could not be recorded.";
      toast.error("Decision failed", { description: message });
      setActionNotice(message);
    } finally {
      setSubmitting(false);
    }
  }

  async function openEvidence(sourceId: string) {
    setEvidenceLoading(true);
    try {
      const payload = await apiGet<{ document: string; content: string }>(`/api/v1/evidence/${sourceId}`);
      setSourceDocument({ name: payload.document, content: payload.content });
    } catch (error) {
      toast.error("Document unavailable", {
        description: error instanceof Error ? error.message : "The source document could not be loaded.",
      });
    } finally {
      setEvidenceLoading(false);
    }
  }

  async function runInvestigation() {
    if (!transaction) return;
    setInvestigating(true);
    setActionNotice("");
    try {
      await apiPost(`/api/v1/transactions/${transaction.id}/investigate`);
      await loadTransaction();
      toast.success("AI investigation completed", {
        description: "Evidence and recommendations are ready for human review.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "The AI investigation could not be completed.";
      toast.error("Investigation failed", { description: message });
      setActionNotice(message);
    } finally {
      setInvestigating(false);
    }
  }

  const handleBack = () => {
    if (window.history.length > 1) {
      window.history.back();
    }
  };

  if (isCheckingAuth) {
    return (
      <main className="min-h-screen bg-background p-8 text-foreground">
        <div className="mx-auto max-w-6xl rounded-xl border border-border bg-[#0d2638] p-8">
          <div className="flex items-center gap-3 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            Authenticating…
          </div>
        </div>
      </main>
    );
  }

  // Regular user trying to view transaction investigation / approval admin page -> UNAUTHORIZED
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
            <ArrowLeft className="h-3.5 w-3.5" /> Return to Customer Portal
          </Link>
        </header>
        <UnauthorizedView userRole={user?.role || "GUEST"} />
      </div>
    );
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-background p-8 text-foreground">
        <div className="mx-auto max-w-6xl rounded-xl border border-border bg-[#0d2638] p-8">
          <div className="flex items-center gap-3 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            Loading transaction investigation workspace…
          </div>
        </div>
      </main>
    );
  }

  if (!transaction) {
    return (
      <main className="min-h-screen bg-background p-8 text-foreground">
        <div className="mx-auto max-w-5xl rounded-xl border border-border bg-[#0d2638] p-8">
          <p className="text-lg font-semibold">Transaction not found</p>
          <Link to="/" className="mt-4 inline-flex items-center gap-2 text-primary">
            <ArrowLeft className="h-4 w-4" /> Return to close board
          </Link>
        </div>
      </main>
    );
  }

  const managerDecision = transaction.status === "AWAITING_MANAGER_APPROVAL";
  const isResolved = ["RECONCILED", "RESOLVED"].includes(transaction.status);

  return (
    <main className="min-h-screen overflow-x-hidden bg-background text-foreground pb-12">
      <ConfirmDecisionModal
        transaction={transaction}
        confirmDialog={confirmDialog}
        setConfirmDialog={setConfirmDialog}
        executeDecision={executeDecision}
        reason={reason}
      />

      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8 space-y-6">
        <div className="flex items-center justify-between">
          <button
            onClick={handleBack}
            className="inline-flex items-center gap-2 text-xs font-semibold text-primary hover:text-emerald-300 transition"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Financial Close
          </button>
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${getStatusColor(transaction.status)}`}>
            {transaction.status.replaceAll("_", " ")}
          </span>
        </div>

        {/* Escalation banner */}
        {managerDecision && (
          <div className="flex items-start gap-3 rounded-2xl border border-yellow-500/40 bg-yellow-500/10 p-4">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-yellow-400" />
            <div>
              <p className="font-bold text-yellow-200">Manager Approval Required</p>
              <p className="mt-1 text-xs text-yellow-200/80">
                This transaction was escalated after an analyst rejection. A Finance Manager must review the
                evidence package and approve or reject the proposed adjustment before financial period closure.
              </p>
            </div>
          </div>
        )}

        {/* Resolved success banner */}
        {isResolved && (
          <div className="flex items-start gap-3 rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-4">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
            <div>
              <p className="font-bold text-emerald-200">Transaction Reconciled & Resolved</p>
              <p className="mt-1 text-xs text-emerald-200/80">
                All discrepancies have been reconciled. The journal entry has been posted to the general ledger and verified.
              </p>
            </div>
          </div>
        )}

        {/* 1. Transaction Header */}
        <TransactionHeader
          transaction={transaction}
          onInvestigate={runInvestigation}
          investigating={investigating}
          onBack={handleBack}
        />

        {/* 2. Discrepancy Overview */}
        <TransactionSummarySection transaction={transaction} />

        {/* 3. Financial Relationship View (Neo4j / PostgreSQL) */}
        <FinancialRelationshipSection transaction={transaction} />

        {/* 4. Evidence View & Pinecone Precedents */}
        <EvidenceSection
          transaction={transaction}
          evidenceLoading={evidenceLoading}
          openEvidence={openEvidence}
        />

        {/* 5. Specialized Agent Findings */}
        <AgentFindingsSection findings={transaction.investigation?.agent_findings} />

        {/* 6. Investigation Execution Timeline */}
        <InvestigationTimelineSection
          transaction={transaction}
          evidenceLoading={evidenceLoading}
          sourceDocument={sourceDocument}
          setSourceDocument={setSourceDocument}
        />

        {/* 7. Root Cause WHY, AI Recommendation, Customer Communication Draft, Proposed Action & Approval Controls */}
        <RecommendationAndApprovalSection
          transaction={transaction}
          auditTrail={auditTrail}
          reason={reason}
          setReason={setReason}
          submitting={submitting}
          investigating={investigating}
          runInvestigation={runInvestigation}
          requestDecision={requestDecision}
          actionNotice={actionNotice}
        />
      </div>
    </main>
  );
}
