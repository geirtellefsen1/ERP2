export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'employee' | 'manager' | 'admin';
  department: string;
  avatarUrl?: string;
}

export interface Expense {
  id: string;
  userId: string;
  amount: number;
  currency: string;
  category: string;
  description: string;
  receiptUrl?: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected';
  submittedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TimeEntry {
  id: string;
  userId: string;
  projectId: string;
  projectName: string;
  description: string;
  startTime: string;
  endTime?: string;
  duration: number; // in seconds
  status: 'running' | 'stopped' | 'submitted' | 'approved';
  date: string;
}

export interface Payslip {
  id: string;
  userId: string;
  period: string;
  grossPay: number;
  netPay: number;
  deductions: number;
  taxes: number;
  currency: string;
  paidAt: string;
  downloadUrl: string;
}

export interface LeaveRequest {
  id: string;
  userId: string;
  type: 'annual' | 'sick' | 'personal' | 'maternity' | 'paternity' | 'unpaid';
  startDate: string;
  endDate: string;
  businessDays: number;
  reason: string;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  createdAt: string;
}

export interface ApprovalItem {
  id: string;
  type: 'expense' | 'timesheet' | 'leave';
  requesterId: string;
  requesterName: string;
  summary: string;
  amount?: number;
  submittedAt: string;
  status: 'pending' | 'approved' | 'rejected';
}
