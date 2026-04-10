'use client';

import { useEffect, useState } from 'react';
import { clients } from '../lib/api';

interface Client {
  id: number;
  name: string;
  country: string;
  industry: string;
  is_active: boolean;
  health_score: string;
}

interface ClientListData {
  items: Client[];
  total: number;
}

export default function ClientList() {
  const [clientList, setClientList] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadClients();
  }, []);

  async function loadClients() {
    try {
      const data = await clients.list() as ClientListData;
      setClientList(data.items || []);
    } catch (error) {
      console.error('Failed to load clients:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="p-4 text-slate-500">Loading clients...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Clients</h2>
      {clientList.length === 0 ? (
        <p className="text-slate-500">No clients found</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-slate-600">
              <th className="pb-2">Name</th>
              <th className="pb-2">Country</th>
              <th className="pb-2">Industry</th>
              <th className="pb-2">Health</th>
            </tr>
          </thead>
          <tbody>
            {clientList.map((client) => (
              <tr key={client.id} className="border-b last:border-0">
                <td className="py-2 font-medium">{client.name}</td>
                <td className="py-2">{client.country}</td>
                <td className="py-2">{client.industry}</td>
                <td className="py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    client.health_score === 'excellent' ? 'bg-green-100 text-green-800' :
                    client.health_score === 'good' ? 'bg-blue-100 text-blue-800' :
                    client.health_score === 'fair' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {client.health_score}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
