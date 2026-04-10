'use client';

import { useEffect, useState } from 'react';

interface JournalEntry {
  id: number;
  entry_number: string;
  entry_date: string;
  description: string;
  debit_total: number;
  credit_total: number;
  status: string;
  is_balanced: boolean;
}

export default function JournalsPage() {
  const [journals, setJournals] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchJournals = async () => {
      try {
        const res = await fetch('/api/journals?client_id=1');
        if (!res.ok) throw new Error('Failed to fetch journals');
        const data = await res.json();
        setJournals(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchJournals();
  }, []);

  if (loading) return <main className="p-8 max-w-7xl mx-auto"><p>Loading journals...</p></main>;
  if (error) return <main className="p-8 max-w-7xl mx-auto"><p className="text-red-500">Error: {error}</p></main>;

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Journal Entries</h1>
      {journals.length === 0 ? (
        <p className="text-gray-500">No journal entries found.</p>
      ) : (
        <table className="min-w-full border border-gray-200 rounded-lg overflow-hidden">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Entry #</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Date</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Description</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Debit</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Credit</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {journals.map((entry) => (
              <tr key={entry.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono">{entry.entry_number}</td>
                <td className="px-4 py-3 text-sm">{new Date(entry.entry_date).toLocaleDateString()}</td>
                <td className="px-4 py-3 text-sm">{entry.description}</td>
                <td className="px-4 py-3 text-sm text-right">{entry.debit_total.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-right">{entry.credit_total.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    entry.status === 'posted' ? 'bg-green-100 text-green-700' :
                    entry.status === 'balanced' ? 'bg-blue-100 text-blue-700' :
                    entry.status === 'reversed' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {entry.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
