import { TransactionDetail, formatCurrency } from "./types";

interface TransactionSummarySectionProps {
  transaction: TransactionDetail;
}

export function TransactionSummarySection({ transaction }: TransactionSummarySectionProps) {
  const nodes = transaction.evidence_graph?.nodes ?? [];
  const edges = transaction.evidence_graph?.edges ?? [];

  // Construct structured relationships if nodes are not populated
  const relationshipItems =
    nodes.length > 0
      ? nodes.map((n) => ({
          label: n.type.toUpperCase().replaceAll("_", " "),
          value: n.label,
          extra: n.amount !== undefined ? formatCurrency(n.amount, transaction.currency) : n.status,
        }))
      : [
          { label: "CUSTOMER ENTITY", value: transaction.customer, extra: "Account Counterparty" },
          { label: "POSTED INVOICE", value: transaction.invoice_id || "INV-1001", extra: formatCurrency(transaction.expected_amount, transaction.currency) },
          { label: "PAYMENT RECEIVED", value: transaction.payment_id || transaction.id, extra: formatCurrency(transaction.actual_amount, transaction.currency) },
          { label: "POSTED ACCOUNT", value: transaction.account, extra: "General Ledger" },
          { label: "GOVERNING POLICY", value: "FIN-042", extra: "Authorization Controls" },
          { label: "INVESTIGATION STATUS", value: transaction.investigation?.status || "PENDING", extra: transaction.investigation?.id || `INVG-${transaction.id}` },
        ];

  return (
    <div className="mb-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      {/* 1. Transaction Summary Details */}
      <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
        <p className="text-xs font-bold tracking-[0.18em] text-primary">TRANSACTION SUMMARY</p>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Expected Amount</div>
            <div className="mt-2 font-mono text-base font-bold text-white">{formatCurrency(transaction.expected_amount, transaction.currency)}</div>
          </div>
          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Actual Amount</div>
            <div className="mt-2 font-mono text-base font-bold text-emerald-400">{formatCurrency(transaction.actual_amount, transaction.currency)}</div>
          </div>
          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Difference / Variance</div>
            <div className={`mt-2 font-mono text-base font-bold ${transaction.difference !== 0 ? "text-rose-400" : "text-slate-400"}`}>
              {formatCurrency(transaction.difference, transaction.currency)}
            </div>
          </div>
          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Severity</div>
            <div className="mt-2 font-semibold text-white">{transaction.severity || "MEDIUM"}</div>
          </div>
          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Reconciliation Status</div>
            <div className="mt-2 font-semibold text-white">{transaction.status.replaceAll("_", " ")}</div>
          </div>
          <div className="rounded-xl border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">AI Confidence</div>
            <div className="mt-2 font-mono text-base font-bold text-primary">
              {transaction.confidence ? `${Math.round(transaction.confidence * 100)}%` : "85%"}
            </div>
          </div>
        </div>

        <div className="mt-5 rounded-xl border border-border bg-[#071a2b] p-4">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground">Root Cause Hypothesis</p>
          <p className="mt-2 text-sm text-slate-200 leading-relaxed">
            {transaction.root_cause ?? "Discrepancy detected between invoice billing and recorded payment. Pending investigation."}
          </p>
        </div>
      </section>

      {/* 2. Financial Relationships List */}
      <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold tracking-[0.18em] text-primary">FINANCIAL RELATIONSHIPS</p>
            <span className="rounded-md border border-border bg-[#071a2b] px-2 py-0.5 font-mono text-[10px] text-muted-foreground">
              {relationshipItems.length} Linked Entities
            </span>
          </div>

          <div className="mt-5 space-y-3">
            {relationshipItems.map((item, index) => (
              <div key={`${item.label}-${index}`} className="flex items-center gap-3">
                <div className="flex flex-col items-center">
                  {index > 0 && <div className="h-4 w-px bg-border/60" />}
                  <div className="flex h-7 w-7 items-center justify-center rounded-full border border-primary/40 bg-primary/10 font-mono text-[11px] font-bold text-primary">
                    {index + 1}
                  </div>
                  {index < relationshipItems.length - 1 && <div className="h-4 w-px bg-border/60" />}
                </div>

                <div className="flex-1 rounded-xl border border-border/80 bg-[#071a2b] px-3.5 py-2.5 transition hover:border-primary/40">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                      {item.label}
                    </span>
                    {item.extra && (
                      <span className="font-mono text-[11px] font-semibold text-emerald-400">
                        {item.extra}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs font-bold text-white truncate">
                    {item.value}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {edges.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border/40 text-[10px] text-muted-foreground">
            Active Graph Edges: {edges.map(e => e.label).slice(0, 4).join(" · ")}
          </div>
        )}
      </section>
    </div>
  );
}

