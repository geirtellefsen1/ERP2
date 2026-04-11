"use client";
import { useState } from "react";

const REPORTS = [
  { id: "profit-and-loss", label: "Profit & Loss", desc: "Revenue vs expenses for a period" },
  { id: "balance-sheet", label: "Balance Sheet", desc: "Assets, liabilities and equity snapshot" },
  { id: "cash-flow", label: "Cash Flow", desc: "Operating, investing and financing flows" },
];

export default function PortalReportsPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [year, setYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);

  async function downloadReport(reportId: string) {
    setLoading(true);
    setSelected(reportId);
    // In production: fetch from /api/v1/reports/{reportId}?client_id=X&year=Y&format=pdf
    await new Promise((r) => setTimeout(r, 1500));
    setLoading(false);
    alert("In production, this downloads the PDF report.");
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Financial Reports</h1>
        <p className="text-slate-500 mt-1">Download your financial statements</p>
      </div>

      <div className="mb-6 flex items-center gap-3">
        <label className="text-sm font-medium text-slate-700">Year</label>
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
        >
          {[2024, 2025, 2026].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      <div className="space-y-4">
        {REPORTS.map((report) => (
          <div
            key={report.id}
            className="bg-white border border-slate-200 rounded-xl p-5 flex items-center justify-between hover:border-blue-200 transition-colors"
          >
            <div>
              <div className="font-semibold text-slate-900">{report.label}</div>
              <div className="text-sm text-slate-500 mt-0.5">{report.desc}</div>
            </div>
            <button
              onClick={() => downloadReport(report.id)}
              disabled={loading && selected === report.id}
              className="ml-4 px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {loading && selected === report.id ? (
                <span>Generating...</span>
              ) : (
                <>
                  <span>Download PDF</span>
                  <span>↓</span>
                </>
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
