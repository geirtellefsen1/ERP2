'use client';

import { useState } from 'react';

interface Template {
  id: number;
  name: string;
  report_type: string;
  tone: string;
  length: string;
  created_at: string;
}

interface GeneratedReport {
  id: number;
  narrative_commentary: string;
  status: string;
  generated_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ReportingPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [name, setName] = useState('');
  const [reportType, setReportType] = useState('monthly');
  const [tone, setTone] = useState('formal');
  const [length, setLength] = useState('full');
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getAuthHeaders = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  };

  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/reporting/templates`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error('Failed to fetch templates');
      const data = await res.json();
      setTemplates(data.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
    } finally {
      setLoading(false);
    }
  };

  const createTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/reporting/templates`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          name,
          report_type: reportType,
          tone,
          length,
        }),
      });
      if (!res.ok) throw new Error('Failed to create template');
      setName('');
      await fetchTemplates();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create template');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (template: Template) => {
    setGenerating(true);
    setError(null);
    setPreview(null);
    try {
      const res = await fetch(`${API_BASE}/reporting/generate`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          template_id: template.id,
          client_id: 1,
          period_start: '2026-01-01',
          period_end: '2026-03-31',
          financial_data: {
            client_name: 'Sample Client',
            total_revenue: 500000,
            total_expenses: 350000,
            net_income: 150000,
          },
        }),
      });
      if (!res.ok) throw new Error('Failed to generate report');
      const data: GeneratedReport = await res.json();
      setPreview(data.narrative_commentary);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Narrative Report Engine</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Template Creation Form */}
      <section className="mb-8 p-6 border border-gray-200 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Create Report Template</h2>
        <form onSubmit={createTemplate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Monthly Management Report"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="annual">Annual</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tone
            </label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="formal">Formal</option>
              <option value="conversational">Conversational</option>
              <option value="technical">Technical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Length
            </label>
            <select
              value={length}
              onChange={(e) => setLength(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="executive_summary">Executive Summary</option>
              <option value="full">Full Report</option>
              <option value="extended">Extended</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Template'}
            </button>
          </div>
        </form>
      </section>

      {/* Template List */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Templates</h2>
          <button
            onClick={fetchTemplates}
            disabled={loading}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {templates.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No templates yet. Create one above or click Refresh to load existing templates.
          </p>
        ) : (
          <div className="space-y-3">
            {templates.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div>
                  <h3 className="font-medium">{t.name}</h3>
                  <p className="text-sm text-gray-500">
                    {t.report_type} | {t.tone} | {t.length}
                  </p>
                </div>
                <button
                  onClick={() => generateReport(t)}
                  disabled={generating}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {generating ? 'Generating...' : 'Generate Report'}
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Preview Area */}
      {preview && (
        <section className="p-6 border border-gray-200 rounded-lg bg-gray-50">
          <h2 className="text-lg font-semibold mb-4">Generated Narrative</h2>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
            {preview}
          </div>
        </section>
      )}
    </main>
  );
}
