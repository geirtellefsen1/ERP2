"use client";
import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";

interface Document {
  id: number;
  name: string;
  category: string;
  uploaded_at: string;
  size: number;
}

const CATEGORIES = [
  "Bank Statements",
  "Invoices",
  "Contracts",
  "Payslips",
  "Tax Returns",
  "Other",
];

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

export default function DocumentsPage() {
  const params = useParams();
  const clientId = params.clientId as string;
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [category, setCategory] = useState("Other");
  const fileInput = useRef<HTMLInputElement>(null);

  async function uploadFiles(files: FileList) {
    setUploading(true);
    const uploaded = [];
    for (const file of Array.from(files)) {
      // In production: POST to /api/v1/documents/{clientId}/upload
      uploaded.push({
        id: Date.now() + Math.random(),
        name: file.name,
        category,
        uploaded_at: new Date().toISOString(),
        size: file.size,
      });
    }
    setDocuments((prev) => [...uploaded, ...prev]);
    setUploading(false);
  }

  async function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) {
      await uploadFiles(e.dataTransfer.files);
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Documents</h1>
          <p className="text-slate-500 mt-1">Securely upload and manage your documents</p>
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* Drop zone */}
      <div
        className={`border-2 border-dashed rounded-2xl p-12 text-center transition-colors mb-8 ${
          dragOver ? "border-blue-500 bg-blue-50" : "border-slate-300 hover:border-blue-400"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <div className="text-4xl mb-3">📄</div>
        <p className="text-slate-700 font-medium mb-1">
          Drag & drop files here, or{" "}
          <button
            onClick={() => fileInput.current?.click()}
            className="text-blue-600 hover:underline"
          >
            browse files
          </button>
        </p>
        <p className="text-sm text-slate-400">PDF, DOC, JPG, PNG up to 50MB</p>
        <input
          ref={fileInput}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && uploadFiles(e.target.files)}
        />
        {uploading && <p className="mt-2 text-blue-600 text-sm">Uploading...</p>}
      </div>

      {/* Document list */}
      {documents.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="font-semibold text-slate-800">Uploaded Documents ({documents.length})</h2>
          </div>
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                {["Name", "Category", "Size", "Uploaded"].map((h) => (
                  <th key={h} className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-800 text-sm">{doc.name}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-full">{doc.category}</span>
                  </td>
                  <td className="px-6 py-4 text-slate-500 text-sm">{formatSize(doc.size)}</td>
                  <td className="px-6 py-4 text-slate-500 text-sm">{new Date(doc.uploaded_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
