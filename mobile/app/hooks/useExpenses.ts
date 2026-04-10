import { useState, useCallback } from 'react';
import { Expense } from '../../types';

const MOCK_EXPENSES: Expense[] = [
  {
    id: '1',
    userId: '1',
    amount: 45.99,
    currency: 'USD',
    category: 'Meals',
    description: 'Client lunch meeting',
    status: 'submitted',
    submittedAt: '2026-04-08T10:00:00Z',
    createdAt: '2026-04-08T09:30:00Z',
    updatedAt: '2026-04-08T10:00:00Z',
  },
  {
    id: '2',
    userId: '1',
    amount: 120.0,
    currency: 'USD',
    category: 'Travel',
    description: 'Uber to client site',
    status: 'approved',
    submittedAt: '2026-04-05T08:00:00Z',
    createdAt: '2026-04-05T07:30:00Z',
    updatedAt: '2026-04-06T14:00:00Z',
  },
];

export function useExpenses() {
  const [expenses, setExpenses] = useState<Expense[]>(MOCK_EXPENSES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExpenses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Would call: const data = await fetchAPI('/api/expenses');
      // setExpenses(data);
      setExpenses(MOCK_EXPENSES);
    } catch (err) {
      setError('Failed to load expenses');
    } finally {
      setLoading(false);
    }
  }, []);

  const createExpense = useCallback(
    async (expense: Omit<Expense, 'id' | 'createdAt' | 'updatedAt'>) => {
      setLoading(true);
      setError(null);
      try {
        // Would call: const data = await fetchAPI('/api/expenses', { method: 'POST', body: JSON.stringify(expense) });
        const newExpense: Expense = {
          ...expense,
          id: Date.now().toString(),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        setExpenses((prev) => [newExpense, ...prev]);
        return newExpense;
      } catch (err) {
        setError('Failed to create expense');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const deleteExpense = useCallback(async (id: string) => {
    setLoading(true);
    try {
      // Would call: await fetchAPI(`/api/expenses/${id}`, { method: 'DELETE' });
      setExpenses((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      setError('Failed to delete expense');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    expenses,
    loading,
    error,
    fetchExpenses,
    createExpense,
    deleteExpense,
  };
}
