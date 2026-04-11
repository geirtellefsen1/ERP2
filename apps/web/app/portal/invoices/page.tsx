"use client";
import { useEffect, useState } from "react";

interface Invoice {
  id: number;
  invoice_number: string;
  amount: string;
  currency: string;
  status: string;
  due_date: string;
  issued_at: string;
}

export default function PortalInvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    setLoading(false);
  }, []);

  const filtered = filter === "all" ? invoices : invoices.filter((i) => i.status === filter);

  const statusColor = (s: string) => {
    if (s === "paid") return "bg-green-100 text-green-700";
    if (s === "overdue") return "bg-red-100 text-red-700";
    if (s === "sent") return "bg-blue-100 text-blue-700";
    return "bg-slate-100 text-slate-600";
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Invoices</h1>
          <p className="text-slate-500 mt-1">Your billing history</p>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
        >
          <option value="all">All</option>
          <option value="sent">Sent</option>
          <option value="paid">Paid</option>
          <option value="overdue">Overdue</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            No invoices found. Contact your BPO agent for billing enquiries.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                {["Invoice #", "Amount", "Status", "Due Date", "Issued"].map((h) => (
                  <th key={h} className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((inv) => (
                <tr key={inv.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-mono text-sm font-medium text-slate-800">{inv.invoice_number}</td>
                  <td className="px-6 py-4 font-semibold text-slate-800">{inv.currency} {inv.amount}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${statusColor(inv.status)}`}>
                      {inv.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-600 text-sm">{inv.due_date ? new Date(inv.due_date).toLocaleDateString() : "—"}</td>
                  <td className="px-6 py-4 text-slate-600 text-sm">{new Date(inv.issued_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
