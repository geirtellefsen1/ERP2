import type { Metadata } from 'next'
import PublicShell from '@/components/PublicShell'
import './globals.css'

export const metadata: Metadata = {
  title: {
    default: "ClaudERP",
    template: "%s · ClaudERP",
  },
  description: "AI-first accounting and BPO platform by Saga Advisory",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">
        {children}
        <PublicShell />
      </body>
    </html>
  )
}
