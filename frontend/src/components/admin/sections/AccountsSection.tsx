import { CheckCircle2, Search } from "lucide-react";
import { AccountRecord, formatCurrency } from "./types";

interface AccountsSectionProps {
  accounts: AccountRecord[];
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  viewAccountTransactions: (accountId: string) => void;
}

export function AccountsSection({
  accounts,
  searchQuery,
  setSearchQuery,
  viewAccountTransactions,
}: AccountsSectionProps) {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">General Ledger Accounts</h2>
          <p className="text-xs text-muted-foreground">
            Inspect chart of accounts, balances, account types, and assigned transaction volume.
          </p>
        </div>
        <div className="relative min-w-[260px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search accounts by code, name, type..."
            className="w-full rounded-xl border border-border bg-[#0a2033] py-2 pl-9 pr-4 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-border bg-[#0a2033]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border/60 text-muted-foreground">
                <th className="px-5 py-3 font-semibold">Account Code</th>
                <th className="px-5 py-3 font-semibold">Account Name</th>
                <th className="px-5 py-3 font-semibold">Account Type</th>
                <th className="px-5 py-3 font-semibold">Normal Balance</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold text-right">Transactions</th>
                <th className="px-5 py-3 font-semibold text-right">Total Balance</th>
                <th className="px-5 py-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {accounts.map((acct) => (
                <tr key={acct.id} className="transition hover:bg-white/5">
                  <td className="px-5 py-3.5 font-mono text-muted-foreground">{acct.code}</td>
                  <td className="px-5 py-3.5 font-bold text-white">{acct.name}</td>
                  <td className="px-5 py-3.5 text-muted-foreground">{acct.account_type}</td>
                  <td className="px-5 py-3.5">
                    <span
                      className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${
                        acct.account_type === "Asset"
                          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                          : acct.account_type === "Liability"
                          ? "border-rose-500/40 bg-rose-500/10 text-rose-300"
                          : acct.account_type === "Revenue"
                          ? "border-sky-500/40 bg-sky-500/10 text-sky-300"
                          : "border-yellow-500/40 bg-yellow-500/10 text-yellow-300"
                      }`}
                    >
                      {acct.normal_balance?.toUpperCase() || acct.account_type}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="inline-flex items-center gap-1 text-emerald-400">
                      <CheckCircle2 className="h-3 w-3" /> {acct.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-right font-medium text-white">{acct.transaction_count}</td>
                  <td className="px-5 py-3.5 text-right font-bold text-emerald-400">
                    {formatCurrency(acct.total_balance)}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      onClick={() => viewAccountTransactions(acct.id)}
                      className="inline-flex rounded-lg border border-primary/30 bg-primary/10 px-3 py-1 font-semibold text-primary hover:bg-primary hover:text-[#071a2b]"
                    >
                      View Records
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
