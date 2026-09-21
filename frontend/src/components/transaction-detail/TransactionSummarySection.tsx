import { TransactionDetail, formatCurrency } from "./types";

interface TransactionSummarySectionProps {
  transaction: TransactionDetail;
}

export function TransactionSummarySection({ transaction }: TransactionSummarySectionProps) {
  const graph = transaction.evidence_graph ?? [];

  return (
    <div className="mb-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <section className="rounded-xl border border-border bg-[#0d2638] p-6">
        <p className="text-xs font-bold tracking-[0.18em] text-primary">TRANSACTION SUMMARY</p>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Expected</div>
            <div className="mt-2 font-semibold text-foreground">{formatCurrency(transaction.expected_amount, transaction.currency)}</div>
          </div>
          <div className="rounded-lg border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Actual</div>
            <div className="mt-2 font-semibold text-foreground">{formatCurrency(transaction.actual_amount, transaction.currency)}</div>
          </div>
          <div className="rounded-lg border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Difference</div>
            <div className="mt-2 font-semibold text-red-300">{formatCurrency(transaction.difference, transaction.currency)}</div>
          </div>
          <div className="rounded-lg border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Severity</div>
            <div className="mt-2 font-semibold text-foreground">{transaction.severity}</div>
          </div>
          <div className="rounded-lg border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Status</div>
            <div className="mt-2 font-semibold text-foreground">{transaction.status.replaceAll("_", " ")}</div>
          </div>
          <div className="rounded-lg border border-border bg-[#071a2b] p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Confidence</div>
            <div className="mt-2 font-semibold text-foreground">{transaction.confidence ? `${(transaction.confidence * 100).toFixed(0)}%` : "n/a"}</div>
          </div>
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
  );
}
