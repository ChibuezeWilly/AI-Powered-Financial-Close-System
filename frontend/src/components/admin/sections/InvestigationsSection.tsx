import { useNavigate } from "@tanstack/react-router";
import { ArrowRight, Sparkles } from "lucide-react";
import { InvestigationRecord, getStatusBadge } from "./types";

interface InvestigationsSectionProps {
  investigations: InvestigationRecord[];
}

export function InvestigationsSection({ investigations }: InvestigationsSectionProps) {
  const navigate = useNavigate();

  return (
    <div className="space-y-5">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-center md:justify-between gap-3 md:gap-0">
        <div>
          <h2 className="text-lg font-bold text-white">LangGraph AI Investigations</h2>
          <p className="text-xs text-muted-foreground">
            Multi-node autonomous agents running root-cause analysis via Hugging Face Inference Providers.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
          <Sparkles className="h-3.5 w-3.5" /> Model: meta-llama/Llama-3.3-70B-Instruct
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {investigations.map((inv) => (
          <div
            key={inv.id}
            className="flex flex-col justify-between rounded-2xl border border-border bg-[#0a2033] p-5 transition hover:border-primary/50"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm font-bold text-primary">{inv.id}</span>
                <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(inv.status)}`}>
                  {inv.status}
                </span>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Linked Transaction</p>
                <p className="font-mono text-xs font-bold text-white">{inv.transaction_id}</p>
              </div>
              {inv.root_cause && (
                <div className="rounded-xl border border-border/60 bg-[#071a2b] p-3 text-xs">
                  <p className="font-semibold text-white">Root Cause Hypothesis</p>
                  <p className="mt-1 text-muted-foreground">{inv.root_cause}</p>
                </div>
              )}
              {inv.recommendation && (
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-3 text-xs text-emerald-300">
                  <p className="font-semibold">AI Recommendation</p>
                  <p className="mt-1">{inv.recommendation}</p>
                </div>
              )}
              {inv.confidence !== null && (
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Confidence Score</span>
                  <span className="font-bold text-white">{(inv.confidence * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>

            <button
              onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: inv.transaction_id } })}
              className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl border border-primary/30 bg-primary/10 py-2.5 text-xs font-bold text-primary hover:bg-primary hover:text-[#071a2b]"
            >
              Inspect Evidence Graph & Act <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
