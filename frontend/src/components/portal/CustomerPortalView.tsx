import { useNavigate } from "@tanstack/react-router";
import { LogOut, Search } from "lucide-react";
import React from "react";

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
};

export type CustomerAccountData = {
  id: string;
  name: string;
  legal_name: string;
  customer_tier: string;
  country: string;
  currency: string;
  credit_limit: number;
  contact_email: string;
  total_amount: number;
  transaction_count: number;
};

export type PortalSearchResult = {
  query: string;
  total_matches: number;
  matching_amount: number;
  account_total: number;
  results: TransactionRecord[];
};

export type UserAccount = {
  id: number;
  full_name: string;
  email: string;
  role: string;
};

interface CustomerPortalViewProps {
  user: UserAccount;
  portalCustomer: CustomerAccountData | null;
  portalTxs: TransactionRecord[];
  portalTotal: number;
  selectedPeriod: string;
  setSelectedPeriod: (period: string) => void;
  months: string[];
  customerSearch: string;
  setCustomerSearch: (q: string) => void;
  handleCustomerSearch: (e: React.FormEvent) => void;
  customerSearchLoading: boolean;
  portalSearchResult: PortalSearchResult | null;
  setPortalSearchResult: (res: PortalSearchResult | null) => void;
  portalOffset: number;
  portalLoadingMore: boolean;
  fetchPortalData: (offset?: number, append?: boolean) => void;
  handleSignOut: () => void;
}

const formatCurrency = (val: number, cur = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: cur, maximumFractionDigits: 2 }).format(val);

const getStatusBadge = (status: string) => {
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

export function CustomerPortalView({
  user,
  portalCustomer,
  portalTxs,
  portalTotal,
  selectedPeriod,
  setSelectedPeriod,
  months,
  customerSearch,
  setCustomerSearch,
  handleCustomerSearch,
  customerSearchLoading,
  portalSearchResult,
  setPortalSearchResult,
  portalOffset,
  portalLoadingMore,
  fetchPortalData,
  handleSignOut,
}: CustomerPortalViewProps) {
  const navigate = useNavigate();
  const totalVolume = portalCustomer?.total_amount ?? portalTxs.reduce((acc, t) => acc + t.actual_amount, 0);

  return (
    <div className="min-h-screen bg-[#071A2B] text-foreground">
      <header className="flex h-16 items-center justify-between border-b border-border bg-[#0a2033] px-6 md:px-12">
        <div className="flex items-center gap-3">
          <img src="/logo2.jpg" alt="Logo" className="h-8 w-8 rounded-lg border border-primary/30 object-cover" />
          <div>
            <span className="text-[10px] font-bold tracking-widest text-primary">TALLY FLOW</span>
            <p className="text-xs font-semibold text-white">Customer Account Portal</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden text-right sm:block">
            <p className="text-xs font-bold text-white">{user.full_name}</p>
            <p className="text-[11px] text-muted-foreground">{user.email}</p>
          </div>
          <button
            onClick={handleSignOut}
            className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-[#071a2b] px-3.5 py-1.5 text-xs font-semibold text-muted-foreground hover:text-white"
          >
            <LogOut className="h-3.5 w-3.5" /> Sign out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl p-6 md:p-10 space-y-6">
        <div className="rounded-2xl border border-primary/20 bg-linear-to-r from-[#0a2033] to-[#0d2638] p-6 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-[11px] font-bold text-primary">
                {portalCustomer?.customer_tier?.toUpperCase() || "VERIFIED"} ACCOUNT{portalCustomer ? ` · ${portalCustomer.id}` : ""}
              </span>
              <h2 className="mt-2 text-2xl font-bold text-white">Welcome, {user.full_name}</h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Here is your transaction ledger and balance overview. Showing active month by default.
              </p>
            </div>
            <div className="rounded-xl border border-border bg-[#071a2b] p-4 text-right">
              <p className="text-xs text-muted-foreground">Total Account Volume</p>
              <p className="text-2xl font-bold text-emerald-400">{formatCurrency(totalVolume)}</p>
            </div>
          </div>
        </div>

        {/* Month Selector Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          <span className="text-xs font-bold text-muted-foreground">SELECT MONTH:</span>
          {months.map((m) => (
            <button
              key={m}
              onClick={() => setSelectedPeriod(m)}
              className={`rounded-xl px-4 py-1.5 text-xs font-bold transition ${
                selectedPeriod === m
                  ? "bg-primary text-[#071a2b] shadow"
                  : "border border-border bg-[#0a2033] text-muted-foreground hover:text-white"
              }`}
            >
              {new Date(`${m}-01`).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
            </button>
          ))}
        </div>

        <form onSubmit={handleCustomerSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              value={customerSearch}
              onChange={(e) => {
                setCustomerSearch(e.target.value);
                if (!e.target.value.trim()) {
                  setPortalSearchResult(null);
                }
              }}
              placeholder="Search your transactions by ID, invoice, or account..."
              className="w-full rounded-xl border border-border bg-[#0a2033] py-2 pl-9 pr-4 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
            />
          </div>
          <button
            type="submit"
            disabled={customerSearchLoading}
            className="rounded-xl bg-primary px-5 py-2 text-xs font-bold text-[#071a2b] hover:bg-[#4ADE80] disabled:opacity-50"
          >
            {customerSearchLoading ? "Searching..." : "Search"}
          </button>
        </form>

        {portalSearchResult && (
          <div className="divide-y divide-border/40 rounded-xl border border-border bg-[#0a2033] p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 text-xs">
              <p className="text-muted-foreground">
                Found <span className="font-bold text-white">{portalSearchResult.total_matches}</span> transaction{portalSearchResult.total_matches === 1 ? "" : "s"} matching "{portalSearchResult.query}"
              </p>
              <div className="text-right">
                <span className="text-muted-foreground">Account Total: </span>
                <span className="font-bold text-emerald-400">{formatCurrency(portalSearchResult.account_total)}</span>
                {portalSearchResult.matching_amount !== portalSearchResult.account_total && (
                  <span className="text-[11px] text-muted-foreground ml-2">
                    (Matching: {formatCurrency(portalSearchResult.matching_amount)})
                  </span>
                )}
              </div>
            </div>

            {portalSearchResult.results.length === 0 ? (
              <div className="py-4 text-center text-xs text-muted-foreground">
                No transactions found matching your search.
              </div>
            ) : (
              <div className="divide-y divide-border/40 pt-1">
                {portalSearchResult.results.map((tx) => (
                  <div
                    key={tx.id}
                    onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                    className="flex cursor-pointer items-center justify-between py-2.5 transition hover:bg-white/5 px-2 rounded-lg text-xs"
                  >
                    <div>
                      <p className="font-semibold text-white font-mono">{tx.id} · <span className="text-muted-foreground">{tx.invoice_id}</span></p>
                      <p className="text-muted-foreground text-[11px]">
                        {tx.date} · {tx.account}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-white block">{formatCurrency(tx.actual_amount)}</span>
                      <span className={`inline-flex rounded-full border px-2 py-0.5 text-[9px] font-bold ${getStatusBadge(tx.status)}`}>
                        {tx.status.replaceAll("_", " ")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Transactions List */}
        <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
          <div className="flex items-center justify-between border-b border-border bg-[#0d2638] px-6 py-3.5">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Transactions ({portalTxs.length} of {portalTotal} records)
            </span>
            <span className="text-xs text-primary font-medium">Period: {selectedPeriod}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="px-6 py-3 font-semibold">Date</th>
                  <th className="px-6 py-3 font-semibold">Transaction ID</th>
                  <th className="px-6 py-3 font-semibold">Invoice ID</th>
                  <th className="px-6 py-3 font-semibold">Account</th>
                  <th className="px-6 py-3 font-semibold text-right">Amount</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {portalTxs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                      No transactions found for this period.
                    </td>
                  </tr>
                ) : (
                  portalTxs.map((tx) => (
                    <tr
                      key={tx.id}
                      onClick={() => navigate({ to: "/transactions/$transactionId", params: { transactionId: tx.id } })}
                      className="cursor-pointer transition hover:bg-white/5"
                    >
                      <td className="px-6 py-3.5 text-muted-foreground">{tx.date}</td>
                      <td className="px-6 py-3.5 font-mono font-bold text-primary">{tx.id}</td>
                      <td className="px-6 py-3.5 font-mono text-muted-foreground">{tx.invoice_id}</td>
                      <td className="px-6 py-3.5 text-muted-foreground">{tx.account}</td>
                      <td className="px-6 py-3.5 text-right font-bold text-white">{formatCurrency(tx.actual_amount)}</td>
                      <td className="px-6 py-3.5">
                        <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${getStatusBadge(tx.status)}`}>
                          {tx.status.replaceAll("_", " ")}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Show More Button */}
          {portalTxs.length < portalTotal && (
            <div className="border-t border-border p-4 text-center">
              <button
                onClick={() => fetchPortalData(portalOffset + 20, true)}
                disabled={portalLoadingMore}
                className="rounded-xl border border-primary/30 bg-primary/10 px-6 py-2 text-xs font-bold text-primary hover:bg-primary hover:text-[#071a2b] disabled:opacity-50"
              >
                {portalLoadingMore ? "Loading more..." : "Show More Transactions"}
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
