"use client";

import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface LeaveType {
  id: number;
  name: string;
  code: string | null;
  is_paid: boolean;
}

interface LeaveBalance {
  id: number;
  employee_id: number;
  leave_type_id: number;
  calendar_year: number;
  opening_balance: number;
  entitlements: number;
  used: number;
  closing_balance: number;
}

interface LeaveRequest {
  id: number;
  employee_id: number;
  leave_type_id: number;
  start_date: string;
  end_date: string;
  business_days: number;
  status: string;
  approver_id: number | null;
  approved_at: string | null;
  rejection_reason: string | null;
  created_at: string;
}

const statusColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  submitted: "bg-blue-100 text-blue-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export default function LeavePage() {
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [calculatedDays, setCalculatedDays] = useState<number | null>(null);
  const [form, setForm] = useState({
    leave_type_id: "",
    start_date: "",
    end_date: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");

  const getToken = () => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("token") || "";
    }
    return "";
  };

  const headers = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
  });

  useEffect(() => {
    fetchLeaveTypes();
    fetchRequests();
  }, []);

  useEffect(() => {
    fetchRequests();
  }, [statusFilter]);

  useEffect(() => {
    if (form.start_date && form.end_date) {
      calculateDays();
    } else {
      setCalculatedDays(null);
    }
  }, [form.start_date, form.end_date]);

  async function fetchLeaveTypes() {
    try {
      const res = await fetch(`${API}/leave/types`, { headers: headers() });
      if (res.ok) {
        setLeaveTypes(await res.json());
      }
    } catch {
      // silent
    }
  }

  async function fetchRequests() {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : "";
      const res = await fetch(`${API}/leave/requests${params}`, {
        headers: headers(),
      });
      if (res.ok) {
        const data = await res.json();
        setRequests(data.items || []);
      }
    } catch {
      // silent
    }
  }

  async function fetchBalances(employeeId: number) {
    try {
      const res = await fetch(`${API}/leave/balance/${employeeId}`, {
        headers: headers(),
      });
      if (res.ok) {
        setBalances(await res.json());
      }
    } catch {
      // silent
    }
  }

  async function calculateDays() {
    try {
      const res = await fetch(`${API}/leave/calculate-days`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          start_date: form.start_date,
          end_date: form.end_date,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setCalculatedDays(data.business_days);
      }
    } catch {
      setCalculatedDays(null);
    }
  }

  async function submitRequest(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API}/leave/requests`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          leave_type_id: Number(form.leave_type_id),
          start_date: form.start_date,
          end_date: form.end_date,
        }),
      });

      if (res.ok) {
        setForm({ leave_type_id: "", start_date: "", end_date: "" });
        setCalculatedDays(null);
        fetchRequests();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to submit leave request");
      }
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Leave Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leave Request Form */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">New Leave Request</h2>
            <form onSubmit={submitRequest} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Leave Type
                </label>
                <select
                  value={form.leave_type_id}
                  onChange={(e) =>
                    setForm({ ...form, leave_type_id: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  required
                >
                  <option value="">Select type...</option>
                  {leaveTypes.map((lt) => (
                    <option key={lt.id} value={lt.id}>
                      {lt.name}
                      {lt.code ? ` (${lt.code})` : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  value={form.start_date}
                  onChange={(e) =>
                    setForm({ ...form, start_date: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  value={form.end_date}
                  onChange={(e) =>
                    setForm({ ...form, end_date: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  required
                />
              </div>

              {calculatedDays !== null && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <p className="text-sm text-blue-800">
                    <span className="font-semibold">{calculatedDays}</span>{" "}
                    business day{calculatedDays !== 1 ? "s" : ""}
                  </p>
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
              >
                {loading ? "Submitting..." : "Submit Leave Request"}
              </button>
            </form>
          </div>

          {/* Leave Balances */}
          <div className="bg-white rounded-lg shadow p-6 mt-6">
            <h2 className="text-lg font-semibold mb-4">Leave Balances</h2>
            {balances.length === 0 ? (
              <p className="text-sm text-gray-500">
                No balance records found.
              </p>
            ) : (
              <div className="space-y-3">
                {balances.map((b) => (
                  <div
                    key={b.id}
                    className="border border-gray-200 rounded-md p-3"
                  >
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Entitlements</span>
                      <span className="font-medium">{b.entitlements}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Used</span>
                      <span className="font-medium">{b.used}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Remaining</span>
                      <span className="font-semibold text-green-600">
                        {b.closing_balance}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Leave Requests List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Leave Requests</h2>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1.5 text-sm"
              >
                <option value="">All statuses</option>
                <option value="draft">Draft</option>
                <option value="submitted">Submitted</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>

            {requests.length === 0 ? (
              <p className="text-sm text-gray-500">No leave requests found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-2 font-medium text-gray-600">
                        ID
                      </th>
                      <th className="text-left py-3 px-2 font-medium text-gray-600">
                        Start
                      </th>
                      <th className="text-left py-3 px-2 font-medium text-gray-600">
                        End
                      </th>
                      <th className="text-left py-3 px-2 font-medium text-gray-600">
                        Days
                      </th>
                      <th className="text-left py-3 px-2 font-medium text-gray-600">
                        Status
                      </th>
                      <th className="text-left py-3 px-2 font-medium text-gray-600">
                        Submitted
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {requests.map((req) => (
                      <tr
                        key={req.id}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="py-3 px-2">{req.id}</td>
                        <td className="py-3 px-2">{req.start_date}</td>
                        <td className="py-3 px-2">{req.end_date}</td>
                        <td className="py-3 px-2">{req.business_days}</td>
                        <td className="py-3 px-2">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                              statusColors[req.status] || "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {req.status}
                          </span>
                        </td>
                        <td className="py-3 px-2 text-gray-500">
                          {new Date(req.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
