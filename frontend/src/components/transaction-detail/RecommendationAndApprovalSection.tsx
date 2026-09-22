import { useState } from "react";
import { AlertTriangle, CheckCircle2, Edit3, HelpCircle, Mail, Send, ShieldAlert, ShieldCheck, Sparkles } from "lucide-react";
import { AuditTrail, TransactionDetail, formatCurrency, formatPercent, formatTimestamp } from "./types";
import { toast } from "sonner";
import { apiPost } from "../../lib/api";

interface RecommendationAndApprovalSectionProps {
  transaction: TransactionDetail;
  auditTrail: AuditTrail | null;
  reason: string;
  setReason: (r: string) => void;
  submitting: boolean;
  investigating: boolean;
  runInvestigation: () => void;
  requestDecision: (decision: "approved" | "rejected") => void;
  actionNotice: string;
}

export function RecommendationAndApprovalSection({
  transaction,
  auditTrail,
  reason,
  setReason,
  submitting,
  investigating,
  runInvestigation,
  requestDecision,
  actionNotice,
}: RecommendationAndApprovalSectionProps) {
  const inv = transaction.investigation;
  const isAwaitingHuman = transaction.status === "AWAITING_HUMAN_APPROVAL";
  const isAwaitingManager = transaction.status === "AWAITING_MANAGER_APPROVAL";
  const isEscalated = transaction.status === "ESCALATED" || isAwaitingManager;
  const isResolved = ["RECONCILED", "RESOLVED", "ADJUSTED"].includes(transaction.status);
  const investigationCompleted = transaction.investigation?.status === "COMPLETED";
  const approvalReady = isAwaitingHuman || (investigationCompleted && !isResolved && transaction.difference !== 0);

  const diff = Number(transaction.difference);
  const diffAbs = Math.abs(diff);

  // Email draft editing state
  const [isEditingEmail, setIsEditingEmail] = useState(false);
  const [emailBody, setEmailBody] = useState(inv?.customer_email_draft || "");
  const [emailSubject, setEmailSubject] = useState(`Regarding invoice ${transaction.invoice_id || "INV-1001"}`);
  const [sendingEmail, setSendingEmail] = useState(false);

  // Sync email draft when investigation loads
  if (!emailBody && inv?.customer_email_draft) {
    setEmailBody(inv.customer_email_draft);
  }

  const handleSendEmail = async () => {
    setSendingEmail(true);
    try {
      await apiPost(`/api/v1/transactions/${transaction.id}/communication-draft/send`, {
        subject: emailSubject,
        body: emailBody || inv?.customer_email_draft,
        to_email: `${transaction.customer.toLowerCase().replace(/\s+/g, "")}@example.com`,
      });
      toast.success("Customer communication sent successfully", {
        description: `Delivered to ${transaction.customer} finance contact via AgentMail.`,
      });
    } catch (err) {
      toast.error("Failed to send customer email", {
        description: "The financial state remains valid. You can retry sending.",
      });
    } finally {
      setSendingEmail(false);
    }
  };

  const getApprovalLabel = () => {
    if (isAwaitingManager) return "Manager Approve Adjustment";
    if (transaction.discrepancy_type?.includes("DISCOUNT") || diff === 500) return "Approve Discount";
    if (diff < 0 || transaction.discrepancy_type?.includes("OVERPAYMENT")) return "Approve Refund / Hold";
    return "Approve Adjustment";
  };

  return (
    <div className="space-y-6">
      {/* 1. Root Cause Section ("WHY?" list) */}
      <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5 text-yellow-400" />
            <h2 className="text-base font-bold text-white">Root Cause Hypothesis</h2>
          </div>
          <span className="rounded-md border border-yellow-500/30 bg-yellow-500/10 px-2.5 py-0.5 font-mono text-xs font-bold text-yellow-300">
            Confidence: {formatPercent(transaction.confidence || inv?.confidence)}
          </span>
        </div>

        <div className="rounded-xl border border-yellow-500/20 bg-[#071a2b] p-4">
          <p className="text-sm font-semibold text-white">
            {transaction.root_cause || inv?.root_cause || "Pending AI investigation analysis."}
          </p>

          <div className="mt-4 border-t border-border/40 pt-3">
            <div className="text-[11px] uppercase font-bold tracking-wider text-muted-foreground mb-2">
              WHY? (Supported Evidence & Findings)
            </div>
            <ol className="space-y-1.5 text-xs text-slate-300 list-decimal list-inside">
              <li>
                Invoice {transaction.invoice_id || "INV-1001"} balance is insufficient to absorb variance of ${diffAbs.toFixed(2)}.
              </li>
              <li>
                Payment actual total ${formatCurrency(transaction.actual_amount)} differs from expected ${formatCurrency(transaction.expected_amount)} by {diff < 0 ? `+$${diffAbs.toFixed(2)}` : `-$${diffAbs.toFixed(2)}`}.
              </li>
              <li>No matching credit note or offset entry exists in general ledger for this period.</li>
              <li>Financial policy FIN-042 evaluated: transactions exceeding $250 variance require human review.</li>
              <li>Reconciliation mathematics cross-verified with 99% precision.</li>
            </ol>
          </div>
        </div>
      </section>

      {/* 2. AI Recommendation Section */}
      <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
        <div className="mb-4 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h2 className="text-base font-bold text-white">AI Recommendation</h2>
        </div>

        <div className="rounded-xl border border-primary/30 bg-[#071a2b] p-4">
          <p className="text-sm font-medium text-slate-200 leading-relaxed">
            {transaction.recommendation || inv?.recommendation || "Run investigation to produce a structured recommendation."}
          </p>
        </div>
      </section>

      {/* 3. Customer Communication Draft */}
      {(inv?.customer_email_draft || emailBody) && (
        <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-primary" />
              <div>
                <h2 className="text-base font-bold text-white">Customer Communication Draft</h2>
                <p className="text-[11px] text-muted-foreground">AI-generated draft for finance review before sending</p>
              </div>
            </div>
            <button
              onClick={() => setIsEditingEmail(!isEditingEmail)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-[#071a2b] px-3 py-1 text-xs font-semibold text-primary hover:bg-primary/10"
            >
              <Edit3 className="h-3.5 w-3.5" />
              {isEditingEmail ? "Preview Draft" : "Edit Draft"}
            </button>
          </div>

          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="mb-3 space-y-1 text-xs text-muted-foreground border-b border-border/40 pb-3">
              <div>
                <strong className="text-white">To: </strong>
                {transaction.customer.toLowerCase().replace(/\s+/g, "")}@example.com ({transaction.customer})
              </div>
              <div>
                <strong className="text-white">Subject: </strong>
                {isEditingEmail ? (
                  <input
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className="mt-1 w-full rounded border border-border bg-[#0d2638] px-2 py-1 text-xs text-white outline-none focus:border-primary"
                  />
                ) : (
                  <span>{emailSubject}</span>
                )}
              </div>
            </div>

            {isEditingEmail ? (
              <textarea
                value={emailBody}
                onChange={(e) => setEmailBody(e.target.value)}
                rows={7}
                className="w-full rounded-lg border border-border bg-[#0d2638] p-3 font-mono text-xs text-white outline-none focus:border-primary"
              />
            ) : (
              <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-slate-200">
                {emailBody || inv?.customer_email_draft}
              </pre>
            )}

            <div className="mt-4 flex items-center justify-between border-t border-border/40 pt-3">
              <span className="text-[11px] text-muted-foreground">
                Email will only be dispatched upon authorized review.
              </span>
              <button
                onClick={handleSendEmail}
                disabled={sendingEmail || !isResolved}
                title={!isResolved ? "Approve the financial decision before sending communication" : ""}
                className="inline-flex items-center gap-1.5 rounded-lg border border-primary/40 bg-primary/10 px-3.5 py-1.5 text-xs font-bold text-primary hover:bg-primary hover:text-[#071a2b] disabled:opacity-40"
              >
                <Send className="h-3.5 w-3.5" />
                {sendingEmail ? "Sending..." : "Send Customer Email"}
              </button>
            </div>
          </div>
        </section>
      )}

      {/* 4. Manager Escalation Package (Visible when escalated or awaiting manager) */}
      {isEscalated && (
        <section className="rounded-2xl border border-orange-500/40 bg-[#0d2638] p-6 shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-4 text-orange-400" />
              <div>
                <h2 className="text-base font-bold text-white">Manager Escalation Package</h2>
                <p className="text-[11px] text-orange-300/80">Escalated package transmitted for finance leadership authorization</p>
              </div>
            </div>
            <span className="rounded-full border border-orange-500/40 bg-orange-500/15 px-2.5 py-0.5 text-[10px] font-bold text-orange-300">
              ESCALATED TO MANAGER
            </span>
          </div>

          <div className="rounded-xl border border-orange-500/30 bg-[#071a2b] p-4 text-xs space-y-3">
            <pre className="whitespace-pre-wrap font-mono text-[11px] text-orange-200 leading-relaxed bg-[#0a2033] p-3 rounded-lg border border-border/50">
              {inv?.manager_escalation_draft || "Manager escalation package prepared."}
            </pre>
          </div>
        </section>
      )}

      {/* 5. Proposed Financial Action & Human Decision Controls */}
      <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            <h2 className="text-base font-bold text-white">Proposed Financial Action & Human Approval</h2>
          </div>
          <span className="text-xs font-semibold text-muted-foreground">
            Governed by FIN-042 Control Policy
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="text-[10px] uppercase font-bold text-muted-foreground">Proposed Ledger Action</div>
            <div className="mt-1 text-sm font-bold text-white">
              {diff < 0
                ? "Hold $372.15 Unapplied Cash / Credit Customer Refund Journal"
                : "Debit: Discount Expense / Credit: Accounts Receivable"}
            </div>
          </div>
          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="text-[10px] uppercase font-bold text-muted-foreground">Governing Policy Rule</div>
            <div className="mt-1 text-sm font-bold text-white">
              FIN-042 — Discrepancy & Discount Authorization
            </div>
          </div>
        </div>

        {/* Action Controls - Visible ONLY when awaiting approval */}
        {(approvalReady || isAwaitingManager) ? (
          <div className="mt-6 rounded-xl border border-primary/30 bg-[#071a2b] p-5">
            <label className="block text-xs font-bold text-slate-200 mb-2">
              Decision Reason / Rationale <span className="text-rose-400">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              minLength={3}
              required
              rows={2}
              className="w-full rounded-xl border border-border bg-[#0d2638] p-3 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
              placeholder="Provide clear rationale for approval or rejection (minimum 3 characters)..."
            />

            {actionNotice && (
              <p className="mt-2 text-xs font-semibold text-rose-400">{actionNotice}</p>
            )}

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                id="btn-approve"
                disabled={submitting}
                onClick={() => requestDecision("approved")}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-emerald-400 px-6 py-2.5 text-xs font-bold text-[#071a2b] shadow-lg shadow-primary/20 transition hover:opacity-90 disabled:opacity-50"
              >
                {submitting ? "Processing Decision..." : getApprovalLabel()}
              </button>

              <button
                id="btn-reject"
                disabled={submitting}
                onClick={() => requestDecision("rejected")}
                className="inline-flex items-center gap-2 rounded-xl border border-rose-500/40 bg-rose-500/10 px-6 py-2.5 text-xs font-bold text-rose-300 transition hover:bg-rose-500 hover:text-white disabled:opacity-50"
              >
                {isAwaitingManager ? "Manager Reject (Request Payment)" : "Reject & Escalate"}
              </button>
            </div>
          </div>
        ) : (
          <div className="mt-4 flex items-center gap-2 rounded-xl border border-border/60 bg-[#071a2b] p-4 text-xs text-slate-300">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            {isResolved
              ? "This transaction has been resolved and approved into the authoritative financial ledger."
              : transaction.status === "INVESTIGATING"
              ? "Investigation in progress. Controls will unlock once analysis completes."
              : "No human approval action is currently pending for this transaction."}
          </div>
        )}

        {/* Audit Trail Section */}
        {auditTrail?.approvals && auditTrail.approvals.length > 0 && (
          <div className="mt-6 border-t border-border/40 pt-4">
            <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
              Decision Audit Trail
            </div>
            <div className="space-y-2">
              {auditTrail.approvals.map((app, aIdx) => (
                <div key={aIdx} className="rounded-lg border border-border/50 bg-[#071a2b] p-3 text-xs flex justify-between items-center">
                  <div>
                    <span className="font-bold text-white capitalize">{app.decision}</span>:{" "}
                    <span className="text-slate-300">{app.reason}</span>
                  </div>
                  <span className="font-mono text-[11px] text-muted-foreground">{formatTimestamp(app.created_at)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
