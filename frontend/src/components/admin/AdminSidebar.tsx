import { Link } from "@tanstack/react-router";
import { X, LogOut } from "lucide-react";
import { apiPost, clearToken } from "../../lib/api";

export const navigationItems = [
  { label: "Overview", path: "/" },
  { label: "Financial Close", path: "/financial-close" },
  { label: "Reconciliation", path: "/reconciliation" },
  { label: "Transactions", path: "/transactions" },
  { label: "Discrepancies", path: "/discrepancies" },
  { label: "Investigations", path: "/investigations" },
  { label: "Approvals", path: "/approvals" },
  { label: "Documents", path: "/documents" },
  { label: "Reconciled", path: "/reconciled" },
  { label: "User Accounts", path: "/accounts" },
];

interface AdminSidebarProps {
  currentPath?: string;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

export function AdminSidebar({
  currentPath = "/",
  mobileOpen,
  setMobileOpen,
}: AdminSidebarProps) {
  const handleSignOut = async () => {
    try {
      await apiPost("/api/v1/auth/logout");
    } catch {
      // Clear the local session even when the backend logout request fails.
    } finally {
      clearToken();
      window.location.assign("/");
    }
  };

  return (
    <>
      {/* Mobile Sidebar */}
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 z-50 bg-black/70 md:hidden"
        />
      )}
      <aside
        aria-label="Mobile navigation"
        style={{ scrollbarWidth: "none" }}
        className={`fixed inset-y-0 right-0 z-60 w-64 border-l border-border bg-[#0a2033] p-5 shadow-2xl transition-transform duration-200 scrollbar-none lg:hidden overflow-y-auto ${
          mobileOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img
              src="/logo2.jpg"
              alt="Logo"
              className="h-8 w-8 rounded-lg border border-primary/30 object-cover"
            />
            <span className="text-xs font-bold tracking-widest text-primary">
              TALLY FLOW
            </span>
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            className="rounded p-1 text-muted-foreground hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav
          style={{ scrollbarWidth: "none" }}
          className="space-y-1 overflow-y-auto scrollbar-none text-sm"
        >
          {navigationItems.map((item) => {
            const isActive =
              currentPath === item.path ||
              (item.path !== "/" && currentPath.startsWith(item.path));
            return (
              <Link
                key={item.label}
                to={item.path === "/" ? "/" : "/$section"}
                {...(item.path === "/"
                  ? {}
                  : { params: { section: item.path.slice(1) } })}
                onClick={() => setMobileOpen(false)}
                className={`block rounded-lg px-3 py-2.5 font-medium transition ${
                  isActive
                    ? "bg-primary/20 text-primary border border-primary/30"
                    : "text-muted-foreground hover:bg-white/5 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button
          onClick={handleSignOut}
          className="inline-flex sm:hidden justify-center items-center w-full gap-1 rounded-md border border-border bg-primary/10 px-3.5 py-2 text-xs font-semibold text-primary text-center"
        >
          <LogOut className="h-3.5 w-3.5 text-center" /> Sign out
        </button>
      </aside>

      {/* Desktop Sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-[#0a2033] p-5 lg:block">
        <div className="mb-8 flex items-center gap-3">
          <img
            src="/logo2.jpg"
            alt="Logo"
            className="h-9 w-9 rounded-lg border border-primary/30 object-cover shadow"
          />
          <div>
            <p className="text-[10px] font-bold tracking-[0.2em] text-primary">
              TALLY FLOW
            </p>
            <p className="text-xs font-medium text-muted-foreground">
              Close Platform
            </p>
          </div>
        </div>
        <nav className="space-y-1 text-sm font-medium">
          {navigationItems.map((item) => {
            const isActive =
              currentPath === item.path ||
              (item.path !== "/" && currentPath.startsWith(item.path));
            return (
              <Link
                key={item.label}
                to={item.path === "/" ? "/" : "/$section"}
                {...(item.path === "/"
                  ? {}
                  : { params: { section: item.path.slice(1) } })}
                className={`block rounded-lg px-3 py-2.5 transition ${
                  isActive
                    ? "bg-primary/20 text-primary border border-primary/30 shadow-sm"
                    : "text-muted-foreground hover:bg-white/5 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
