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
  notFoundComponent: NotFoundComponent,
});

function NotFoundComponent() {
  return (
    <main className="grid min-h-screen place-items-center bg-background px-5 text-center text-foreground">
      <div>
        <p className="text-xs font-bold tracking-[0.18em] text-primary">TALLY FLOW</p>
        <h1 className="mt-3 text-3xl font-semibold">Page not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you requested does not exist.
        </p>
        <a
          href="/"
          className="mt-6 inline-flex rounded-md bg-primary px-4 py-2.5 text-sm font-bold text-[#071a2b] hover:bg-[#4ADE80]"
        >
          Return home
        </a>
      </div>
    </main>
  );
}

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
