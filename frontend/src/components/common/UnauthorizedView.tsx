import { Link } from "@tanstack/react-router";
import { ArrowLeft, ShieldAlert } from "lucide-react";

interface UnauthorizedViewProps {
  userRole?: string;
}

export function UnauthorizedView({ userRole }: UnauthorizedViewProps) {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-4 text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl border border-red-500/30 bg-red-500/10 text-red-400 shadow-xl shadow-red-500/10">
        <ShieldAlert className="h-10 w-10" />
      </div>

      <div className="inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-red-400">
        Access Denied (403)
      </div>

      <h1 className="mt-4 text-2xl font-bold tracking-tight text-white sm:text-3xl">
        Unauthorized to View Page
      </h1>

      <p className="mt-3 max-w-md text-sm text-slate-400">
        You do not have administrative privileges to access this area. This section is restricted to authorized financial close staff and administrators.
        {userRole && (
          <span className="mt-1 block text-xs text-slate-500">
            Current role: <span className="font-mono text-slate-300">{userRole}</span>
          </span>
        )}
      </p>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-[#071a2b] shadow-lg shadow-primary/20 transition-all hover:bg-[#4ADE80] hover:shadow-primary/30"
        >
          <ArrowLeft className="h-4 w-4" /> Return to Customer Portal
        </Link>
      </div>
    </div>
  );
}
