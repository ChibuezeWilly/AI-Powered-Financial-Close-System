import { useNavigate } from "@tanstack/react-router";
import { Clock, Play } from "lucide-react";
import { TransactionRecord, formatCurrency, getStatusBadge } from "./types";

interface ReconciliationSectionProps {
  transactions: TransactionRecord[];
  selectedPeriod: string;
  runReconcile: () => void;
  actionLoading: string | null;
}

export function ReconciliationSection({
  transactions,
  selectedPeriod,
  runReconcile,
  actionLoading,
}: ReconciliationSectionProps) {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-primary/30 bg-gradient-to-r from-emerald-950/40 via-[#0a2033] to-[#0a2033] p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
              <Clock className="h-3.5 w-3.5" /> CURRENT CLOSE PERIOD: {new Date(`${selectedPeriod}-01`).toLocaleDateString("en-US", { month: "long", year: "numeric" }).toUpperCase()} ({selectedPeriod})
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
            {new Date(`${selectedPeriod}-01`).toLocaleDateString("en-US", { month: "long", year: "numeric" })} Transactions ({transactions.length} items)
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
  );
}
