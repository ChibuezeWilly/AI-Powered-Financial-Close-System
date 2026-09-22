import { useState, useMemo } from "react";
import { useNavigate } from "@tanstack/react-router";
import { BarChart3, Filter, Search, Sparkles, X } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TransactionRecord, formatCurrency, getStatusBadge } from "./types";

interface TransactionsSectionProps {
  transactions: TransactionRecord[];
  selectedPeriod: string;
  setSelectedPeriod: (p: string) => void;
  months: string[];
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  loading: boolean;
}

export function TransactionsSection({
  transactions,
  selectedPeriod,
  setSelectedPeriod,
  months,
  searchQuery,
  setSearchQuery,
  loading,
}: TransactionsSectionProps) {
  const navigate = useNavigate();

  // Multi-Filter State
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [discrepancyFilter, setDiscrepancyFilter] = useState("ALL");
  const [minAmount, setMinAmount] = useState<string>("");
  const [maxAmount, setMaxAmount] = useState<string>("");

  // Filtered transactions
  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      // Query search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesQuery =
          tx.id.toLowerCase().includes(q) ||
          tx.customer.toLowerCase().includes(q) ||
          tx.invoice_id.toLowerCase().includes(q) ||
          tx.account.toLowerCase().includes(q);
        if (!matchesQuery) return false;
      }

      // Status
      if (statusFilter !== "ALL" && tx.status !== statusFilter) {
        return false;
      }

      // Severity
      if (severityFilter !== "ALL" && tx.severity !== severityFilter) {
        return false;
      }

      // Discrepancy type
      if (discrepancyFilter !== "ALL") {
        if (!tx.discrepancy_type || !tx.discrepancy_type.toUpperCase().includes(discrepancyFilter)) {
          return false;
        }
      }

      // Amount range
      const act = Number(tx.actual_amount);
      if (minAmount && act < Number(minAmount)) return false;
      if (maxAmount && act > Number(maxAmount)) return false;

      return true;
    });
  }, [transactions, searchQuery, statusFilter, severityFilter, discrepancyFilter, minAmount, maxAmount]);

  const reconciliationChartData = [
    { label: "Matched", count: transactions.filter((t) => ["RECONCILED", "RESOLVED"].includes(t.status)).length },
    { label: "Variance", count: transactions.filter((t) => t.difference !== 0).length },
    { label: "Pending", count: transactions.filter((t) => t.difference === 0 && !["RECONCILED", "RESOLVED"].includes(t.status)).length },
  ];

  const clearAllFilters = () => {
    setSearchQuery("");
    setStatusFilter("ALL");
    setSeverityFilter("ALL");
    setDiscrepancyFilter("ALL");
    setMinAmount("");
    setMaxAmount("");
  };

  const hasActiveFilters =
    searchQuery.trim() !== "" ||
    statusFilter !== "ALL" ||
    severityFilter !== "ALL" ||
    discrepancyFilter !== "ALL" ||
    minAmount !== "" ||
    maxAmount !== "";

  return (
    <div className="space-y-5">
      {/* Top Header & Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Month Switcher Tabs */}
        <div className="flex items-center gap-1.5 rounded-xl border border-border bg-[#0a2033] p-1.5">
          {months.map((m) => {
            const label = new Date(`${m}-01`).toLocaleDateString("en-US", { month: "short", year: "numeric" });
            return (
              <button
                key={m}
                onClick={() => setSelectedPeriod(m)}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
                  selectedPeriod === m
                    ? "bg-primary text-[#071a2b] shadow"
                    : "text-muted-foreground hover:text-white"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>

        {/* Global/Section Search with 'X' Clear Button */}
        <div className="relative min-w-[280px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search transactions, customers, invoices..."
            className="w-full rounded-xl border border-border bg-[#0a2033] py-2 pl-9 pr-9 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-2.5 flex h-4 w-4 items-center justify-center rounded-full bg-white/10 text-muted-foreground hover:bg-white/20 hover:text-white"
              title="Clear search query"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-[#0a2033] p-4 text-xs">
        <div className="flex items-center gap-1.5 text-muted-foreground font-semibold">
          <Filter className="h-3.5 w-3.5 text-primary" />
          <span>Filters:</span>
        </div>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-border bg-[#071a2b] px-2.5 py-1.5 text-white outline-none focus:border-primary"
        >
          <option value="ALL">All Statuses</option>
          <option value="AWAITING_HUMAN_APPROVAL">Awaiting Human Approval</option>
          <option value="AWAITING_MANAGER_APPROVAL">Awaiting Manager Approval</option>
          <option value="DISCREPANCY_DETECTED">Discrepancy Detected</option>
          <option value="INVESTIGATING">Investigating</option>
          <option value="RECONCILED">Reconciled</option>
          <option value="RESOLVED">Resolved</option>
          <option value="ESCALATED">Escalated</option>
        </select>

        {/* Severity Filter */}
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-lg border border-border bg-[#071a2b] px-2.5 py-1.5 text-white outline-none focus:border-primary"
        >
          <option value="ALL">All Severities</option>
          <option value="CRITICAL">Critical Severity</option>
          <option value="HIGH">High Severity</option>
          <option value="MEDIUM">Medium Severity</option>
          <option value="LOW">Low Severity</option>
        </select>

        {/* Discrepancy Type Filter */}
        <select
          value={discrepancyFilter}
          onChange={(e) => setDiscrepancyFilter(e.target.value)}
          className="rounded-lg border border-border bg-[#071a2b] px-2.5 py-1.5 text-white outline-none focus:border-primary"
        >
          <option value="ALL">All Discrepancy Types</option>
          <option value="OVERPAYMENT">Overpayment</option>
          <option value="DISCOUNT">Undocumented Discount</option>
          <option value="DUPLICATE">Duplicate Payment</option>
          <option value="TIMING">Timing Difference</option>
        </select>

        {/* Amount Range */}
        <div className="flex items-center gap-1.5">
          <input
            type="number"
            value={minAmount}
            onChange={(e) => setMinAmount(e.target.value)}
            placeholder="Min $"
            className="w-20 rounded-lg border border-border bg-[#071a2b] px-2 py-1.5 text-white placeholder-muted-foreground outline-none focus:border-primary"
          />
          <span className="text-muted-foreground">-</span>
          <input
            type="number"
            value={maxAmount}
            onChange={(e) => setMaxAmount(e.target.value)}
            placeholder="Max $"
            className="w-20 rounded-lg border border-border bg-[#071a2b] px-2 py-1.5 text-white placeholder-muted-foreground outline-none focus:border-primary"
          />
        </div>

        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="ml-auto inline-flex items-center gap-1 rounded-lg border border-border bg-white/5 px-2.5 py-1.5 text-[11px] font-semibold text-muted-foreground hover:bg-white/10 hover:text-white"
          >
            <X className="h-3 w-3" /> Reset Filters
          </button>
        )}
      </div>

      {/* Chart Section */}
      <div className="rounded-2xl border border-border bg-[#0a2033] p-5 shadow">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">Reconciliation Status Breakdown</h3>
            <p className="text-xs text-muted-foreground">Invoice matching results for the active period ({selectedPeriod})</p>
          </div>
          <BarChart3 className="h-4 w-4 text-primary" />
        </div>
        <div className="mt-4 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={reconciliationChartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#1B3A4D" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "#8FA3B8", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fill: "#8FA3B8", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: "rgba(255,255,255,0.04)" }} contentStyle={{ background: "#0d2638", border: "1px solid #1B3A4D", borderRadius: 12, color: "#F5F7FA" }} />
              <Bar dataKey="count" fill="#19C37D" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
        <div className="border-b border-border bg-[#0d2638] px-5 py-3 flex items-center justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Transactions for {selectedPeriod} ({filteredTransactions.length} records)
            </p>
            <p className="text-[11px] text-muted-foreground">
              Click any transaction row to inspect evidence, AI findings, and execute decisions.
            </p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border/60 text-muted-foreground">
                <th className="px-5 py-3 font-semibold">Date</th>
                <th className="px-5 py-3 font-semibold">Transaction ID</th>
                <th className="px-5 py-3 font-semibold">Customer</th>
                <th className="px-5 py-3 font-semibold">Severity</th>
                <th className="px-5 py-3 font-semibold">Invoice ID</th>
                <th className="px-5 py-3 font-semibold text-right">Expected</th>
                <th className="px-5 py-3 font-semibold text-right">Actual</th>
                <th className="px-5 py-3 font-semibold text-right">Difference</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-5 py-8 text-center text-muted-foreground">
                    {loading ? "Loading transactions..." : "No matching transactions found."}
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((tx) => {
                  const diffNum = Number(tx.difference);
                  const isOver = diffNum < 0;
                  const isUnder = diffNum > 0;
                  const severityBadge =
                    tx.severity === "CRITICAL"
                      ? "border-rose-500/40 bg-rose-500/15 text-rose-300"
                      : tx.severity === "HIGH"
                      ? "border-orange-500/40 bg-orange-500/15 text-orange-300"
                      : tx.severity === "MEDIUM"
                      ? "border-yellow-500/40 bg-yellow-500/15 text-yellow-300"
                      : "border-slate-500/40 bg-slate-500/15 text-slate-300";

                  return (
                    <tr
                      key={tx.id}
                      onClick={() => navigate({ to: `/transactions/${tx.id}` })}
                      className="cursor-pointer transition hover:bg-white/5"
                    >
                      <td className="px-5 py-3.5 font-mono text-muted-foreground">{tx.date}</td>
                      <td className="px-5 py-3.5 font-mono font-bold text-white">{tx.id}</td>
                      <td className="px-5 py-3.5 font-medium text-white">{tx.customer}</td>
                      <td className="px-5 py-3.5">
                        <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${severityBadge}`}>
                          {tx.severity || "MEDIUM"}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-muted-foreground">{tx.invoice_id}</td>
                      <td className="px-5 py-3.5 text-right font-medium text-muted-foreground">
                        {formatCurrency(tx.expected_amount)}
                      </td>
                      <td className="px-5 py-3.5 text-right font-bold text-white">
                        {formatCurrency(tx.actual_amount)}
                      </td>
                      <td className="px-5 py-3.5 text-right font-bold">
                        <span className={diffNum === 0 ? "text-slate-400" : isOver ? "text-emerald-400" : "text-rose-400"}>
                          {isOver ? `+${formatCurrency(Math.abs(diffNum))}` : isUnder ? `-${formatCurrency(diffNum)}` : "$0.00"}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${getStatusBadge(tx.status)}`}>
                          {tx.status.replaceAll("_", " ")}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => navigate({ to: `/transactions/${tx.id}` })}
                          className="inline-flex items-center gap-1 rounded-lg border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary hover:bg-primary hover:text-[#071a2b]"
                        >
                          {tx.investigation_status === "COMPLETED" && tx.difference !== 0
                            ? "Review Approval"
                            : tx.status === "DISCREPANCY_DETECTED"
                            ? "Investigate"
                            : "Inspect"}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
