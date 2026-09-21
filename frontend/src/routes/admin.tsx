import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/admin")({ component: AdminAuthPage });

type AdminMode = "login" | "register";

function AdminAuthPage() {
  const [mode, setMode] = useState<AdminMode>("login");
  const [notice, setNotice] = useState("");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice("");
    const form = new FormData(event.currentTarget);
    const payload = {
      portal: "admin",
      email: form.get("email"),
      password: form.get("password"),
      ...(mode === "register"
        ? { full_name: form.get("full_name"), role: form.get("role") }
        : {}),
    };
    const response = await fetch(
      `${import.meta.env["VITE_API_URL"] || "http://localhost:8000"}/api/v1/auth/admin/${mode === "login" ? "login" : "register"}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    const data = await response.json();
    if (!response.ok) {
      setNotice(data.detail || "Unable to complete request.");
      return;
    }
    localStorage.setItem("financial-close-token", data.access_token);
    window.location.href = "/";
  }

  return (
    <main className="grid min-h-screen place-items-center bg-background p-5 text-foreground">
      <form onSubmit={submit} className="w-full max-w-md rounded-xl border border-border bg-card p-7 shadow-2xl shadow-black/20">
        <div className="mb-8 flex items-center gap-3">
          <img src="/logo2.jpg" alt="TallyFlow logo" className="h-12 w-12 rounded-md border border-primary/20 object-cover" />
          <div>
            <p className="text-xs font-bold tracking-[0.16em] text-primary">TALLY FLOW</p>
            <h1 className="font-semibold">Finance admin portal</h1>
          </div>
        </div>
        <h2 className="text-2xl font-semibold">{mode === "login" ? "Admin sign in" : "Create admin account"}</h2>
        <p className="mt-2 text-sm text-muted-foreground">Finance operations, approvals, investigations, and close controls.</p>
        <div className="mt-6 space-y-4">
          {mode === "register" && (
            <>
              <label className="block text-sm">Full name<input required name="full_name" className="mt-1.5 w-full rounded-md border border-border bg-[#071a2b] px-3 py-2.5 outline-none focus:border-primary" /></label>
              <label className="block text-sm">Admin role<select name="role" defaultValue="ANALYST" className="mt-1.5 w-full rounded-md border border-border bg-[#071a2b] px-3 py-2.5 outline-none focus:border-primary"><option value="ANALYST">Analyst</option><option value="FINANCE_MANAGER">Finance manager</option><option value="FINANCE_ADMIN">Finance admin</option><option value="ADMIN">Administrator</option></select></label>
            </>
          )}
          <label className="block text-sm">Work email<input required type="email" name="email" className="mt-1.5 w-full rounded-md border border-border bg-[#071a2b] px-3 py-2.5 outline-none focus:border-primary" /></label>
          <label className="block text-sm">Password<input required minLength={12} type="password" name="password" className="mt-1.5 w-full rounded-md border border-border bg-[#071a2b] px-3 py-2.5 outline-none focus:border-primary" /></label>
        </div>
        {notice && <p className="mt-4 text-sm text-red-300">{notice}</p>}
        <button className="mt-6 w-full rounded-md bg-primary px-4 py-2.5 text-sm font-bold text-[#071a2b] hover:bg-[#4ADE80]">{mode === "login" ? "Sign in" : "Create admin account"}</button>
        <p className="mt-5 text-center text-sm text-muted-foreground">
          {mode === "login" ? "Need an admin account?" : "Already have an admin account?"}{" "}
          <button type="button" className="font-medium text-primary" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "Register" : "Sign in"}</button>
        </p>
      </form>
    </main>
  );
}