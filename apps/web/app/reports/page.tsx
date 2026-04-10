'use client';

import Link from 'next/link';

const reports = [
  {
    title: 'Profit & Loss',
    description: 'Revenue vs expenses for a given period',
    href: '/reports/profit-loss',
  },
  {
    title: 'Balance Sheet',
    description: 'Assets, liabilities, and equity as at a specific date',
    href: '/reports/balance-sheet',
  },
  {
    title: 'Trial Balance',
    description: 'All accounts with debit and credit totals',
    href: '/reports/trial-balance',
  },
  {
    title: 'Aged Debtors',
    description: 'Outstanding invoices grouped by 30/60/90/90+ days',
    href: '/reports/aged-debtors',
  },
];

export default function ReportsPage() {
  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Financial Reports</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reports.map((report) => (
          <Link
            key={report.href}
            href={report.href}
            className="block p-6 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <h2 className="text-lg font-semibold mb-2">{report.title}</h2>
            <p className="text-gray-500 text-sm">{report.description}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
