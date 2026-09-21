import { CircleAlert, Loader2 } from "lucide-react";
import { TransactionDetail } from "./types";

interface InvestigationTimelineSectionProps {
  transaction: TransactionDetail;
  evidenceLoading: boolean;
  sourceDocument: { name: string; content: string } | null;
  setSourceDocument: (doc: { name: string; content: string } | null) => void;
}

export function InvestigationTimelineSection({
  transaction,
  evidenceLoading,
  sourceDocument,
  setSourceDocument,
}: InvestigationTimelineSectionProps) {
  const timeline = transaction.investigation?.timeline ?? ["Investigation scheduled", "Evidence pending"];

  return (
    <>
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
    </>
  );
}
