import { useState } from "react";
import { ChevronDown, ChevronUp, Database, ExternalLink, FileText, History, Layers } from "lucide-react";
import { TransactionDetail, formatPercent } from "./types";

interface EvidenceSectionProps {
  transaction: TransactionDetail;
  evidenceLoading: boolean;
  openEvidence: (sourceId: string) => void;
}

export function EvidenceSection({
  transaction,
  evidenceLoading,
  openEvidence,
}: EvidenceSectionProps) {
  const evidence = transaction.investigation?.evidence ?? [];
  const precedents = transaction.pinecone_precedents ?? [];
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({});

  const toggleExpand = (idx: number) => {
    setExpandedIndices((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getSourceBadge = (sourceType: string) => {
    const s = sourceType.toLowerCase();
    if (s.includes("postgres")) return "border-blue-500/40 bg-blue-500/10 text-blue-300";
    if (s.includes("ledger")) return "border-sky-500/40 bg-sky-500/10 text-sky-300";
    if (s.includes("pinecone")) return "border-purple-500/40 bg-purple-500/10 text-purple-300";
    if (s.includes("neo4j")) return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
    if (s.includes("policy")) return "border-yellow-500/40 bg-yellow-500/10 text-yellow-300";
    return "border-primary/40 bg-primary/10 text-primary";
  };

  return (
    <div className="space-y-6">
      {/* 1. Retrieved Evidence Section */}
      <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <h2 className="text-base font-bold text-white">Retrieved Evidence & Citations</h2>
          </div>
          <span className="text-xs font-semibold text-muted-foreground">
            {evidence.length} Evidence Records
          </span>
        </div>

        {evidence.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border/80 bg-[#071a2b] p-6 text-center text-xs text-muted-foreground">
            No evidence records retrieved yet. Run investigation to load contextual documents.
          </div>
        ) : (
          <div className="space-y-3">
            {evidence.map((item, index) => {
              const isExpanded = expandedIndices[index] ?? true;
              return (
                <div
                  key={`${item.source_id}-${index}`}
                  className="overflow-hidden rounded-xl border border-border/80 bg-[#071a2b] transition hover:border-primary/50"
                >
                  <div
                    onClick={() => toggleExpand(index)}
                    className="flex cursor-pointer flex-wrap items-center justify-between gap-3 p-4 select-none"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className={`rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-bold ${getSourceBadge(item.source_type)}`}>
                        {item.source_type}
                      </span>
                      <span className="font-mono text-xs font-bold text-white">{item.source_id}</span>
                      <span className="text-xs text-muted-foreground truncate max-w-[280px]">{item.title}</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2 font-mono text-[11px]">
                        <span className="text-muted-foreground">
                          Relevance: <span className="font-bold text-emerald-400">{formatPercent(item.relevance)}</span>
                        </span>
                        <span className="text-muted-foreground">•</span>
                        <span className="text-muted-foreground">
                          Confidence: <span className="font-bold text-primary">{formatPercent(item.confidence)}</span>
                        </span>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-border/40 bg-[#0a2238]/60 p-4">
                      <div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">Relevant Excerpt</div>
                      <p className="mt-1 rounded-lg border border-border/50 bg-[#071a2b] p-3 text-xs leading-relaxed text-slate-200">
                        &ldquo;{item.excerpt}&rdquo;
                      </p>

                      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-[11px] text-muted-foreground">
                        <div className="flex items-center gap-3">
                          <span>Page / Section: <strong className="text-slate-200">{item.page ?? 1}</strong></span>
                          <span>•</span>
                          <span>Retrieved by: <strong className="text-primary">{item.agent_name || "Investigation Agent"}</strong></span>
                          <span>•</span>
                          <span>Method: <strong className="text-slate-200">{item.retrieval_method || "SQL"}</strong></span>
                        </div>

                        {item.source_id.startsWith("INV-") && (
                          <button
                            type="button"
                            disabled={evidenceLoading}
                            className="inline-flex items-center gap-1 font-semibold text-primary hover:text-emerald-300 disabled:opacity-50"
                            onClick={(e) => {
                              e.stopPropagation();
                              openEvidence(item.source_id);
                            }}
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                            {evidenceLoading ? "Loading…" : "Inspect Source Document"}
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* 2. Pinecone Historical Precedent Memory */}
      {precedents.length > 0 && (
        <section className="rounded-2xl border border-purple-500/30 bg-[#0d2638] p-6 shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="h-5 w-5 text-purple-400" />
              <div>
                <h2 className="text-base font-bold text-white">Similar Resolved Precedents</h2>
                <p className="text-[11px] text-purple-300/80">Historical Investigation Memory from Pinecone (Non-authoritative precedent)</p>
              </div>
            </div>
            <span className="rounded-full border border-purple-500/40 bg-purple-500/15 px-2.5 py-0.5 text-[10px] font-bold text-purple-300">
              PINECONE MEMORY
            </span>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {precedents.map((prec, pIdx) => (
              <div
                key={pIdx}
                className="rounded-xl border border-purple-500/20 bg-[#071a2b] p-4 transition hover:border-purple-500/50"
              >
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <span className="font-mono text-xs font-bold text-purple-300">Case: {prec.case_id}</span>
                  <span className="rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 font-mono text-[10px] font-bold text-purple-300">
                    Similarity: {formatPercent(prec.similarity)}
                  </span>
                </div>

                <div className="mt-2 text-xs">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground">Previous Root Cause</div>
                  <p className="mt-0.5 text-slate-200">{prec.root_cause}</p>
                </div>

                <div className="mt-2 text-xs">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground">Previous Resolution</div>
                  <p className="mt-0.5 text-emerald-300">{prec.resolution}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

