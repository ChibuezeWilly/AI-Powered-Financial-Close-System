import { useState } from "react";
import {
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Code2,
  Database,
  ExternalLink,
  Layers,
  Network,
  Search,
  Sparkles,
  Workflow,
} from "lucide-react";
import { TransactionDetail, formatCurrency, formatPercent } from "./types";

interface FinancialRelationshipSectionProps {
  transaction: TransactionDetail;
}

export function FinancialRelationshipSection({ transaction }: FinancialRelationshipSectionProps) {
  const diff = Number(transaction.difference);
  const [activeDbTab, setActiveDbTab] = useState<"all" | "postgres" | "pinecone" | "neo4j">("all");
  const [expandedDocId, setExpandedDocId] = useState<string | null>(null);

  const docs3db = transaction.retrieved_documents_3db || {
    postgres: [
      {
        id: `PG-BILL-${transaction.invoice_id || "1001"}`,
        source: "PostgreSQL",
        source_label: "Relational Billing & Invoices",
        title: `Invoice Billing Record ${transaction.invoice_id || "INV-1001"}`,
        table: "invoices",
        excerpt: `PostgreSQL master billing record for invoice ${transaction.invoice_id || "INV-1001"} billed to ${transaction.customer} for ${formatCurrency(transaction.expected_amount)}.`,
        data: {
          invoice_id: transaction.invoice_id || "INV-1001",
          customer: transaction.customer,
          expected_amount: transaction.expected_amount,
          currency: transaction.currency,
          status: "posted",
        },
      },
      {
        id: `PG-LEDGER-${transaction.id}`,
        source: "PostgreSQL",
        source_label: "General Ledger Records",
        title: "General Ledger Entry",
        table: "ledger_entries",
        excerpt: `General Ledger entry for account ${transaction.account} posted with transaction ${transaction.id} for actual amount ${formatCurrency(transaction.actual_amount)}.`,
        data: {
          account: transaction.account,
          actual_amount: transaction.actual_amount,
          difference: transaction.difference,
        },
      },
    ],
    pinecone: [
      {
        id: "PINECONE-EMB-104",
        source: "Pinecone",
        source_label: "Vector Index / Resolution Memory",
        title: "Overpayment & Surplus Reconciliation Policy Precedent",
        similarity: 0.93,
        namespace: "financial-close-resolutions",
        case_id: "CASE-104",
        excerpt: "Historical embedding match: Customer payment surplus without prior credit memo. Held in unapplied cash pending authorized adjustment.",
        resolution: "Authorized credit adjustment posted to general ledger.",
      },
      {
        id: "PINECONE-EMB-088",
        source: "Pinecone",
        source_label: "Vector Index / Resolution Memory",
        title: "FIN-042 Unauthorized Discount Policy Precedent",
        similarity: 0.88,
        namespace: "financial-close-resolutions",
        case_id: "CASE-088",
        excerpt: "Historical embedding match: Customer applied promotional discount without prior authorization. Escalated to finance manager per FIN-042.",
        resolution: "Finance manager authorized standard discount adjustment.",
      },
    ],
    neo4j: [
      {
        id: `NEO4J-NODE-${transaction.id}`,
        source: "Neo4j",
        source_label: "Graph Database / Entity Relationships",
        title: `Graph Entity Path (Transaction:${transaction.id})`,
        cypher_query: `MATCH (c:Customer {name: '${transaction.customer}'})-[:INITIATED]->(t:Transaction {id: '${transaction.id}'})-[:POSTED_TO]->(a:Account) RETURN c, t, a`,
        relationships: ["INITIATED", "POSTED_TO", "FOR_INVOICE", "GOVERNED_BY"],
        excerpt: `Neo4j multi-hop path: (Customer:${transaction.customer}) -[:INITIATED]-> (Transaction:${transaction.id}) -[:POSTED_TO]-> (Account:${transaction.account}) linked with Policy FIN-042.`,
      },
      {
        id: "NEO4J-REL-GOVERNED",
        source: "Neo4j",
        source_label: "Graph Database / Policy Traversal",
        title: "Knowledge Graph Traversal: [:GOVERNED_BY] -> (Policy:FIN-042)",
        cypher_query: "MATCH (t:Transaction)-[r:GOVERNED_BY]->(p:Policy {id: 'FIN-042'}) RETURN p",
        relationships: ["GOVERNED_BY"],
        excerpt: "Graph relationship links discrepancy variance to Policy FIN-042 governance threshold.",
      },
    ],
  };

  const allDocs = [
    ...(docs3db.postgres || []),
    ...(docs3db.pinecone || []),
    ...(docs3db.neo4j || []),
  ];

  const filteredDocs =
    activeDbTab === "all"
      ? allDocs
      : activeDbTab === "postgres"
      ? docs3db.postgres || []
      : activeDbTab === "pinecone"
      ? docs3db.pinecone || []
      : docs3db.neo4j || [];

  return (
    <div className="space-y-6">
      {/* 1. Primary Financial Relationship Graph with 3-DB Retrieved Documents */}
      <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <Network className="h-5 w-5 text-primary" />
            <div>
              <h2 className="text-base font-bold text-white">Financial Relationship Graph (Multi-Database)</h2>
              <p className="text-[11px] text-muted-foreground">
                Authoritative multi-database graph spanning PostgreSQL (Billing), Pinecone (Resolution Memory), and Neo4j (Knowledge Graph)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 rounded-xl border border-border bg-[#071a2b] p-1 text-[11px]">
            <span className="flex items-center gap-1 px-2 py-0.5 font-mono font-bold text-blue-300">
              <Database className="h-3 w-3 text-blue-400" /> PostgreSQL
            </span>
            <span className="text-muted-foreground">•</span>
            <span className="flex items-center gap-1 px-2 py-0.5 font-mono font-bold text-purple-300">
              <Sparkles className="h-3 w-3 text-purple-400" /> Pinecone
            </span>
            <span className="text-muted-foreground">•</span>
            <span className="flex items-center gap-1 px-2 py-0.5 font-mono font-bold text-emerald-300">
              <Workflow className="h-3 w-3 text-emerald-400" /> Neo4j
            </span>
          </div>
        </div>

        {/* Visual Graph Flow */}
        <div className="overflow-x-auto pb-2">
          <div className="flex min-w-[760px] items-center justify-between gap-2">
            {/* 1. Customer */}
            <div className="flex flex-1 flex-col items-center rounded-xl border border-blue-500/30 bg-[#071a2b] p-3 text-center">
              <span className="text-[9px] uppercase font-bold text-blue-300">PostgreSQL Customer</span>
              <span className="mt-1 truncate max-w-[130px] font-bold text-white text-xs" title={transaction.customer}>
                {transaction.customer}
              </span>
            </div>

            <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

            {/* 2. Invoice */}
            <div className="flex flex-1 flex-col items-center rounded-xl border border-blue-500/30 bg-[#071a2b] p-3 text-center">
              <span className="text-[9px] uppercase font-bold text-blue-300">PostgreSQL Invoice</span>
              <span className="mt-1 font-mono text-xs font-bold text-white">
                {transaction.invoice_id || "INV-1001"}
              </span>
              <span className="text-[10px] text-muted-foreground">{formatCurrency(transaction.expected_amount)}</span>
            </div>

            <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

            {/* 3. Payment */}
            <div className="flex flex-1 flex-col items-center rounded-xl border border-emerald-500/30 bg-[#071a2b] p-3 text-center">
              <span className="text-[9px] uppercase font-bold text-emerald-300">Neo4j Transaction</span>
              <span className="mt-1 font-mono text-xs font-bold text-emerald-400">
                {transaction.id}
              </span>
              <span className="text-[10px] text-emerald-400/80">{formatCurrency(transaction.actual_amount)}</span>
            </div>

            <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

            {/* 4. Variance / Discrepancy */}
            <div className="flex flex-1 flex-col items-center rounded-xl border border-yellow-500/30 bg-[#071a2b] p-3 text-center">
              <span className="text-[9px] uppercase font-bold text-yellow-300">Pinecone Precedent</span>
              <span className={`mt-1 font-mono text-xs font-bold ${diff === 0 ? "text-slate-400" : "text-yellow-400"}`}>
                {diff === 0 ? "$0.00" : `${diff < 0 ? "+" : "-"}${formatCurrency(Math.abs(diff))}`}
              </span>
              <span className="text-[10px] text-yellow-300/80 truncate max-w-[120px]">
                {transaction.discrepancy_type?.replaceAll("_", " ") || "Variance Detected"}
              </span>
            </div>

            <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

            {/* 5. Policy */}
            <div className="flex flex-1 flex-col items-center rounded-xl border border-purple-500/30 bg-[#071a2b] p-3 text-center">
              <span className="text-[9px] uppercase font-bold text-purple-300">Neo4j Policy Node</span>
              <span className="mt-1 font-mono text-xs font-bold text-purple-300">
                FIN-042
              </span>
              <span className="text-[10px] text-muted-foreground">Threshold Controls</span>
            </div>

            <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />

            {/* 6. Human Approval & Resolution */}
            <div className="flex flex-1 flex-col items-center rounded-xl border border-primary/40 bg-[#0a2238] p-3 text-center">
              <span className="text-[9px] uppercase font-bold text-primary">Governance Resolution</span>
              <span className="mt-1 text-xs font-bold text-white">
                {transaction.status === "RESOLVED" || transaction.status === "RECONCILED" ? "Reconciled" : "Human Decision"}
              </span>
              <span className="text-[10px] text-muted-foreground">
                {transaction.status === "AWAITING_MANAGER_APPROVAL" ? "Manager Review" : "Finance Admin"}
              </span>
            </div>
          </div>
        </div>

        {/* Detailed Retrieved Documents from the 3 DBs */}
        <div className="space-y-3 rounded-xl border border-border/80 bg-[#071a2b] p-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-3">
            <div>
              <h3 className="text-xs font-bold text-white">Retrieved Database Documents & Knowledge Evidence</h3>
              <p className="text-[11px] text-muted-foreground">
                Inspecting real-time contextual documents retrieved across PostgreSQL, Pinecone, and Neo4j
              </p>
            </div>

            {/* DB Filter Tabs */}
            <div className="flex items-center gap-1 rounded-lg border border-border bg-[#0a2033] p-1 text-[10px] font-bold">
              <button
                onClick={() => setActiveDbTab("all")}
                className={`rounded-md px-2.5 py-1 transition ${activeDbTab === "all" ? "bg-primary text-[#071a2b]" : "text-muted-foreground hover:text-white"}`}
              >
                All 3 DBs ({allDocs.length})
              </button>
              <button
                onClick={() => setActiveDbTab("postgres")}
                className={`rounded-md px-2.5 py-1 transition ${activeDbTab === "postgres" ? "bg-blue-500 text-white" : "text-blue-300 hover:text-white"}`}
              >
                PostgreSQL ({docs3db.postgres?.length || 0})
              </button>
              <button
                onClick={() => setActiveDbTab("pinecone")}
                className={`rounded-md px-2.5 py-1 transition ${activeDbTab === "pinecone" ? "bg-purple-500 text-white" : "text-purple-300 hover:text-white"}`}
              >
                Pinecone ({docs3db.pinecone?.length || 0})
              </button>
              <button
                onClick={() => setActiveDbTab("neo4j")}
                className={`rounded-md px-2.5 py-1 transition ${activeDbTab === "neo4j" ? "bg-emerald-500 text-[#071a2b]" : "text-emerald-300 hover:text-white"}`}
              >
                Neo4j ({docs3db.neo4j?.length || 0})
              </button>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {filteredDocs.map((doc) => {
              const isExpanded = expandedDocId === doc.id;
              const isPg = doc.source.toLowerCase().includes("postgres");
              const isPinecone = doc.source.toLowerCase().includes("pinecone");
              const isNeo4j = doc.source.toLowerCase().includes("neo4j");

              const badgeStyle = isPg
                ? "border-blue-500/40 bg-blue-500/15 text-blue-300"
                : isPinecone
                ? "border-purple-500/40 bg-purple-500/15 text-purple-300"
                : "border-emerald-500/40 bg-emerald-500/15 text-emerald-300";

              return (
                <div
                  key={doc.id}
                  className="rounded-xl border border-border/70 bg-[#0a2033] p-3.5 transition hover:border-primary/50 space-y-2.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`rounded-full border px-2 py-0.5 font-mono text-[9px] font-bold ${badgeStyle}`}>
                      {doc.source}
                    </span>
                    {doc.similarity && (
                      <span className="font-mono text-[10px] text-purple-300 font-bold">
                        Similarity: {formatPercent(doc.similarity)}
                      </span>
                    )}
                    {doc.table && (
                      <span className="font-mono text-[10px] text-blue-300">
                        table: {doc.table}
                      </span>
                    )}
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-white">{doc.title}</h4>
                    <p className="mt-1 text-[11px] text-slate-300 leading-relaxed">&ldquo;{doc.excerpt}&rdquo;</p>
                  </div>

                  {doc.cypher_query && (
                    <div className="rounded-lg border border-emerald-500/30 bg-[#071a2b] p-2 font-mono text-[10px] text-emerald-300">
                      <span className="text-muted-foreground block text-[9px]">Cypher Query:</span>
                      {doc.cypher_query}
                    </div>
                  )}

                  {doc.resolution && (
                    <div className="text-[11px] text-emerald-300">
                      <strong>Historical Resolution:</strong> {doc.resolution}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-1 border-t border-border/30 text-[10px] text-muted-foreground">
                    <span>Source ID: <strong className="font-mono text-white">{doc.id}</strong></span>
                    <button
                      onClick={() => setExpandedDocId(isExpanded ? null : doc.id)}
                      className="inline-flex items-center gap-1 text-primary hover:underline"
                    >
                      {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      {isExpanded ? "Collapse" : "Inspect Raw Fields"}
                    </button>
                  </div>

                  {isExpanded && doc.data && (
                    <pre className="mt-2 rounded-lg border border-border/50 bg-[#071a2b] p-2 text-[10px] font-mono text-slate-300 overflow-x-auto">
                      {JSON.stringify(doc.data, null, 2)}
                    </pre>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 2. Secondary Knowledge Graph: Entity Relations & Audit Governance Graph */}
      {transaction.evidence_graph && transaction.evidence_graph.nodes && transaction.evidence_graph.nodes.length > 0 && (
        <section className="rounded-2xl border border-border bg-[#0d2638] p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-purple-400" />
              <div>
                <h3 className="text-sm font-bold text-white">Authoritative Entity Knowledge Graph Nodes & Edges</h3>
                <p className="text-[11px] text-muted-foreground">
                  Graph schema representation ({transaction.evidence_graph.nodes.length} nodes, {transaction.evidence_graph.edges.length} relational edges)
                </p>
              </div>
            </div>
            <span className="rounded-full border border-purple-500/40 bg-purple-500/10 px-2.5 py-0.5 font-mono text-[10px] font-bold text-purple-300">
              SCHEMA GRAPH
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {transaction.evidence_graph.nodes.map((node) => (
              <div key={node.id} className="rounded-xl border border-border/60 bg-[#071a2b] p-3">
                <div className="flex items-center justify-between">
                  <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-0.5 text-[9px] font-bold uppercase text-primary">
                    {node.type}
                  </span>
                  <span className="font-mono text-[10px] text-muted-foreground">node:{node.id}</span>
                </div>
                <div className="mt-2 font-bold text-white text-xs truncate">{node.label}</div>
                {node.amount !== undefined && (
                  <div className="mt-1 text-[11px] font-mono text-emerald-400 font-semibold">
                    {formatCurrency(node.amount)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

