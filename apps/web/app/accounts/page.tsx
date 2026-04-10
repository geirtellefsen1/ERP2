'use client';

import { useEffect, useState } from 'react';
import { fetchAPI } from '../../lib/api';

interface Account {
  id: number;
  account_number: string;
  name: string;
  account_type: string;
  balance: number;
  is_active: string;
  children?: Account[];
}

function AccountRow({ account, depth = 0 }: { account: Account; depth?: number }) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = account.children && account.children.length > 0;

  const typeColor: Record<string, string> = {
    asset: 'text-blue-600',
    liability: 'text-red-600',
    equity: 'text-purple-600',
    revenue: 'text-green-600',
    expense: 'text-orange-600',
  };

  return (
    <>
      <tr className="border-b hover:bg-slate-50">
        <td className="py-2 pr-4" style={{ paddingLeft: `${depth * 24 + 8}px` }}>
          {hasChildren && (
            <button onClick={() => setExpanded(!expanded)} className="mr-1 text-slate-400">
              {expanded ? '\u25BC' : '\u25B6'}
            </button>
          )}
          <span className="font-mono text-sm text-slate-500">{account.account_number}</span>
        </td>
        <td className="py-2">{account.name}</td>
        <td className={`py-2 capitalize ${typeColor[account.account_type] || ''}`}>
          {account.account_type}
        </td>
        <td className="py-2 text-right font-mono">
          {account.balance.toLocaleString('en', { minimumFractionDigits: 2 })}
        </td>
      </tr>
      {expanded && hasChildren && account.children!.map((child) => (
        <AccountRow key={child.id} account={child} depth={depth + 1} />
      ))}
    </>
  );
}

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In production, client_id would come from route params or context
    fetchAPI<Account[]>('/accounts/client/1/hierarchy')
      .then(setAccounts)
      .catch(() => setAccounts([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-slate-500">Loading accounts...</div>;

  return (
    <main className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Chart of Accounts</h1>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-left text-slate-600">
              <th className="p-3">Code</th>
              <th className="p-3">Name</th>
              <th className="p-3">Type</th>
              <th className="p-3 text-right">Balance</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((account) => (
              <AccountRow key={account.id} account={account} />
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
