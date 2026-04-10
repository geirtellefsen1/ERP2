const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAPI<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

export const clients = {
  list: (page = 1, perPage = 20) =>
    fetchAPI(`/clients?page=${page}&per_page=${perPage}`),
  get: (id: number) => fetchAPI(`/clients/${id}`),
  create: (data: Record<string, unknown>) =>
    fetchAPI('/clients', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Record<string, unknown>) =>
    fetchAPI(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
};

export const tasks = {
  list: (filters: Record<string, string> = {}) => {
    const params = new URLSearchParams(filters);
    return fetchAPI(`/tasks?${params}`);
  },
  create: (data: Record<string, unknown>) =>
    fetchAPI('/tasks', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Record<string, unknown>) =>
    fetchAPI(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
};
