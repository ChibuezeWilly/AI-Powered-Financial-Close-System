import { useNavigate } from "@tanstack/react-router";
import { TransactionRecord, formatCurrency } from "./types";

interface ApprovalsSectionProps {
  transactions: TransactionRecord[];
}

export function ApprovalsSection({ transactions }: ApprovalsSectionProps) {
  const navigate = useNavigate();

  return (
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
  );
}
