export type AgentFindingItem = {
  agent: string;
  purpose: string;
  finding: string;
  confidence: number;
  documents: string[];
  reasoning: string;
};

export type EvidenceItem = {
  source_type: string;
  source_id: string;
  title: string;
  page?: number | null;
  excerpt: string;
  relevance: number;
  confidence: number;
  agent_name?: string;
  retrieval_method?: string;
};

export type PineconePrecedentItem = {
  case_id: string;
  similarity: number;
  root_cause: string;
  resolution: string;
  source?: string;
};

export type GraphNode = {
  id: string;
  label: string;
  type: string;
  amount?: number;
  status?: string;
};

export type GraphEdge = {
  source: string;
  target: string;
  label: string;
};

export type TransactionDetail = {
  id: string;
  period: string;
  date: string;
  customer: string;
  invoice_id: string;
  payment_id: string | null;
  account: string;
  currency: string;
  expected_amount: number;
  actual_amount: number;
  difference: number;
  discrepancy_type: string | null;
  severity: string;
  status: string;
  root_cause: string | null;
  recommendation: string | null;
  confidence: number | null;
  investigation?: {
    id: string;
    status: string;
    evidence: EvidenceItem[];
    agent_findings?: AgentFindingItem[];
    timeline: string[];
    root_cause?: string | null;
    recommendation?: string | null;
    customer_email_draft?: string | null;
    manager_escalation_draft?: string | null;
    final_summary?: string | null;
    confidence?: number | null;
    ai_model?: string | null;
    model_used?: string | null;
    fallback_used?: boolean;
    completed_at?: string | null;
  } | null;
  journal_entry?: { id: string; amount: number; status: string; debit: string; credit: string } | null;
  ledger_entries?: Array<{
    id: string;
    account_code: string;
    account_name: string;
    debit: number;
    credit: number;
    description: string;
    reference: string;
    posted_date: string;
  }>;
  evidence_graph?: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  pinecone_precedents?: PineconePrecedentItem[];
};

export type AuditTrail = {
  approvals: Array<{ decision: string; reason: string; decided_by: number; created_at: string }>;
  events: Array<{ action: string; actor_id: number | null; created_at: string }>;
};

export const formatCurrency = (value: number | null | undefined, currency = "USD") => {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return "$0.00";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));
};

export const formatPercent = (val: number | null | undefined): string => {
  if (val === null || val === undefined || isNaN(Number(val))) {
    return "Not available";
  }
  const num = Number(val);
  const normalized = num <= 1.0 ? num * 100 : num;
  if (isNaN(normalized)) return "Not available";
  return `${Math.round(normalized)}%`;
};

export const formatTimestamp = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
};

export const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    RECONCILED: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
    RESOLVED: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
    AWAITING_HUMAN_APPROVAL: "border-violet-500/40 bg-violet-500/10 text-violet-300",
    AWAITING_MANAGER_APPROVAL: "border-yellow-500/40 bg-yellow-500/10 text-yellow-300",
    APPROVED: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
    ADJUSTED: "border-teal-500/40 bg-teal-500/10 text-teal-300",
    ADJUSTMENT_PENDING: "border-sky-500/40 bg-sky-500/10 text-sky-300",
    REJECTED: "border-red-500/40 bg-red-500/10 text-red-300",
    REJECTED_MANAGER: "border-rose-500/40 bg-rose-500/10 text-rose-300",
    ESCALATED: "border-orange-500/40 bg-orange-500/10 text-orange-300",
    INVESTIGATING: "border-orange-500/40 bg-orange-500/10 text-orange-300",
    PAYMENT_REQUESTED: "border-amber-500/40 bg-amber-500/10 text-amber-300",
    PAYMENT_PENDING: "border-amber-500/40 bg-amber-500/10 text-amber-300",
    DISCREPANCY_DETECTED: "border-rose-500/40 bg-rose-500/10 text-rose-300",
  };
  return colors[status] ?? "border-primary/30 bg-primary/10 text-primary";
};
