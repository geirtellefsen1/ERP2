import type { Metadata } from "next"
import "./globals.css"
import { ToastProvider } from "@/components/ui/toast"
import { I18nProvider } from "@/i18n/provider"

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
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen">
        <I18nProvider>
          <ToastProvider>{children}</ToastProvider>
        </I18nProvider>
      </body>
    </html>
  )
}
