// Shared TypeScript types for BPO Nexus
// Used by both web and api packages

export interface Agency {
  id: number
  name: string
  slug: string
  subscriptionTier: 'starter' | 'growth' | 'enterprise'
  countriesEnabled: string[]
  createdAt: string
}

export interface Client {
  id: number
  agencyId: number
  name: string
  registrationNumber?: string
  country: 'ZA' | 'NO' | 'UK' | 'EU'
  industry: string
  fiscalYearEnd?: string
  isActive: boolean
  createdAt: string
}

export interface User {
  id: number
  agencyId: number
  email: string
  fullName: string
  role: 'admin' | 'agent' | 'client_admin' | 'client_user'
  isActive: boolean
}

export interface Invoice {
  id: number
  clientId: number
  invoiceNumber: string
  status: 'draft' | 'sent' | 'paid' | 'overdue'
  amount: number
  currency: string
  dueDate: string
  issuedAt: string
}

export interface PayrollRun {
  id: number
  clientId: number
  periodStart: string
  periodEnd: string
  status: 'draft' | 'processing' | 'submitted' | 'paid'
  totalGross: number
  totalPaye: number
  totalUif: number
}

export type Country = 'ZA' | 'NO' | 'UK' | 'EU'
export type SubscriptionTier = 'starter' | 'growth' | 'enterprise'
