"use client"

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react"
import { apiGet } from "./api"

export interface ClientSummary {
  id: number
  name: string
  country: string
  industry: string
  is_active: boolean
}

interface ClientContextValue {
  clients: ClientSummary[]
  selectedClient: ClientSummary | null
  setSelectedClientId: (id: number | null) => void
  loading: boolean
}

const ClientContextObj = createContext<ClientContextValue | undefined>(undefined)

const STORAGE_KEY = "claud_selected_client_id"

export function ClientProvider({ children }: { children: ReactNode }) {
  const [clients, setClients] = useState<ClientSummary[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  // Restore from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const id = parseInt(stored, 10)
        if (!isNaN(id)) setSelectedId(id)
      }
    }

    apiGet<ClientSummary[]>("/api/v1/clients")
      .then((data) => setClients(data))
      .catch(() => setClients([]))
      .finally(() => setLoading(false))
  }, [])

  const setSelectedClientId = useCallback((id: number | null) => {
    setSelectedId(id)
    if (typeof window !== "undefined") {
      if (id === null) localStorage.removeItem(STORAGE_KEY)
      else localStorage.setItem(STORAGE_KEY, id.toString())
    }
  }, [])

  const selectedClient = selectedId
    ? clients.find((c) => c.id === selectedId) || null
    : null

  return (
    <ClientContextObj.Provider
      value={{ clients, selectedClient, setSelectedClientId, loading }}
    >
      {children}
    </ClientContextObj.Provider>
  )
}

export function useClientContext(): ClientContextValue {
  const ctx = useContext(ClientContextObj)
  if (!ctx)
    throw new Error("useClientContext must be used within ClientProvider")
  return ctx
}
