import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { TransactionDetail, formatCurrency } from "./types";

interface ConfirmDecisionModalProps {
  transaction: TransactionDetail;
  confirmDialog: { decision: "approved" | "rejected"; open: boolean };
  setConfirmDialog: (dialog: { decision: "approved" | "rejected"; open: boolean }) => void;
  executeDecision: () => void;
  reason: string;
}

export function ConfirmDecisionModal({
  transaction,
  confirmDialog,
  setConfirmDialog,
  executeDecision,
  reason,
}: ConfirmDecisionModalProps) {
  if (!confirmDialog.open) return null;

  return (
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
  );
}
