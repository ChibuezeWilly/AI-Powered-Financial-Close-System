import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { apiGet, apiPost } from "../lib/api";
import { useNotifications } from "../hooks/useNotifications";
import { AuthModal, Account } from "../components/auth/AuthModal";
import {
  CustomerPortalView,
  CustomerAccountData,
  PortalSearchResult,
  TransactionRecord,
} from "../components/portal/CustomerPortalView";
import {
  AdminOverviewView,
  InsightResponse,
  KPIResponse,
  SearchResultItem,
} from "../components/admin/AdminOverviewView";

export const Route = createFileRoute("/")({ component: Index });

const months = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09"];

function Index() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<Account | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // App State
  const [selectedPeriod, setSelectedPeriod] = useState<string>("2026-09");
  const [kpis, setKpis] = useState<KPIResponse | null>(null);
  const [insights, setInsights] = useState<InsightResponse | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Unified 3-Source Search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [excludedSources, setExcludedSources] = useState<string[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Customer Portal State
  const [portalTxs, setPortalTxs] = useState<TransactionRecord[]>([]);
  const [portalTotal, setPortalTotal] = useState(0);
  const [portalOffset, setPortalOffset] = useState(0);
  const [portalLoadingMore, setPortalLoadingMore] = useState(false);
  const [customerSearch, setCustomerSearch] = useState("");
  const [portalCustomer, setPortalCustomer] = useState<CustomerAccountData | null>(null);
  const [portalSearchResult, setPortalSearchResult] = useState<PortalSearchResult | null>(null);
  const [customerSearchLoading, setCustomerSearchLoading] = useState(false);

  const { notifications, unreadCount, dismiss } = useNotifications(!!token);

  // Authenticate without flash
  useEffect(() => {
    const saved = localStorage.getItem("financial-close-token");
    if (!saved) {
      setIsCheckingAuth(false);
      return;
    }
    fetch(`${import.meta.env["VITE_API_URL"] || "http://localhost:8000"}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${saved}` },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((userData) => {
        setToken(saved);
        setUser(userData);
      })
      .catch(() => {
        localStorage.removeItem("financial-close-token");
        setToken(null);
        setUser(null);
      })
      .finally(() => setIsCheckingAuth(false));
  }, []);

  // Fetch admin dashboard data
  const fetchAdminData = useCallback(async () => {
    if (!token || user?.role === "REGULAR_USER") return;
    try {
      const [kpiData, txData] = await Promise.all([
        apiGet<KPIResponse>("/api/v1/workspace/kpis"),
        apiGet<TransactionRecord[]>(`/api/v1/transactions?period=${selectedPeriod}`),
      ]);
      setKpis(kpiData);
      setTransactions(txData);
    } catch (err) {
      console.error("Dashboard data load failed", err);
    }
  }, [token, user, selectedPeriod]);

  // Fetch AI insights
  const fetchInsights = useCallback(async () => {
    if (!token || user?.role === "REGULAR_USER") return;
    setInsightsLoading(true);
    try {
      const data = await apiGet<InsightResponse>(`/api/v1/workspace/insights?period=${selectedPeriod}`);
      setInsights(data);
    } catch (err) {
      console.error("Insights load failed", err);
    } finally {
      setInsightsLoading(false);
    }
  }, [token, user, selectedPeriod]);

  // Fetch customer account
  const fetchCustomerAccount = useCallback(async () => {
    if (!token || user?.role !== "REGULAR_USER") return;
    try {
      const data = await apiGet<CustomerAccountData>("/api/v1/portal/customer-account");
      setPortalCustomer(data);
    } catch (err) {
      console.error("Customer account load failed", err);
    }
  }, [token, user]);

  // Fetch customer portal transactions
  const fetchPortalData = useCallback(
    async (offset = 0, append = false) => {
      if (!token || user?.role !== "REGULAR_USER") return;
      if (append) setPortalLoadingMore(true);
      try {
        const data = await apiGet<{
          transactions: TransactionRecord[];
          total: number;
          offset: number;
          has_more: boolean;
        }>(`/api/v1/portal/transactions?period=${selectedPeriod}&limit=20&offset=${offset}`);
        if (append) {
          setPortalTxs((prev) => [...prev, ...data.transactions]);
        } else {
          setPortalTxs(data.transactions);
        }
        setPortalTotal(data.total);
        setPortalOffset(offset);
      } catch (err) {
        console.error("Portal transactions load failed", err);
      } finally {
        setPortalLoadingMore(false);
      }
    },
    [token, user, selectedPeriod]
  );

  useEffect(() => {
    if (user?.role === "REGULAR_USER") {
      fetchCustomerAccount();
      fetchPortalData(0, false);
    } else if (user) {
      fetchAdminData();
      fetchInsights();
    }
  }, [user, selectedPeriod, fetchAdminData, fetchInsights, fetchPortalData, fetchCustomerAccount]);

  // 3-Source Search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      const query = new URLSearchParams({ q: searchQuery.trim() });
      excludedSources.forEach((s) => query.append("exclude", s));
      const res = await apiGet<{ results: SearchResultItem[] }>(`/api/v1/workspace/search?${query}`);
      setSearchResults(res.results || []);
    } catch (err) {
      toast.error("Search failed");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleCustomerSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerSearch.trim()) {
      setPortalSearchResult(null);
      return;
    }
    setCustomerSearchLoading(true);
    try {
      const data = await apiGet<PortalSearchResult>(
        `/api/v1/portal/transactions/search?q=${encodeURIComponent(customerSearch.trim())}`
      );
      setPortalSearchResult(data);
    } catch (err) {
      toast.error("Transaction search failed");
    } finally {
      setCustomerSearchLoading(false);
    }
  };

  const toggleSourceExclusion = (source: string) => {
    setExcludedSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    );
  };

  // Sign out
  const handleSignOut = async () => {
    if (token) {
      try {
        await apiPost("/api/v1/auth/logout");
      } catch (e) {}
    }
    localStorage.removeItem("financial-close-token");
    setToken(null);
    setUser(null);
    toast.success("Signed out");
  };

  if (isCheckingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#071A2B]">
        <div className="flex flex-col items-center gap-3">
          <img src="/logo2.jpg" alt="TallyFlow" className="h-12 w-12 rounded-xl border border-primary/30 object-cover shadow-lg animate-pulse" />
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-xs font-bold tracking-widest text-primary">INITIALIZING TALLYFLOW...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <AuthModal
        onSuccess={(newToken, newUser) => {
          setToken(newToken);
          setUser(newUser);
        }}
      />
    );
  }

  if (user.role === "REGULAR_USER") {
    return (
      <CustomerPortalView
        user={user}
        portalCustomer={portalCustomer}
        portalTxs={portalTxs}
        portalTotal={portalTotal}
        selectedPeriod={selectedPeriod}
        setSelectedPeriod={setSelectedPeriod}
        months={months}
        customerSearch={customerSearch}
        setCustomerSearch={setCustomerSearch}
        handleCustomerSearch={handleCustomerSearch}
        customerSearchLoading={customerSearchLoading}
        portalSearchResult={portalSearchResult}
        setPortalSearchResult={setPortalSearchResult}
        portalOffset={portalOffset}
        portalLoadingMore={portalLoadingMore}
        fetchPortalData={fetchPortalData}
        handleSignOut={handleSignOut}
      />
    );
  }

  return (
    <AdminOverviewView
      user={user}
      kpis={kpis}
      insights={insights}
      insightsLoading={insightsLoading}
      fetchInsights={fetchInsights}
      transactions={transactions}
      selectedPeriod={selectedPeriod}
      setSelectedPeriod={setSelectedPeriod}
      months={months}
      searchQuery={searchQuery}
      setSearchQuery={setSearchQuery}
      handleSearch={handleSearch}
      searchLoading={searchLoading}
      searchResults={searchResults}
      excludedSources={excludedSources}
      toggleSourceExclusion={toggleSourceExclusion}
      notifications={notifications}
      unreadCount={unreadCount}
      dismiss={dismiss}
      showNotifications={showNotifications}
      setShowNotifications={setShowNotifications}
      mobileSidebarOpen={mobileSidebarOpen}
      setMobileSidebarOpen={setMobileSidebarOpen}
      handleSignOut={handleSignOut}
    />
  );
}