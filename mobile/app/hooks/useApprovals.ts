import { useState, useCallback } from 'react';
import { ApprovalItem } from '../../types';

const MOCK_APPROVALS: ApprovalItem[] = [
  {
    id: 'a1',
    type: 'expense',
    requesterId: 'u2',
    requesterName: 'Alice Johnson',
    summary: 'Client dinner - $89.50',
    amount: 89.5,
    submittedAt: '2026-04-09T14:00:00Z',
    status: 'pending',
  },
  {
    id: 'a2',
    type: 'timesheet',
    requesterId: 'u3',
    requesterName: 'Bob Smith',
    summary: 'Week of Apr 7 - 42 hours',
    submittedAt: '2026-04-09T17:00:00Z',
    status: 'pending',
  },
  {
    id: 'a3',
    type: 'leave',
    requesterId: 'u4',
    requesterName: 'Carol Davis',
    summary: 'Annual Leave - Apr 15-18 (4 days)',
    submittedAt: '2026-04-08T09:00:00Z',
    status: 'pending',
  },
];

export function useApprovals() {
  const [approvals, setApprovals] = useState<ApprovalItem[]>(MOCK_APPROVALS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchApprovals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Would call: const data = await fetchAPI('/api/approvals');
      // setApprovals(data);
      setApprovals(MOCK_APPROVALS);
    } catch {
      setError('Failed to load approvals');
    } finally {
      setLoading(false);
    }
  }, []);

  const approve = useCallback(async (id: string) => {
    try {
      // Would call: await fetchAPI(`/api/approvals/${id}/approve`, { method: 'POST' });
      setApprovals((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: 'approved' as const } : a
        )
      );
    } catch {
      setError('Failed to approve item');
    }
  }, []);

  const reject = useCallback(async (id: string) => {
    try {
      // Would call: await fetchAPI(`/api/approvals/${id}/reject`, { method: 'POST' });
      setApprovals((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: 'rejected' as const } : a
        )
      );
    } catch {
      setError('Failed to reject item');
    }
  }, []);

  const pendingApprovals = approvals.filter((a) => a.status === 'pending');

  return {
    approvals,
    pendingApprovals,
    loading,
    error,
    fetchApprovals,
    approve,
    reject,
  };
}
