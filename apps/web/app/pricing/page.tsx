import Link from 'next/link';

export const metadata = {
  title: 'Pricing — BPO Nexus',
  description: 'Simple, transparent pricing for AI-powered BPO services.',
};

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-6 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Simple, Transparent Pricing</h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Plans that scale with your business. All plans include multi-jurisdiction support
            for South Africa, Norway, and the UK.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {/* Starter */}
          <div className="rounded-xl border border-slate-200 bg-white p-8">
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Starter</h3>
            <p className="text-sm text-slate-500 mb-4">For small businesses and freelancers</p>
            <div className="mb-6">
              <span className="text-4xl font-bold text-slate-900">TBD</span>
              <span className="text-slate-500 ml-1">/month</span>
            </div>
            <ul className="space-y-3 text-sm text-slate-600 mb-8">
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Basic accounting
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Single entity
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Email support
              </li>
            </ul>
            <button className="w-full py-2.5 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
              Coming Soon
            </button>
          </div>

          {/* Professional */}
          <div className="rounded-xl border-2 border-blue-600 bg-white p-8 relative">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-blue-600 text-white text-xs font-semibold rounded-full">
              Most Popular
            </span>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Professional</h3>
            <p className="text-sm text-slate-500 mb-4">For growing BPO practices</p>
            <div className="mb-6">
              <span className="text-4xl font-bold text-slate-900">TBD</span>
              <span className="text-slate-500 ml-1">/month</span>
            </div>
            <ul className="space-y-3 text-sm text-slate-600 mb-8">
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Full accounting &amp; payroll
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Up to 20 client entities
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Multi-jurisdiction support
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Priority support
              </li>
            </ul>
            <button className="w-full py-2.5 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors">
              Coming Soon
            </button>
          </div>

          {/* Enterprise */}
          <div className="rounded-xl border border-slate-200 bg-white p-8">
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Enterprise</h3>
            <p className="text-sm text-slate-500 mb-4">For large firms and multi-national operations</p>
            <div className="mb-6">
              <span className="text-4xl font-bold text-slate-900">Custom</span>
            </div>
            <ul className="space-y-3 text-sm text-slate-600 mb-8">
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Everything in Professional
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Unlimited entities
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Dedicated account manager
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">&#10003;</span>
                Custom integrations &amp; SLA
              </li>
            </ul>
            <button className="w-full py-2.5 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
              Contact Sales
            </button>
          </div>
        </div>

        <div className="text-center">
          <p className="text-sm text-slate-500">
            Pricing details will be published before general availability.{' '}
            <Link href="/" className="text-blue-600 hover:text-blue-700 underline">
              Request early access
            </Link>{' '}
            to be notified.
          </p>
        </div>
      </div>
    </main>
  );
}
