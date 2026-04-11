"use client";
import { useState } from "react";

export default function PortalLoginPage() {
  const [email, setEmail] = useState("");
  const [clientCode, setClientCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    // In production: POST to /api/v1/auth/client-login
    // For now: simulate login
    await new Promise((r) => setTimeout(r, 1000));
    if (!email.includes("@")) {
      setError("Please enter a valid email");
      setLoading(false);
      return;
    }
    localStorage.setItem("bpo_client_token", "demo-token");
    localStorage.setItem(
      "bpo_client_user",
      JSON.stringify({ email, clientId: "1", clientName: clientCode || "Your Company" })
    );
    window.location.href = "/portal/1";
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
      <div className="bg-white shadow-lg rounded-2xl p-8 w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="text-3xl font-bold text-slate-900 mb-1">Client Portal</div>
          <p className="text-slate-500 text-sm">Sign in with your client credentials</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Client Code</label>
            <input
              value={clientCode}
              onChange={(e) => setClientCode(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="e.g. ACME-001"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="you@yourcompany.com"
              required
            />
          </div>
          {error && (
            <div className="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-2">{error}</div>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white font-semibold py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </main>
  );
}
