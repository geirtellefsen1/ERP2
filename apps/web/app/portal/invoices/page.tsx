'use client';

import { useEffect, useState } from 'react';
import { fetchAPI } from '../../../lib/api';

interface Invoice {
  id: number;
  invoice_number: string;
  amount: number;
  currency: string;
  status: string;
  due_date: string;
  issued_at: string;
}

const STATUS_OPTIONS = ['all', 'draft', 'sent', 'paid', 'overdue'];

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadInvoices();
  }, [statusFilter]);

  async function loadInvoices() {
    setLoading(true);
    try {
      const params = statusFilter !== 'all' ? `&status=${statusFilter}` : '';
      const data = await fetchAPI<{ items: Invoice[]; total: number }>(
        `/invoices?per_page=50${params}`
      );
      setInvoices(data.items || []);
    } catch (error) {
      console.error('Failed to load invoices:', error);
    } finally {
      setLoading(false);
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-slate-100 text-slate-700';
      case 'sent': return 'bg-blue-100 text-blue-800';
      case 'paid': return 'bg-green-100 text-green-800';
      case 'overdue': return 'bg-red-100 text-red-800';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Invoices</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt.charAt(0).toUpperCase() + opt.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200">
        {loading ? (
          <div className="p-6 text-slate-500 text-center">Loading invoices...</div>
        ) : invoices.length === 0 ? (
          <div className="p-6 text-slate-500 text-center">No invoices found.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-slate-600">
                <th className="px-4 py-3">Invoice #</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Currency</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Due Date</th>
                <th className="px-4 py-3">Issued</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-b last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">{inv.invoice_number}</td>
                  <td className="px-4 py-3 text-slate-700 tabular-nums">
                    {Number(inv.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{inv.currency}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor(inv.status)}`}>
                      {inv.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {inv.due_date ? new Date(inv.due_date).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {inv.issued_at ? new Date(inv.issued_at).toLocaleDateString() : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
