import { useState, useMemo } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ArrowRight, Filter, Search, X } from "lucide-react";
import { TransactionRecord, formatCurrency, getSeverityBadge, getStatusBadge } from "./types";

interface DiscrepanciesSectionProps {
  transactions: TransactionRecord[];
}

export function DiscrepanciesSection({ transactions }: DiscrepanciesSectionProps) {
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");

  const filtered = useMemo(() => {
    return transactions.filter((tx) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const match =
          tx.id.toLowerCase().includes(q) ||
          tx.customer.toLowerCase().includes(q) ||
          tx.invoice_id.toLowerCase().includes(q);
        if (!match) return false;
      }
      if (statusFilter !== "ALL" && tx.status !== statusFilter) return false;
      if (severityFilter !== "ALL" && tx.severity !== severityFilter) return false;
      if (typeFilter !== "ALL") {
        if (!tx.discrepancy_type || !tx.discrepancy_type.toUpperCase().includes(typeFilter)) {
          return false;
        }
      }
      return true;
    });
  }, [transactions, searchQuery, statusFilter, severityFilter, typeFilter]);

  const totalVariance = filtered.reduce((acc, t) => acc + Math.abs(t.difference), 0);

  return (
    <div className="space-y-5">
      {/* Top Banner */}
      <div className="rounded-2xl border border-rose-500/30 bg-[#0a2033] p-5 shadow">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white">Discrepancy Resolution Watch</h2>
            <p className="text-xs text-muted-foreground">
              All transactions with detected variances requiring active reconciliation, investigation, or managerial approval.
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">Filtered Variance Total</p>
            <p className="text-xl font-bold text-rose-400 font-mono">
              {formatCurrency(totalVariance)}
            </p>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-[#0a2033] p-4 text-xs">
        <div className="relative min-w-[240px] flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search discrepancies by ID, customer, invoice..."
            className="w-full rounded-xl border border-border bg-[#071a2b] py-2 pl-9 pr-8 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-white"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-border bg-[#071a2b] px-2.5 py-2 text-white outline-none focus:border-primary"
        >
          <option value="ALL">All Statuses</option>
          <option value="DISCREPANCY_DETECTED">Discrepancy Detected</option>
          <option value="INVESTIGATING">Investigating</option>
          <option value="AWAITING_HUMAN_APPROVAL">Awaiting Human Approval</option>
          <option value="AWAITING_MANAGER_APPROVAL">Awaiting Manager Approval</option>
          <option value="ESCALATED">Escalated</option>
        </select>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-lg border border-border bg-[#071a2b] px-2.5 py-2 text-white outline-none focus:border-primary"
        >
          <option value="ALL">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-lg border border-border bg-[#071a2b] px-2.5 py-2 text-white outline-none focus:border-primary"
        >
          <option value="ALL">All Discrepancy Types</option>
          <option value="OVERPAYMENT">Overpayment</option>
          <option value="DISCOUNT">Undocumented Discount</option>
          <option value="DUPLICATE">Duplicate Payment</option>
        </select>
      </div>

      {/* Discrepancies Table */}
      <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border/60 text-muted-foreground">
                <th className="px-5 py-3 font-semibold">Transaction ID</th>
                <th className="px-5 py-3 font-semibold">Customer</th>
                <th className="px-5 py-3 font-semibold">Discrepancy Type</th>
                <th className="px-5 py-3 font-semibold">Severity</th>
                <th className="px-5 py-3 font-semibold text-right">Variance</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-muted-foreground">
                    No discrepancies matching the active filters.
                  </td>
                </tr>
              ) : (
                filtered.map((tx) => (
                  <tr
                    key={tx.id}
                    onClick={() => navigate({ to: `/transactions/${tx.id}` })}
                    className="cursor-pointer transition hover:bg-white/5"
                  >
                    <td className="px-5 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                    <td className="px-5 py-3.5 font-medium text-white">{tx.customer}</td>
                    <td className="px-5 py-3.5 text-muted-foreground">
                      {tx.discrepancy_type?.replaceAll("_", " ") || "Variance Detected"}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`inline-flex rounded border px-2 py-0.5 text-[10px] font-bold ${getSeverityBadge(tx.severity)}`}>
                        {tx.severity}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right font-bold text-rose-400 font-mono">
                      {formatCurrency(tx.difference)}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(tx.status)}`}>
                        {tx.status.replaceAll("_", " ")}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <span className="inline-flex items-center gap-1 text-primary hover:underline">
                        Investigate <ArrowRight className="h-3 w-3" />
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
