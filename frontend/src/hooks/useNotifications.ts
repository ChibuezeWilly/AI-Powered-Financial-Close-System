/**
 * Polls the /api/v1/notifications endpoint and exposes
 * a reactive notification list with an unread count.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet } from "../lib/api";

export type AppNotification = {
  id: number;
  event: string;
  message: string;
  status: string;
  created_at: string;
};

const POLL_MS = 30_000;

export function useNotifications(enabled: boolean) {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const dismissed = useRef<Set<number>>(new Set());

  const fetch = useCallback(async () => {
    if (!enabled) return;
    try {
      setLoading(true);
      const data = await apiGet<AppNotification[]>("/api/v1/notifications");
      setNotifications(data);
    } catch {
      // Notifications are non-critical; swallow errors silently
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    fetch();
    if (!enabled) return;
    const timer = setInterval(fetch, POLL_MS);
    return () => clearInterval(timer);
  }, [fetch, enabled]);

  const dismiss = useCallback((id: number) => {
    dismissed.current.add(id);
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const unreadCount = notifications.filter(
    (n) => n.status === "PENDING" && !dismissed.current.has(n.id),
  ).length;

  return { notifications, unreadCount, dismiss, loading, refetch: fetch };
}
