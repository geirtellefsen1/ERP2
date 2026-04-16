import Link from 'next/link';

export const metadata = {
  title: 'Features — BPO Nexus',
  description: 'AI-powered accounting, payroll, compliance, and advisory for BPO firms.',
};

const features = [
  {
    title: 'Multi-Entity Accounting',
    description:
      'Manage books for multiple client entities across jurisdictions from a single platform. Full chart-of-accounts support for SA, Norway, and UK standards.',
  },
  {
    title: 'Automated Payroll',
    description:
      'Run payroll across South Africa, Norway, and the UK with jurisdiction-aware tax calculations, leave management, and statutory filings.',
  },
  {
    title: 'Compliance & Regulatory',
    description:
      'Stay compliant with automated VAT/GST returns, statutory reporting, and jurisdiction-specific regulatory requirements — all tracked in one place.',
  },
  {
    title: 'AI-Powered Advisory',
    description:
      'Leverage AI to surface insights, flag anomalies, and generate advisory recommendations for your clients automatically.',
  },
  {
    title: 'Client Portal',
    description:
      'Give your clients self-service access to their financial data, documents, and reports through a branded portal.',
  },
  {
    title: 'Row-Level Security',
    description:
      'Enterprise-grade data isolation ensures each tenant and client can only access their own data, enforced at the database level.',
  },
];

export default function FeaturesPage() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-6 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">
            Everything You Need to Run a Modern BPO
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            One intelligent platform for accounting, payroll, compliance, and advisory —
            built for firms operating across South Africa, Norway, and the UK.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-slate-200 bg-white p-6"
            >
              <h3 className="text-lg font-semibold text-slate-900 mb-2">{feature.title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>

        <div className="text-center">
          <p className="text-slate-600 mb-6">
            Ready to modernize your practice?
          </p>
          <Link
            href="/"
            className="inline-block px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Get Early Access
          </Link>
        </div>
      </div>
    </main>
  );
}
