'use client';

import { useEffect, useState } from 'react';

interface MessageStats {
  total: number;
  pending: number;
  processing: number;
  delivered: number;
  failed: number;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  delivered: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

export default function WhatsAppDashboard() {
  const [stats, setStats] = useState<MessageStats>({
    total: 0,
    pending: 0,
    processing: 0,
    delivered: 0,
    failed: 0,
  });
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMessages() {
      try {
        const res = await fetch('/api/whatsapp/messages', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
          },
        });

        if (res.ok) {
          const data = await res.json();
          setMessages(data.items || []);

          const items = data.items || [];
          setStats({
            total: data.total || items.length,
            pending: items.filter((m: any) => m.status === 'pending').length,
            processing: items.filter((m: any) => m.status === 'processing').length,
            delivered: items.filter((m: any) => m.status === 'delivered').length,
            failed: items.filter((m: any) => m.status === 'failed').length,
          });
        }
      } catch (err) {
        console.error('Failed to fetch WhatsApp messages:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchMessages();
  }, []);

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">WhatsApp Integration</h1>

      {/* Status cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {[
          { label: 'Total Messages', value: stats.total, color: 'bg-slate-100 text-slate-800' },
          { label: 'Pending', value: stats.pending, color: STATUS_COLORS.pending },
          { label: 'Processing', value: stats.processing, color: STATUS_COLORS.processing },
          { label: 'Delivered', value: stats.delivered, color: STATUS_COLORS.delivered },
          { label: 'Failed', value: stats.failed, color: STATUS_COLORS.failed },
        ].map((card) => (
          <div
            key={card.label}
            className={`rounded-lg p-4 ${card.color}`}
          >
            <p className="text-sm font-medium">{card.label}</p>
            <p className="text-2xl font-bold">{card.value}</p>
          </div>
        ))}
      </div>

      {/* Messages table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold">Recent Messages</h2>
        </div>

        {loading ? (
          <div className="p-6 text-center text-slate-500">Loading messages...</div>
        ) : messages.length === 0 ? (
          <div className="p-6 text-center text-slate-500">No WhatsApp messages yet.</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-6 py-3">ID</th>
                <th className="px-6 py-3">Phone</th>
                <th className="px-6 py-3">Direction</th>
                <th className="px-6 py-3">Content</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {messages.map((msg: any) => (
                <tr key={msg.id} className="hover:bg-slate-50">
                  <td className="px-6 py-3">{msg.id}</td>
                  <td className="px-6 py-3 font-mono text-xs">{msg.phone_number}</td>
                  <td className="px-6 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        msg.direction === 'inbound'
                          ? 'bg-indigo-100 text-indigo-700'
                          : 'bg-emerald-100 text-emerald-700'
                      }`}
                    >
                      {msg.direction}
                    </span>
                  </td>
                  <td className="px-6 py-3 max-w-xs truncate">{msg.content}</td>
                  <td className="px-6 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        STATUS_COLORS[msg.status] || 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {msg.status}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-xs text-slate-500">
                    {new Date(msg.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
