import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRootRoute, HeadContent, Outlet, Scripts } from "@tanstack/react-router";
import { Toaster } from "sonner";

import "../styles.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export const Route = createRootRoute({
  head: () => ({
    links: [
      { rel: "icon", type: "image/jpeg", href: "/logo2.jpg" },
    ],
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "TallyFlow — Financial Close & Reconciliation" },
      {
        name: "description",
        content: "Evidence-led financial reconciliation and investigation workspace.",
      },
    ],
  }),
  component: RootComponent,
});

function RootComponent() {
  return (
    <>
      <HeadContent />
      <QueryClientProvider client={queryClient}>
        <Outlet />
      </QueryClientProvider>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#0d2638",
            border: "1px solid #1B3A4D",
            color: "#F5F7FA",
          },
        }}
        richColors
        closeButton
      />
      <Scripts />
    </>
  );
}
