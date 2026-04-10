'use client';

import { useState } from 'react';

interface Deadline {
  id: number;
  client_id: number;
  jurisdiction: string;
  filing_type: string;
  due_date: string;
  frequency: string | null;
  reminder_days_before: number;
}

interface Filing {
  id: number;
  client_id: number;
  jurisdiction: string;
  filing_type: string;
  period_start: string | null;
  period_end: string | null;
  status: string;
  submission_id: string | null;
  submitted_at: string | null;
  created_at: string;
}

const MOCK_DEADLINES: Deadline[] = [
  { id: 1, client_id: 1, jurisdiction: 'NO', filing_type: 'VAT', due_date: '2026-04-15', frequency: 'monthly', reminder_days_before: 7 },
  { id: 2, client_id: 2, jurisdiction: 'ZA', filing_type: 'VAT', due_date: '2026-04-25', frequency: 'monthly', reminder_days_before: 7 },
  { id: 3, client_id: 1, jurisdiction: 'UK', filing_type: 'VAT', due_date: '2026-05-07', frequency: 'quarterly', reminder_days_before: 14 },
  { id: 4, client_id: 3, jurisdiction: 'EU', filing_type: 'VAT', due_date: '2026-06-30', frequency: 'quarterly', reminder_days_before: 14 },
];

const MOCK_FILINGS: Filing[] = [
  { id: 1, client_id: 1, jurisdiction: 'NO', filing_type: 'VAT', period_start: '2026-01-01', period_end: '2026-01-31', status: 'accepted', submission_id: 'SUB-ABC123', submitted_at: '2026-02-10T12:00:00Z', created_at: '2026-02-08T10:00:00Z' },
  { id: 2, client_id: 2, jurisdiction: 'ZA', filing_type: 'VAT', period_start: '2026-01-01', period_end: '2026-02-28', status: 'submitted', submission_id: 'SUB-DEF456', submitted_at: '2026-03-15T09:00:00Z', created_at: '2026-03-14T08:00:00Z' },
  { id: 3, client_id: 1, jurisdiction: 'UK', filing_type: 'VAT', period_start: '2026-01-01', period_end: '2026-03-31', status: 'draft', submission_id: null, submitted_at: null, created_at: '2026-04-01T14:00:00Z' },
  { id: 4, client_id: 3, jurisdiction: 'EU', filing_type: 'PAYROLL', period_start: '2026-03-01', period_end: '2026-03-31', status: 'rejected', submission_id: 'SUB-GHI789', submitted_at: '2026-04-05T11:00:00Z', created_at: '2026-04-04T16:00:00Z' },
];

function getUrgencyColor(dueDate: string): string {
  const today = new Date();
  const due = new Date(dueDate);
  const daysUntil = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (daysUntil < 0) return 'bg-red-100 text-red-800 border-red-300';
  if (daysUntil <= 7) return 'bg-orange-100 text-orange-800 border-orange-300';
  if (daysUntil <= 14) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
  return 'bg-green-100 text-green-800 border-green-300';
}

function getStatusBadge(status: string): string {
  switch (status) {
    case 'draft': return 'bg-gray-100 text-gray-700';
    case 'submitted': return 'bg-blue-100 text-blue-700';
    case 'accepted': return 'bg-green-100 text-green-700';
    case 'rejected': return 'bg-red-100 text-red-700';
    default: return 'bg-gray-100 text-gray-700';
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export default function FilingsPage() {
  const [deadlines] = useState<Deadline[]>(MOCK_DEADLINES);
  const [filings] = useState<Filing[]>(MOCK_FILINGS);

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Statutory Filing Dashboard</h1>

      {/* Upcoming Deadlines */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold mb-4">Upcoming Deadlines</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {deadlines.map((d) => (
            <div
              key={d.id}
              className={`p-4 rounded-lg border ${getUrgencyColor(d.due_date)}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-sm">{d.jurisdiction} {d.filing_type}</span>
                <span className="text-xs uppercase">{d.frequency}</span>
              </div>
              <p className="text-xl font-bold">{formatDate(d.due_date)}</p>
              <p className="text-xs mt-1">Client #{d.client_id}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Filing History */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Filing History</h2>
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors">
              Prepare VAT Filing
            </button>
            <button className="px-4 py-2 bg-white text-gray-700 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
              New Filing
            </button>
          </div>
        </div>
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-gray-600">
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Jurisdiction</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Period</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Submission ID</th>
                <th className="px-4 py-3 font-medium">Submitted</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filings.map((f) => (
                <tr key={f.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">{f.id}</td>
                  <td className="px-4 py-3 font-medium">{f.jurisdiction}</td>
                  <td className="px-4 py-3">{f.filing_type}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {formatDate(f.period_start)} - {formatDate(f.period_end)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(f.status)}`}>
                      {f.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 font-mono text-xs">{f.submission_id || '-'}</td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(f.submitted_at)}</td>
                  <td className="px-4 py-3">
                    {f.status === 'draft' && (
                      <button className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors">
                        Submit
                      </button>
                    )}
                    {f.status === 'rejected' && (
                      <button className="px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 transition-colors">
                        Resubmit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
