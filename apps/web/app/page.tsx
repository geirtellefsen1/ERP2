export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="text-center px-6">
        <div className="mb-6">
          <span className="inline-block px-4 py-1.5 bg-blue-100 text-blue-700 text-sm font-semibold rounded-full tracking-wide uppercase">
            Coming Soon
          </span>
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-slate-900 mb-4 tracking-tight">
          BPO Nexus
        </h1>
        <p className="text-xl md:text-2xl text-blue-600 font-medium mb-3">
          AI-First Business Process Outsourcing
        </p>
        <p className="text-slate-500 max-w-md mx-auto mb-10">
          Accounting, payroll, compliance and advisory — managed for multiple clients across South Africa, Norway and the UK from one intelligent platform.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
            Get Early Access
          </button>
          <button className="px-8 py-3 bg-white text-slate-700 font-semibold rounded-lg border border-slate-200 hover:border-slate-300 transition-colors">
            Contact Sales
          </button>
        </div>
      </div>

      <footer className="absolute bottom-6 text-slate-400 text-sm">
        © 2026 Saga Advisory AS · BPO Nexus
      </footer>
    </main>
  )
}
