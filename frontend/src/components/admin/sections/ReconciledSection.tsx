import { useNavigate } from "@tanstack/react-router";
import { CheckCircle2 } from "lucide-react";
import { TransactionRecord, formatCurrency } from "./types";

interface ReconciledSectionProps {
  transactions: TransactionRecord[];
  selectedPeriod: string;
  setSelectedPeriod: (p: string) => void;
  months: string[];
}

export function ReconciledSection({
  transactions,
  selectedPeriod,
  setSelectedPeriod,
  months,
}: ReconciledSectionProps) {
  const navigate = useNavigate();

  return (
    <div className="space-y-2 md:space-y-5">
      <div className="flex flex-col md:flex-row gap-3   items-start md:items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Reconciled Accounts</h2>
          <p className="text-xs text-muted-foreground">
            Historical verified transactions with balanced accounts and zero
            variance.
          </p>
        </div>
        <div className="flex justify-center items-center gap-1.5 rounded-xl border border-border bg-[#0a2033] p-1.5">
          {months.map((month) => (
            <button
              key={month}
              onClick={() => setSelectedPeriod(month)}
              className={`rounded-lg px-1 md:px-3 py-1.5 text-xs font-bold transition ${
                selectedPeriod === month
                  ? "bg-primary text-[#071a2b] shadow"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              {new Date(`${month}-01`).toLocaleDateString("en-US", {
                month: "short",
                year: "numeric",
              })}
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
                  onClick={() =>
                    navigate({
                      to: "/transactions/$transactionId",
                      params: { transactionId: tx.id },
                    })
                  }
                  className="cursor-pointer transition hover:bg-white/5"
                >
                  <td className="px-5 py-3.5 text-muted-foreground">
                    {tx.date}
                  </td>
                  <td className="px-5 py-3.5 font-mono font-bold text-primary">
                    {tx.id}
                  </td>
                  <td className="px-5 py-3.5 font-medium text-white">
                    {tx.customer}
                  </td>
                  <td className="px-5 py-3.5 text-muted-foreground">
                    {tx.account}
                  </td>
                  <td className="px-5 py-3.5 text-right font-medium text-emerald-400">
                    {formatCurrency(tx.actual_amount)}
                  </td>
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
  );
}
