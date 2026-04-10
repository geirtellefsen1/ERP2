'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchAPI } from '../../../lib/api';

interface Document {
  id: number;
  file_name: string;
  document_type: string;
  status: string;
  file_size: number;
  mime_type: string;
  created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      const data = await fetchAPI<{ items: Document[]; total: number }>('/documents?per_page=50');
      setDocuments(data.items || []);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    setSelectedFiles((prev) => [...prev, ...files]);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  async function uploadFiles() {
    if (selectedFiles.length === 0) return;
    setUploading(true);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        const headers: Record<string, string> = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        await fetch(`${API_URL}/documents/upload?client_id=1`, {
          method: 'POST',
          headers,
          body: formData,
        });
      }

      setSelectedFiles([]);
      await loadDocuments();
    } catch (error) {
      console.error('Failed to upload documents:', error);
    } finally {
      setUploading(false);
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'extracted': return 'bg-blue-100 text-blue-800';
      case 'posted': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Documents</h1>

      {/* Drag and Drop Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center mb-6 transition-colors ${
          dragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-slate-300 bg-white hover:border-slate-400'
        }`}
      >
        <svg
          className="w-10 h-10 mx-auto text-slate-400 mb-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p className="text-slate-600 mb-2">Drag and drop files here, or</p>
        <label className="inline-block px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg cursor-pointer hover:bg-blue-700 transition-colors">
          Browse Files
          <input
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
        </label>
        <p className="text-xs text-slate-400 mt-2">PDF, images, spreadsheets up to 25MB</p>
      </div>

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 mb-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">
            Files to upload ({selectedFiles.length})
          </h3>
          <ul className="space-y-2 mb-4">
            {selectedFiles.map((file, index) => (
              <li key={index} className="flex items-center justify-between text-sm">
                <span className="text-slate-700">{file.name}</span>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400">{formatSize(file.size)}</span>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-red-500 hover:text-red-700 text-xs"
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <button
            onClick={uploadFiles}
            disabled={uploading}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {uploading ? 'Uploading...' : 'Upload All'}
          </button>
        </div>
      )}

      {/* Document List */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="p-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">Uploaded Documents</h2>
        </div>
        {loading ? (
          <div className="p-6 text-slate-500 text-center">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="p-6 text-slate-500 text-center">No documents uploaded yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-slate-600">
                <th className="px-4 py-3">File Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">{doc.file_name}</td>
                  <td className="px-4 py-3 text-slate-600">{doc.document_type}</td>
                  <td className="px-4 py-3 text-slate-600">{formatSize(doc.file_size)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor(doc.status)}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
