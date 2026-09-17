import { Link, createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  FileText,
  Link2,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { apiGet, apiPost } from "../../lib/api";

export const Route = createFileRoute("/transactions/$transactionId")({
  component: TransactionDetailRoute,
});

type TransactionDetail = {
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
  investigation?: {
    id: string;
    status: string;
    evidence: Array<{
      source_type: string;
      source_id: string;
      title: string;
      page: number | null;
      excerpt: string;
      relevance: number;
      confidence: number;
      retrieval_method: string;
    }>;
    timeline: string[];
  } | null;
  journal_entry?: { id: string; amount: number; status: string; debit: string; credit: string } | null;
  evidence_graph?: string[];
};

type AuditTrail = {
  approvals: Array<{ decision: string; reason: string; decided_by: number; created_at: string }>;
  events: Array<{ action: string; actor_id: number | null; created_at: string }>;
};

const AUTO_REFRESH_MS = 15_000;

const formatCurrency = (value: number, currency = "USD") =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);

const formatTimestamp = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
};

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    RECONCILED: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
    RESOLVED: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
    AWAITING_HUMAN_APPROVAL: "border-violet-500/40 bg-violet-500/10 text-violet-300",
    AWAITING_MANAGER_APPROVAL: "border-yellow-500/40 bg-yellow-500/10 text-yellow-300",
    APPROVED: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
    ADJUSTED: "border-teal-500/40 bg-teal-500/10 text-teal-300",
    ADJUSTMENT_PENDING: "border-sky-500/40 bg-sky-500/10 text-sky-300",
    REJECTED: "border-red-500/40 bg-red-500/10 text-red-300",
    REJECTED_MANAGER: "border-rose-500/40 bg-rose-500/10 text-rose-300",
    ESCALATED: "border-orange-500/40 bg-orange-500/10 text-orange-300",
    INVESTIGATING: "border-orange-500/40 bg-orange-500/10 text-orange-300",
    PAYMENT_REQUESTED: "border-amber-500/40 bg-amber-500/10 text-amber-300",
    PAYMENT_PENDING: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  };
  return colors[status] ?? "border-primary/30 bg-primary/10 text-primary";
};

function TransactionDetailRoute() {
  const { transactionId } = Route.useParams();
  const [transaction, setTransaction] = useState<TransactionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [reason, setReason] = useState("");
  const [actionNotice, setActionNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sourceDocument, setSourceDocument] = useState<{ name: string; content: string } | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [auditTrail, setAuditTrail] = useState<AuditTrail | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{ decision: "approved" | "rejected"; open: boolean }>({ decision: "approved", open: false });
  const refreshRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadTransaction = useCallback(async () => {
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
    if (!localStorage.getItem("financial-close-token")) return;
    loadTransaction()
      .then(() => setLoading(false))
      .catch(() => setLoading(false));
    return undefined;
  }, [loadTransaction]);

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
        toast.warning("Decision rejected — escalated", {
          description: result.message || "Escalated to Finance Manager for review.",
        });
      }

      setActionNotice(result.message || `Decision recorded. Transaction is now ${String(result.status).replaceAll("_", " ")}.`);
      setReason("");
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

  if (loading) {
    return (
      <main className="min-h-screen bg-background p-8 text-foreground">
        <div className="mx-auto max-w-6xl rounded-xl border border-border bg-[#0d2638] p-8">
          <div className="flex items-center gap-3 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            Loading transaction investigation…
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

  const evidence = transaction.investigation?.evidence ?? [];
  const timeline = transaction.investigation?.timeline ?? ["Investigation scheduled", "Evidence pending"];
  const graph = transaction.evidence_graph ?? [];
  const requiresDecision = ["AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL"].includes(transaction.status);
  const managerDecision = transaction.status === "AWAITING_MANAGER_APPROVAL";
  const isResolved = ["RECONCILED", "RESOLVED"].includes(transaction.status);
  const journalVerified = transaction.journal_entry?.status === "POSTED";

  return (
    <main className="min-h-screen overflow-x-hidden bg-background text-foreground">
      {/* ── Confirmation dialog ─────────────────────────────────────── */}
      {confirmDialog.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-md rounded-xl border border-border bg-[#0d2638] p-6 shadow-2xl">
            <div className="mb-4 flex items-center gap-3">
              {confirmDialog.decision === "approved" ? (
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-amber-400" />
              )}
              <h3 className="text-lg font-semibold text-foreground">
                {confirmDialog.decision === "approved" ? "Confirm approval" : "Confirm rejection & escalation"}
              </h3>
            </div>

            <div className="mb-4 space-y-2 rounded-lg border border-border bg-[#071a2b] p-4 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Transaction</span>
                <span className="font-medium text-foreground">{transaction.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Amount</span>
                <span className="font-medium text-foreground">{formatCurrency(Math.abs(transaction.difference), transaction.currency)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Action</span>
                <span className="font-medium text-foreground">
                  {confirmDialog.decision === "approved"
                    ? "Post journal adjustment"
                    : "Escalate to Finance Manager"}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Reason: </span>
                <span className="text-foreground">{reason}</span>
              </div>
            </div>

            {confirmDialog.decision === "rejected" && (
              <p className="mb-4 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
                This transaction will be escalated to a Finance Manager for review. The decision cannot be undone.
              </p>
            )}

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}
                className="rounded-md border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
              <button
                onClick={executeDecision}
                className={`rounded-md px-4 py-2 text-sm font-semibold ${
                  confirmDialog.decision === "approved"
                    ? "bg-primary text-[#071a2b] hover:bg-[#4ADE80]"
                    : "bg-amber-500 text-[#071a2b] hover:bg-amber-400"
                }`}
              >
                {confirmDialog.decision === "approved" ? "Confirm approval" : "Confirm escalation"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
        <div className="mb-6 flex items-center justify-between">
          <Link to="/" className="inline-flex items-center gap-2 text-primary">
            <ArrowLeft className="h-4 w-4" /> Back to financial close
          </Link>
          <span className={`rounded-full border px-3 py-1 text-xs font-medium ${getStatusColor(transaction.status)}`}>
            {transaction.status.replaceAll("_", " ")}
          </span>
        </div>

        {/* ── Escalation banner ────────────────────────────────────── */}
        {managerDecision && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-yellow-500/40 bg-yellow-500/10 p-4">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-yellow-400" />
            <div>
              <p className="font-medium text-yellow-200">Manager approval required</p>
              <p className="mt-1 text-sm text-yellow-200/80">
                This transaction was escalated after an analyst rejection. A Finance Manager or Admin must review and
                approve or reject the proposed resolution before the close period can proceed.
              </p>
            </div>
          </div>
        )}

        {/* ── Resolved success banner ─────────────────────────────── */}
        {isResolved && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
            <div>
              <p className="font-medium text-emerald-200">Transaction resolved</p>
              <p className="mt-1 text-sm text-emerald-200/80">
                All discrepancies have been reconciled. The journal entry has been posted and verified.
              </p>
            </div>
          </div>
        )}

        <header className="mb-8 rounded-xl border border-border bg-[#0d2638] p-6">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-bold tracking-[0.18em] text-primary">TRANSACTION</p>
              <h1 className="mt-2 text-3xl font-semibold">{transaction.id}</h1>
            </div>
            <div className="rounded-lg border border-border bg-[#071a2b] px-4 py-3 text-right">
              <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Investigation</div>
              <div className="mt-1 font-medium text-foreground">
                {transaction.investigation?.status ?? "PENDING"}
                {["PENDING", "RUNNING"].includes(transaction.investigation?.status ?? "") && (
                  <Loader2 className="ml-2 inline h-3.5 w-3.5 animate-spin text-primary" />
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <InfoCard label="Customer" value={transaction.customer} />
            <InfoCard label="Invoice" value={transaction.invoice_id} />
            <InfoCard label="Payment" value={transaction.payment_id ?? "Awaiting match"} />
            <InfoCard label="Month" value={transaction.period.replace("-", " ")} />
          </div>
        </header>

        <div className="mb-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-xl border border-border bg-[#0d2638] p-6">
            <p className="text-xs font-bold tracking-[0.18em] text-primary">TRANSACTION SUMMARY</p>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <StatRow label="Expected" value={formatCurrency(transaction.expected_amount, transaction.currency)} />
              <StatRow label="Actual" value={formatCurrency(transaction.actual_amount, transaction.currency)} />
              <StatRow label="Difference" value={formatCurrency(transaction.difference, transaction.currency)} emphasis />
              <StatRow label="Severity" value={transaction.severity} />
              <StatRow label="Status" value={transaction.status.replaceAll("_", " ")} />
              <StatRow label="Confidence" value={transaction.confidence ? `${(transaction.confidence * 100).toFixed(0)}%` : "n/a"} />
            </div>
            <div className="mt-6 rounded-lg border border-border bg-[#071a2b] p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Root cause</p>
              <p className="mt-3 text-base text-foreground">{transaction.root_cause ?? "No root cause determined yet."}</p>
            </div>
          </section>

          <section className="rounded-xl border border-border bg-[#0d2638] p-6">
            <p className="text-xs font-bold tracking-[0.18em] text-primary">FINANCIAL RELATIONSHIPS</p>
            <div className="mt-5 space-y-3">
              {Array.from({ length: Math.ceil(graph.length / 2) }, (_, index) => [graph[index * 2], graph[index * 2 + 1]]).map(([label, value], index) => (
                <div key={label} className="flex items-center gap-3">
                  <div className="flex flex-col items-center">
                    {index > 0 && <div className="h-5 w-px bg-border" />}
                    <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full border border-primary/30 bg-primary/10 text-[10px] text-primary">
                      {index + 1}
                    </div>
                    {index < 5 && <div className="my-1 h-5 w-px bg-border" />}
                  </div>
                  <div className="rounded-md border border-border bg-[#071a2b] px-3 py-2 text-sm">
                    <span className="text-muted-foreground">{label}</span>
                    <div className="font-medium text-foreground">{value}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <section className="mb-8 rounded-xl border border-border bg-[#0d2638] p-6">
          <div className="mb-5 flex items-center gap-3">
            <CircleAlert className="h-5 w-5 text-primary" />
            <p className="text-xs font-bold tracking-[0.18em] text-primary">AI INVESTIGATION</p>
          </div>
          <div className="space-y-3">
            {timeline.map((step) => (
              <div key={step} className="flex gap-3">
                <div className="flex w-20 flex-col items-center text-xs text-muted-foreground">
                  <span>{step.split(" ")[0]}</span>
                </div>
                <div className="mt-1 h-4 w-4 rounded-full border border-primary bg-primary/20" />
                <div className="rounded-md border border-border bg-[#071a2b] px-3 py-2 text-sm text-foreground">
                  {step.replace(/^\d{2}:\d{2}\s*/, "")}
                </div>
              </div>
            ))}
          </div>
          {evidenceLoading && (
            <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin text-primary" /> Loading source document…
            </div>
          )}
          {sourceDocument && (
            <div className="mt-4 rounded-lg border border-primary/30 bg-[#071a2b] p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-foreground">Source viewer · {sourceDocument.name}</p>
                <button type="button" onClick={() => setSourceDocument(null)} className="text-xs text-primary hover:text-emerald-300">Close</button>
              </div>
              <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap font-sans text-sm leading-6 text-muted-foreground">{sourceDocument.content}</pre>
            </div>
          )}
        </section>

        <section className="mb-8 rounded-xl border border-border bg-[#0d2638] p-6">
          <p className="text-xs font-bold tracking-[0.18em] text-primary">ROOT CAUSE</p>
          <div className="mt-4 rounded-lg border border-border bg-[#071a2b] p-4">
            <p className="text-base text-foreground">
              &ldquo;{transaction.root_cause ?? "The discrepancy cannot be confidently attributed without additional evidence."}&rdquo;
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
              <span>Confidence: {transaction.confidence ? `${(transaction.confidence * 100).toFixed(0)}%` : "n/a"}</span>
              <span className="rounded-full border border-border bg-[#0d2638] px-2 py-0.5 text-[10px]">Detected fact</span>
              <span className="rounded-full border border-border bg-[#0d2638] px-2 py-0.5 text-[10px]">AI hypothesis</span>
              <span className="rounded-full border border-border bg-[#0d2638] px-2 py-0.5 text-[10px]">Human decision</span>
            </div>
          </div>
        </section>

        <section className="mb-8 rounded-xl border border-border bg-[#0d2638] p-6">
          <div className="mb-4 flex items-center gap-3">
            <FileText className="h-5 w-5 text-primary" />
            <p className="text-xs font-bold tracking-[0.18em] text-primary">EVIDENCE</p>
          </div>
          <div className="space-y-3">
            {evidence.length === 0 && (
              <p className="text-sm text-muted-foreground">No evidence has been collected yet.</p>
            )}
            {evidence.map((item, index) => (
              <div key={`${item.source_id}-${index}`} className="rounded-lg border border-border bg-[#071a2b] p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-foreground">{item.source_type} · {item.source_id}</p>
                    <p className="text-sm text-muted-foreground">{item.title}</p>
                  </div>
                  <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[11px] text-emerald-300">
                    {item.retrieval_method}
                  </span>
                </div>
                <p className="mt-3 text-sm text-foreground">&ldquo;{item.excerpt}&rdquo;</p>
                <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                  <span>Page: {item.page ?? "n/a"}</span>
                  <span>Relevance: {(item.relevance * 100).toFixed(0)}%</span>
                  <span>Confidence: {(item.confidence * 100).toFixed(0)}%</span>
                  {item.source_id.startsWith("INV-") && (
                    <button
                      type="button"
                      disabled={evidenceLoading}
                      className="font-medium text-primary hover:text-emerald-300 disabled:opacity-50"
                      onClick={() => openEvidence(item.source_id)}
                    >
                      {evidenceLoading ? "Loading…" : "Open source document"}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-8 rounded-xl border border-border bg-[#0d2638] p-6">
          <div className="mb-4 flex items-center gap-3">
            <Link2 className="h-5 w-5 text-primary" />
            <p className="text-xs font-bold tracking-[0.18em] text-primary">RECOMMENDATION</p>
          </div>
          <div className="rounded-lg border border-border bg-[#071a2b] p-4">
            <p className="text-base text-foreground">{transaction.recommendation ?? "A documented action has not yet been generated."}</p>
            {requiresDecision ? (
              <div className="mt-4">
                <label className="block text-sm text-muted-foreground">
                  Decision reason
                  <textarea value={reason} onChange={(event) => setReason(event.target.value)} minLength={3} required rows={2}
                    className="mt-2 w-full rounded-md border border-border bg-[#0d2638] px-3 py-2 text-foreground outline-none focus:border-primary"
                    placeholder="Document the approval or rejection rationale." />
                </label>
                <div className="mt-3 flex flex-wrap gap-3">
                  <button
                    id="btn-approve"
                    disabled={submitting}
                    onClick={() => requestDecision("approved")}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-[#071a2b] enabled:hover:bg-[#4ADE80] disabled:opacity-50"
                  >
                    {submitting ? "Recording…" : managerDecision ? "Manager approve" : "Approve adjustment"}
                  </button>
                  <button
                    id="btn-reject"
                    disabled={submitting}
                    onClick={() => requestDecision("rejected")}
                    className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-foreground enabled:hover:bg-white/5 disabled:opacity-50"
                  >
                    {managerDecision ? "Manager reject" : "Reject & escalate"}
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-4 inline-flex items-center gap-2 text-sm text-emerald-300"><CheckCircle2 className="h-4 w-4" /> No human decision is currently required.</div>
            )}
            {actionNotice && <p className="mt-3 text-sm text-muted-foreground" role="status">{actionNotice}</p>}
          </div>
        </section>

        <section className="rounded-xl border border-border bg-[#0d2638] p-6">
          <div className="mb-4 flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-primary" />
            <p className="text-xs font-bold tracking-[0.18em] text-primary">APPROVAL FLOW</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-[#071a2b] p-4">
              <div className="text-sm text-muted-foreground">Proposed action</div>
              <div className="mt-2 text-lg font-semibold text-foreground">
                {transaction.journal_entry
                  ? `${transaction.journal_entry.debit} / ${transaction.journal_entry.credit}`
                  : "Debit Discount Expense / Credit A/R"}
              </div>
            </div>
            <div className="rounded-lg border border-border bg-[#071a2b] p-4">
              <div className="text-sm text-muted-foreground">Policy</div>
              <div className="mt-2 text-lg font-semibold text-foreground">FIN-042</div>
            </div>
          </div>

          {/* Journal entry with verification indicator */}
          <div className="mt-4 rounded-lg border border-border bg-[#071a2b] p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Posted journal</div>
              {journalVerified && (
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                  <CheckCircle2 className="h-3 w-3" /> Verified
                </span>
              )}
            </div>
            <div className="mt-2 text-sm text-foreground">
              {transaction.journal_entry
                ? `${transaction.journal_entry.id} · ${transaction.journal_entry.debit} / ${transaction.journal_entry.credit} · ${formatCurrency(transaction.journal_entry.amount, transaction.currency)}`
                : "No journal has been posted."}
            </div>
          </div>

          {/* Enriched audit trail with timestamps */}
          <div className="mt-4 rounded-lg border border-border bg-[#071a2b] p-4">
            <div className="text-sm text-muted-foreground">Decision audit trail</div>
            <div className="mt-3 space-y-3">
              {auditTrail?.approvals.length ? auditTrail.approvals.map((approval, index) => (
                <div key={`${approval.created_at}-${index}`} className="flex items-start gap-3">
                  <div className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
                    approval.decision.includes("approved") ? "bg-emerald-400" : "bg-amber-400"
                  }`} />
                  <div className="text-sm">
                    <p className="text-foreground">
                      <span className="font-medium">{approval.decision.replaceAll("_", " ")}</span>
                      {" — "}{approval.reason}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      User #{approval.decided_by} · {formatTimestamp(approval.created_at)}
                    </p>
                  </div>
                </div>
              )) : <p className="text-sm text-muted-foreground">No decisions recorded yet.</p>}
            </div>

            {auditTrail?.events && auditTrail.events.length > 0 && (
              <div className="mt-4 border-t border-border pt-3">
                <p className="mb-2 text-xs font-bold tracking-[0.14em] text-muted-foreground">SYSTEM EVENTS</p>
                <div className="space-y-2">
                  {auditTrail.events.map((event, index) => (
                    <div key={`${event.created_at}-${index}`} className="flex items-center gap-2 text-xs text-muted-foreground">
                      <div className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
                      <span className="font-medium text-foreground/80">{event.action.replaceAll("_", " ")}</span>
                      <span>·</span>
                      <span>{formatTimestamp(event.created_at)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-[#071a2b] p-4">
      <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</div>
      <div className="mt-2 font-medium text-foreground">{value}</div>
    </div>
  );
}

function StatRow({ label, value, emphasis = false }: { label: string; value: string; emphasis?: boolean }) {
  return (
    <div className="rounded-lg border border-border bg-[#071a2b] p-4">
      <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</div>
      <div className={`mt-2 font-semibold ${emphasis ? "text-red-300" : "text-foreground"}`}>{value}</div>
    </div>
  );
}
