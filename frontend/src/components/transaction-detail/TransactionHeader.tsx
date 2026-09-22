import { ArrowLeft, Loader2, Sparkles } from "lucide-react";
import { TransactionDetail, formatCurrency, getStatusColor } from "./types";

interface TransactionHeaderProps {
  transaction: TransactionDetail;
  onInvestigate?: () => void;
  investigating?: boolean;
  onBack?: () => void;
}

export function TransactionHeader({
  transaction,
  onInvestigate,
  investigating,
  onBack,
}: TransactionHeaderProps) {
  const diff = Number(transaction.difference);
  const isOverpayment = diff < 0;
  const isUnderpayment = diff > 0;
  const hasDiscrepancy = diff !== 0 || Boolean(transaction.discrepancy_type);
  const canInvestigate =
    hasDiscrepancy &&
    transaction.status !== "RECONCILED" &&
    transaction.status !== "RESOLVED";

  const severityColor =
    transaction.severity === "CRITICAL"
      ? "border-rose-500/40 bg-rose-500/15 text-rose-300"
      : transaction.severity === "HIGH"
      ? "border-orange-500/40 bg-orange-500/15 text-orange-300"
      : transaction.severity === "MEDIUM"
      ? "border-yellow-500/40 bg-yellow-500/15 text-yellow-300"
      : "border-slate-500/40 bg-slate-500/15 text-slate-300";

  return (
    <header className="mb-8 rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (onBack) {
                onBack();
              } else if (window.history.length > 1) {
                window.history.back();
              }
            }}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-[#071a2b] text-muted-foreground transition hover:border-primary hover:text-white"
            title="Back to previous view"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold tracking-[0.18em] text-primary">TRANSACTION</span>
              <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${severityColor}`}>
                {transaction.severity || "MEDIUM"} SEVERITY
              </span>
              <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${getStatusColor(transaction.status)}`}>
                {transaction.status.replaceAll("_", " ")}
              </span>
            </div>
            <h1 className="mt-1 font-mono text-2xl font-bold text-white md:text-3xl">{transaction.id}</h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {canInvestigate && onInvestigate && (
            <button
              onClick={onInvestigate}
              disabled={investigating}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-emerald-400 px-5 py-2.5 text-xs font-bold text-[#071a2b] shadow-lg shadow-primary/20 transition hover:opacity-90 disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              {investigating
                ? "Running LangGraph Workflow..."
                : transaction.investigation?.status === "COMPLETED"
                ? "Re-Investigate"
                : "Investigate"}
            </button>
          )}


          <div className="rounded-xl border border-border bg-[#071a2b] px-4 py-2.5 text-right">
            <div className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Investigation Status</div>
            <div className="mt-0.5 text-xs font-bold text-foreground">
              {transaction.investigation?.status ?? "NOT STARTED"}
              {["PENDING", "RUNNING"].includes(transaction.investigation?.status ?? "") && (
                <Loader2 className="ml-2 inline h-3.5 w-3.5 animate-spin text-primary" />
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-xl border border-border bg-[#071a2b] p-3.5">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Customer</div>
          <div className="mt-1 truncate text-xs font-bold text-white" title={transaction.customer}>
            {transaction.customer}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-[#071a2b] p-3.5">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Expected Amount</div>
          <div className="mt-1 text-xs font-bold text-white">{formatCurrency(transaction.expected_amount)}</div>
        </div>

        <div className="rounded-xl border border-border bg-[#071a2b] p-3.5">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Actual Amount</div>
          <div className="mt-1 text-xs font-bold text-emerald-400">{formatCurrency(transaction.actual_amount)}</div>
        </div>

        <div className="rounded-xl border border-border bg-[#071a2b] p-3.5">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Difference</div>
          <div
            className={`mt-1 text-xs font-bold ${
              diff === 0
                ? "text-slate-400"
                : isOverpayment
                ? "text-emerald-400"
                : "text-rose-400"
            }`}
          >
            {isOverpayment ? `+${formatCurrency(Math.abs(diff))}` : isUnderpayment ? `-${formatCurrency(diff)}` : "$0.00"}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-[#071a2b] p-3.5">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Discrepancy Type</div>
          <div className="mt-1 truncate text-xs font-bold text-yellow-300">
            {transaction.discrepancy_type ? transaction.discrepancy_type.replaceAll("_", " ") : "NONE"}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-[#071a2b] p-3.5">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Period / Date</div>
          <div className="mt-1 text-xs font-medium text-muted-foreground">
            {transaction.period} • {transaction.date}
          </div>
        </div>
      </div>
    </header>
  );
}
