import { ArrowRight, CheckCircle2, GitFork, Network, ShieldAlert } from "lucide-react";
import { TransactionDetail, formatCurrency } from "./types";

interface FinancialRelationshipSectionProps {
  transaction: TransactionDetail;
}

export function FinancialRelationshipSection({ transaction }: FinancialRelationshipSectionProps) {
  const diff = Number(transaction.difference);

  return (
    <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          <div>
            <h2 className="text-base font-bold text-white">Financial Relationship Graph</h2>
            <p className="text-[11px] text-muted-foreground">Authoritative Knowledge Graph from Neo4j & PostgreSQL</p>
          </div>
        </div>
        <span className="rounded-full border border-emerald-500/40 bg-emerald-500/15 px-2.5 py-0.5 font-mono text-[10px] font-bold text-emerald-300">
          NEO4J RELATIONSHIPS
        </span>
      </div>

      <div className="overflow-x-auto pb-2">
        <div className="flex min-w-[760px] items-center justify-between gap-2">
          {/* 1. Customer */}
          <div className="flex flex-1 flex-col items-center rounded-xl border border-border bg-[#071a2b] p-3 text-center">
            <span className="text-[10px] uppercase font-bold text-muted-foreground">Customer Entity</span>
            <span className="mt-1 truncate max-w-[130px] font-bold text-white text-xs" title={transaction.customer}>
              {transaction.customer}
            </span>
          </div>

          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

          {/* 2. Invoice */}
          <div className="flex flex-1 flex-col items-center rounded-xl border border-border bg-[#071a2b] p-3 text-center">
            <span className="text-[10px] uppercase font-bold text-muted-foreground">Posted Invoice</span>
            <span className="mt-1 font-mono text-xs font-bold text-white">
              {transaction.invoice_id || "INV-1001"}
            </span>
            <span className="text-[10px] text-muted-foreground">{formatCurrency(transaction.expected_amount)}</span>
          </div>

          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

          {/* 3. Payment */}
          <div className="flex flex-1 flex-col items-center rounded-xl border border-border bg-[#071a2b] p-3 text-center">
            <span className="text-[10px] uppercase font-bold text-muted-foreground">Payment Received</span>
            <span className="mt-1 font-mono text-xs font-bold text-emerald-400">
              {transaction.id}
            </span>
            <span className="text-[10px] text-emerald-400/80">{formatCurrency(transaction.actual_amount)}</span>
          </div>

          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

          {/* 4. Variance / Discrepancy */}
          <div className="flex flex-1 flex-col items-center rounded-xl border border-border bg-[#071a2b] p-3 text-center">
            <span className="text-[10px] uppercase font-bold text-muted-foreground">Discrepancy</span>
            <span className={`mt-1 font-mono text-xs font-bold ${diff === 0 ? "text-slate-400" : "text-yellow-400"}`}>
              {diff === 0 ? "$0.00" : `${diff < 0 ? "+" : "-"}${formatCurrency(Math.abs(diff))}`}
            </span>
            <span className="text-[10px] text-yellow-300/80 truncate max-w-[120px]">
              {transaction.discrepancy_type?.replaceAll("_", " ") || "No Variance"}
            </span>
          </div>

          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

          {/* 5. Policy */}
          <div className="flex flex-1 flex-col items-center rounded-xl border border-border bg-[#071a2b] p-3 text-center">
            <span className="text-[10px] uppercase font-bold text-muted-foreground">Policy Rule</span>
            <span className="mt-1 font-mono text-xs font-bold text-purple-300">
              FIN-042
            </span>
            <span className="text-[10px] text-muted-foreground">Authorization Matrix</span>
          </div>

          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

          {/* 6. Human Approval & Resolution */}
          <div className="flex flex-1 flex-col items-center rounded-xl border border-primary/40 bg-[#0a2238] p-3 text-center">
            <span className="text-[10px] uppercase font-bold text-primary">Governance</span>
            <span className="mt-1 text-xs font-bold text-white">
              {transaction.status === "RESOLVED" || transaction.status === "RECONCILED" ? "Reconciled" : "Human Decision"}
            </span>
            <span className="text-[10px] text-muted-foreground">
              {transaction.status === "AWAITING_MANAGER_APPROVAL" ? "Manager Review" : "Finance Admin"}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
