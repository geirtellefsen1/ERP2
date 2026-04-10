'use client';

import { useState } from 'react';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
}

function MetricCard({ title, value, subtitle }: MetricCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 border border-slate-200">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="text-3xl font-bold text-slate-900 mt-2">{value}</p>
      <p className="text-sm text-slate-400 mt-1">{subtitle}</p>
    </div>
  );
}

export default function HospitalityDashboard() {
  const [stockForm, setStockForm] = useState({
    item_code: '',
    description: '',
    quantity_counted: 0,
    quantity_expected: 0,
    unit_cost: 0,
  });

  const handleStockFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setStockForm((prev) => ({
      ...prev,
      [name]: name === 'item_code' || name === 'description' ? value : Number(value),
    }));
  };

  const variance =
    (stockForm.quantity_counted - stockForm.quantity_expected) * stockForm.unit_cost;

  const handleStockSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // API call would go here
    alert(`Stock take recorded. Variance: ${variance.toFixed(2)}`);
  };

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Hospitality Dashboard</h1>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <MetricCard title="RevPAR" value="--" subtitle="Revenue per available room" />
        <MetricCard title="ADR" value="--" subtitle="Average daily rate" />
        <MetricCard title="Occupancy" value="--%" subtitle="Room occupancy rate" />
      </div>

      {/* Daily Revenue Chart Placeholder */}
      <div className="bg-white rounded-lg shadow p-6 border border-slate-200 mb-8">
        <h2 className="text-lg font-semibold mb-4 text-slate-800">Daily Revenue</h2>
        <div className="h-64 flex items-center justify-center bg-slate-50 rounded border border-dashed border-slate-300">
          <p className="text-slate-400">Revenue chart will render here</p>
        </div>
      </div>

      {/* Stock Take Form */}
      <div className="bg-white rounded-lg shadow p-6 border border-slate-200">
        <h2 className="text-lg font-semibold mb-4 text-slate-800">Stock Take</h2>
        <form onSubmit={handleStockSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Item Code</label>
            <input
              type="text"
              name="item_code"
              value={stockForm.item_code}
              onChange={handleStockFormChange}
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. BEV-001"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <input
              type="text"
              name="description"
              value={stockForm.description}
              onChange={handleStockFormChange}
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. House Red Wine"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Quantity Counted</label>
            <input
              type="number"
              name="quantity_counted"
              value={stockForm.quantity_counted}
              onChange={handleStockFormChange}
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Quantity Expected</label>
            <input
              type="number"
              name="quantity_expected"
              value={stockForm.quantity_expected}
              onChange={handleStockFormChange}
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Unit Cost</label>
            <input
              type="number"
              name="unit_cost"
              value={stockForm.unit_cost}
              onChange={handleStockFormChange}
              step="0.01"
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Variance</label>
            <input
              type="text"
              readOnly
              value={variance.toFixed(2)}
              className={`w-full border rounded-md px-3 py-2 text-sm bg-slate-50 ${
                variance < 0 ? 'text-red-600 border-red-300' : variance > 0 ? 'text-green-600 border-green-300' : 'text-slate-700 border-slate-300'
              }`}
            />
          </div>
          <div className="md:col-span-2">
            <button
              type="submit"
              className="bg-blue-600 text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Record Stock Take
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
