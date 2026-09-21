import { Bot, Cpu, FileSpreadsheet, FileText, Scale } from "lucide-react";
import { AgentFindingItem, formatPercent } from "./types";

interface AgentFindingsSectionProps {
  findings?: AgentFindingItem[];
}

export function AgentFindingsSection({ findings }: AgentFindingsSectionProps) {
  if (!findings || findings.length === 0) {
    return null;
  }

  const getAgentIcon = (agentName: string) => {
    const lower = agentName.toLowerCase();
    if (lower.includes("reconciliation")) return <FileSpreadsheet className="h-4 w-4 text-primary" />;
    if (lower.includes("invoice") || lower.includes("document")) return <FileText className="h-4 w-4 text-emerald-400" />;
    if (lower.includes("policy")) return <Scale className="h-4 w-4 text-yellow-400" />;
    if (lower.includes("ledger")) return <Cpu className="h-4 w-4 text-sky-400" />;
    return <Bot className="h-4 w-4 text-violet-400" />;
  };

  return (
    <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <h2 className="text-base font-bold text-white">AI Agent Investigation Findings</h2>
        </div>
        <span className="text-xs font-semibold text-muted-foreground">
          {findings.length} Specialized Agents Evaluated
        </span>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {findings.map((item, idx) => (
          <div
            key={idx}
            className="flex flex-col justify-between rounded-xl border border-border/80 bg-[#071a2b] p-4 transition hover:border-primary/50"
          >
            <div>
              <div className="flex items-center justify-between gap-2 border-b border-border/40 pb-2">
                <div className="flex items-center gap-2">
                  {getAgentIcon(item.agent)}
                  <span className="text-xs font-bold text-white">{item.agent}</span>
                </div>
                <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-primary">
                  Confidence: {formatPercent(item.confidence)}
                </span>
              </div>

              <p className="mt-2 text-[11px] font-medium text-muted-foreground italic">
                {item.purpose}
              </p>

              <div className="mt-3 rounded-lg border border-border/60 bg-[#0a2238] p-3">
                <div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">Finding</div>
                <p className="mt-1 text-xs font-semibold text-foreground leading-relaxed">
                  {item.finding}
                </p>
              </div>

              {item.reasoning && (
                <div className="mt-2 text-[11px] text-muted-foreground">
                  <span className="font-semibold text-slate-300">Reasoning: </span>
                  {item.reasoning}
                </div>
              )}
            </div>

            {item.documents && item.documents.length > 0 && (
              <div className="mt-3 flex flex-wrap items-center gap-1.5 pt-2 border-t border-border/30">
                <span className="text-[10px] uppercase text-muted-foreground">Cited Docs:</span>
                {item.documents.map((doc, dIdx) => (
                  <span
                    key={dIdx}
                    className="rounded bg-white/5 px-2 py-0.5 font-mono text-[10px] text-primary"
                  >
                    {doc}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
