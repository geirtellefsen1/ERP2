'use client';

import { useState } from 'react';

interface ForecastLine {
  week_commencing: string;
  opening_balance: number;
  receipts: number;
  payments: number;
  closing_balance: number;
  alert_flag: boolean;
}

interface ForecastAlert {
  id: number;
  alert_type: string;
  severity: string;
  week_number: number;
  narrative: string;
  created_at: string;
}

interface ForecastResult {
  forecast: {
    id: number;
    client_id: number;
    forecast_date: string;
    end_date: string;
    status: string;
    created_at: string;
  };
  lines: ForecastLine[];
  alerts: ForecastAlert[];
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-ZA', {
    style: 'currency',
    currency: 'ZAR',
    minimumFractionDigits: 2,
  }).format(value);
}

export default function CashflowPage() {
  const [openingBalance, setOpeningBalance] = useState('');
  const [avgReceipts, setAvgReceipts] = useState('');
  const [avgPayments, setAvgPayments] = useState('');
  const [clientId, setClientId] = useState('1');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token') || '';

      const response = await fetch(`${apiUrl}/cashflow/forecasts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          client_id: parseInt(clientId),
          opening_balance: parseFloat(openingBalance),
          avg_weekly_receipts: parseFloat(avgReceipts),
          avg_weekly_payments: parseFloat(avgPayments),
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate forecast: ${response.statusText}`);
      }

      const data: ForecastResult = await response.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const criticalAlerts = result?.alerts.filter((a) => a.severity === 'critical') || [];
  const warningAlerts = result?.alerts.filter((a) => a.severity === 'warning') || [];
  const infoAlerts = result?.alerts.filter((a) => a.severity === 'info') || [];

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Cashflow Forecaster</h1>
      <p className="text-gray-500 mb-8">
        Generate a 13-week rolling cashflow forecast to identify potential shortfalls.
      </p>

      {/* Forecast Generation Form */}
      <form
        onSubmit={handleGenerate}
        className="bg-white border border-gray-200 rounded-lg p-6 mb-8"
      >
        <h2 className="text-lg font-semibold mb-4">Generate Forecast</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client ID
            </label>
            <input
              type="number"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              required
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Opening Balance
            </label>
            <input
              type="number"
              value={openingBalance}
              onChange={(e) => setOpeningBalance(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              placeholder="e.g. 100000"
              required
              step="0.01"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Avg Weekly Receipts
            </label>
            <input
              type="number"
              value={avgReceipts}
              onChange={(e) => setAvgReceipts(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              placeholder="e.g. 50000"
              required
              step="0.01"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Avg Weekly Payments
            </label>
            <input
              type="number"
              value={avgPayments}
              onChange={(e) => setAvgPayments(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              placeholder="e.g. 40000"
              required
              step="0.01"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
        >
          {loading ? 'Generating...' : 'Generate 13-Week Forecast'}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Alert Banners */}
      {criticalAlerts.length > 0 && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded-r-lg">
          <h3 className="font-semibold text-red-800 mb-2">Critical Alerts</h3>
          {criticalAlerts.map((alert, i) => (
            <p key={i} className="text-red-700 text-sm mb-1">
              {alert.narrative}
            </p>
          ))}
        </div>
      )}

      {warningAlerts.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-4 rounded-r-lg">
          <h3 className="font-semibold text-yellow-800 mb-2">Warning Alerts</h3>
          {warningAlerts.map((alert, i) => (
            <p key={i} className="text-yellow-700 text-sm mb-1">
              {alert.narrative}
            </p>
          ))}
        </div>
      )}

      {infoAlerts.length > 0 && (
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4 rounded-r-lg">
          <h3 className="font-semibold text-blue-800 mb-2">Info Alerts</h3>
          {infoAlerts.map((alert, i) => (
            <p key={i} className="text-blue-700 text-sm mb-1">
              {alert.narrative}
            </p>
          ))}
        </div>
      )}

      {/* 13-Week Forecast Table */}
      {result && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              13-Week Forecast
            </h2>
            <span
              className={`text-xs font-medium px-2 py-1 rounded ${
                result.forecast.status === 'published'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              {result.forecast.status.toUpperCase()}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Week</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Week Commencing</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Opening Balance</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Receipts</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Payments</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Closing Balance</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-600">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {result.lines.map((line, index) => (
                  <tr
                    key={index}
                    className={
                      line.alert_flag
                        ? 'bg-red-50'
                        : index % 2 === 0
                        ? 'bg-white'
                        : 'bg-gray-50'
                    }
                  >
                    <td className="px-4 py-3 text-gray-900">{index + 1}</td>
                    <td className="px-4 py-3 text-gray-900">{line.week_commencing}</td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      {formatCurrency(line.opening_balance)}
                    </td>
                    <td className="px-4 py-3 text-right text-green-700">
                      {formatCurrency(line.receipts)}
                    </td>
                    <td className="px-4 py-3 text-right text-red-700">
                      {formatCurrency(line.payments)}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-medium ${
                        line.closing_balance < 0 ? 'text-red-700' : 'text-gray-900'
                      }`}
                    >
                      {formatCurrency(line.closing_balance)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {line.alert_flag ? (
                        <span className="inline-block w-3 h-3 rounded-full bg-red-500" title="Alert"></span>
                      ) : (
                        <span className="inline-block w-3 h-3 rounded-full bg-green-500" title="OK"></span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}
