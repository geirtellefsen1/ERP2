'use client';

import { useState } from 'react';
import { fetchAPI } from '../../lib/api';

interface PayslipResult {
  gross_salary: number;
  otp_pension: number;
  trinnskatt: number;
  trygdeavgift: number;
  income_tax: number;
  holiday_pay_accrual: number;
  employer_ni: number;
  net_salary: number;
}

function formatNOK(value: number): string {
  return value.toLocaleString('nb-NO', {
    style: 'currency',
    currency: 'NOK',
    minimumFractionDigits: 2,
  });
}

export default function PayrollNOPage() {
  const [grossSalary, setGrossSalary] = useState('');
  const [pensionPct, setPensionPct] = useState('2.0');
  const [result, setResult] = useState<PayslipResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await fetchAPI<PayslipResult>('/payroll-no/calculate', {
        method: 'POST',
        body: JSON.stringify({
          gross_salary: grossSalary,
          pension_percentage: pensionPct,
        }),
      });
      setResult(data);
    } catch (err) {
      setError('Calculation failed. Please check your inputs and try again.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Norway Payroll Calculator</h1>
      <p className="text-slate-500 mb-6">
        Calculate Norwegian payroll taxes, OTP pension, and holiday pay accrual.
      </p>

      <form onSubmit={handleCalculate} className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Annual Gross Salary (NOK)
            </label>
            <input
              type="number"
              value={grossSalary}
              onChange={(e) => setGrossSalary(e.target.value)}
              placeholder="e.g. 500000"
              min="0"
              step="1000"
              required
              className="w-full border border-slate-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              OTP Pension (%)
            </label>
            <input
              type="number"
              value={pensionPct}
              onChange={(e) => setPensionPct(e.target.value)}
              placeholder="2.0"
              min="0"
              max="25"
              step="0.1"
              className="w-full border border-slate-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Calculating...' : 'Calculate'}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="bg-slate-50 px-6 py-3 border-b">
            <h2 className="text-lg font-semibold text-slate-800">Payslip Breakdown</h2>
          </div>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b">
                <td className="px-6 py-3 font-medium text-slate-700">Gross Salary</td>
                <td className="px-6 py-3 text-right font-mono">{formatNOK(result.gross_salary)}</td>
              </tr>
              <tr className="border-b bg-slate-50">
                <td className="px-6 py-2 text-slate-500 pl-10">Trinnskatt (bracket tax)</td>
                <td className="px-6 py-2 text-right font-mono text-red-600">
                  -{formatNOK(result.trinnskatt)}
                </td>
              </tr>
              <tr className="border-b bg-slate-50">
                <td className="px-6 py-2 text-slate-500 pl-10">Trygdeavgift (social security 7.9%)</td>
                <td className="px-6 py-2 text-right font-mono text-red-600">
                  -{formatNOK(result.trygdeavgift)}
                </td>
              </tr>
              <tr className="border-b">
                <td className="px-6 py-3 font-medium text-slate-700">Total Income Tax</td>
                <td className="px-6 py-3 text-right font-mono text-red-600">
                  -{formatNOK(result.income_tax)}
                </td>
              </tr>
              <tr className="border-b">
                <td className="px-6 py-3 font-medium text-slate-700">OTP Pension</td>
                <td className="px-6 py-3 text-right font-mono text-red-600">
                  -{formatNOK(result.otp_pension)}
                </td>
              </tr>
              <tr className="border-b bg-green-50">
                <td className="px-6 py-3 font-bold text-slate-800">Net Salary</td>
                <td className="px-6 py-3 text-right font-mono font-bold text-green-700">
                  {formatNOK(result.net_salary)}
                </td>
              </tr>
              <tr className="border-b">
                <td className="px-6 py-3 text-slate-500">Holiday Pay Accrual (10.2%)</td>
                <td className="px-6 py-3 text-right font-mono text-slate-500">
                  {formatNOK(result.holiday_pay_accrual)}
                </td>
              </tr>
              <tr>
                <td className="px-6 py-3 text-slate-500">Employer NI (14.1%)</td>
                <td className="px-6 py-3 text-right font-mono text-slate-500">
                  {formatNOK(result.employer_ni)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
