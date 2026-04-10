'use client';

import { useEffect, useState } from 'react';
import { fetchAPI } from '../../lib/api';

interface Document {
  id: number;
  file_name: string;
  document_type: string;
  status: string;
  created_at: string;
}

interface Invoice {
  id: number;
  invoice_number: string;
  amount: number;
  currency: string;
  status: string;
  due_date: string;
}

interface PortalStats {
  totalInvoices: number;
  pendingDocuments: number;
}

export default function PortalDashboard() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [stats, setStats] = useState<PortalStats>({ totalInvoices: 0, pendingDocuments: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      const [docsData, invoicesData] = await Promise.all([
        fetchAPI<{ items: Document[]; total: number }>('/documents?per_page=5'),
        fetchAPI<{ items: Invoice[]; total: number }>('/invoices?per_page=5'),
      ]);

      setDocuments(docsData.items || []);
      setInvoices(invoicesData.items || []);
      setStats({
        totalInvoices: invoicesData.total || 0,
        pendingDocuments: docsData.items?.filter((d) => d.status === 'pending').length || 0,
      });
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'extracted': return 'bg-blue-100 text-blue-800';
      case 'posted': return 'bg-green-100 text-green-800';
      case 'paid': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'overdue': return 'bg-red-100 text-red-800';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  if (loading) {
    return <div className="text-slate-500">Loading dashboard...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Welcome to your Portal</h1>
        <p className="text-slate-500 mt-1">View your documents, invoices, and account activity.</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <p className="text-sm text-slate-500">Total Invoices</p>
          <p className="text-3xl font-bold text-slate-900 mt-1">{stats.totalInvoices}</p>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <p className="text-sm text-slate-500">Pending Documents</p>
          <p className="text-3xl font-bold text-slate-900 mt-1">{stats.pendingDocuments}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Recent Documents</h2>
          {documents.length === 0 ? (
            <p className="text-slate-500 text-sm">No documents yet.</p>
          ) : (
            <ul className="space-y-3">
              {documents.map((doc) => (
                <li key={doc.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{doc.file_name}</p>
                    <p className="text-xs text-slate-500">{doc.document_type}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor(doc.status)}`}>
                    {doc.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Recent Invoices */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Recent Invoices</h2>
          {invoices.length === 0 ? (
            <p className="text-slate-500 text-sm">No invoices yet.</p>
          ) : (
            <ul className="space-y-3">
              {invoices.map((inv) => (
                <li key={inv.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{inv.invoice_number}</p>
                    <p className="text-xs text-slate-500">
                      {inv.currency} {Number(inv.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor(inv.status)}`}>
                    {inv.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
