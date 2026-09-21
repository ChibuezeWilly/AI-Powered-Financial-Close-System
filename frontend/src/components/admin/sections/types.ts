export type TransactionRecord = {
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
  user?: { id: number; full_name: string; email: string } | null;
};

export type InvestigationRecord = {
  id: string;
  transaction_id: string;
  status: string;
  root_cause: string | null;
  recommendation: string | null;
  confidence: number | null;
  timeline: string[];
};

export type DocumentRecord = {
  id: string;
  filename: string;
  document_type: string;
  file_path: string;
  status: string;
  accounting_period?: string;
  records_created?: number;
  created_at: string;
};

export type UserRecord = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  transaction_count: number;
  total_balance: number;
};

export type AccountRecord = {
  id: string;
  code: string;
  name: string;
  account_type: string;
  normal_balance: string;
  is_active: boolean;
  transaction_count: number;
  total_balance: number;
};

export const formatCurrency = (val: number, cur = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: cur, maximumFractionDigits: 2 }).format(val);

export const getStatusBadge = (status: string) => {
  const map: Record<string, string> = {
    RECONCILED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    RESOLVED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    DISCREPANCY_DETECTED: "bg-red-500/15 text-red-300 border-red-500/40",
    INVESTIGATING: "bg-orange-500/15 text-orange-300 border-orange-500/40 animate-pulse",
    AWAITING_HUMAN_APPROVAL: "bg-violet-500/15 text-violet-300 border-violet-500/40",
    AWAITING_MANAGER_APPROVAL: "bg-yellow-500/15 text-yellow-300 border-yellow-500/40",
    APPROVED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    REJECTED: "bg-red-500/15 text-red-300 border-red-500/40",
    ESCALATED: "bg-orange-500/15 text-orange-300 border-orange-500/40",
  };
  return map[status] ?? "bg-slate-500/15 text-slate-300 border-slate-500/40";
};

export const getSeverityBadge = (sev: string) => {
  const map: Record<string, string> = {
    CRITICAL: "bg-red-950 text-red-300 border-red-800",
    HIGH: "bg-rose-950/80 text-rose-300 border-rose-700/60",
    MEDIUM: "bg-amber-950/80 text-amber-300 border-amber-700/60",
    LOW: "bg-sky-950/80 text-sky-300 border-sky-700/60",
    NONE: "bg-emerald-950/80 text-emerald-300 border-emerald-700/60",
  };
  return map[sev] ?? "bg-slate-800 text-slate-400 border-slate-700";
};
