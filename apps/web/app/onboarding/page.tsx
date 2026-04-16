"use client";

import { useCallback, useEffect, useState } from "react";

const STEP_NAMES = [
  "Agency Setup",
  "Invite Users",
  "Connect Bank",
  "Import Chart of Accounts",
  "First Client",
] as const;

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface OnboardingState {
  current_step: number;
  step_data: Record<string, unknown> | null;
  completed_at: string | null;
  step_names: string[];
}

async function fetchState(): Promise<OnboardingState> {
  const res = await fetch(`${API_BASE}/api/v1/onboarding/state`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch onboarding state");
  return res.json();
}

async function saveState(
  currentStep: number,
  stepData?: Record<string, unknown>
): Promise<OnboardingState> {
  const res = await fetch(`${API_BASE}/api/v1/onboarding/state`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      current_step: currentStep,
      step_data: stepData ?? null,
    }),
  });
  if (!res.ok) throw new Error("Failed to save onboarding state");
  return res.json();
}

/* ------------------------------------------------------------------ */
/*  Step-specific form components                                      */
/* ------------------------------------------------------------------ */

function AgencySetupForm({
  data,
  onChange,
}: {
  data: Record<string, unknown>;
  onChange: (d: Record<string, unknown>) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="agency-name" className="block text-sm font-medium text-slate-700 mb-1">
          Agency Name
        </label>
        <input
          id="agency-name"
          type="text"
          placeholder="Acme Accounting"
          value={(data.agency_name as string) ?? ""}
          onChange={(e) => onChange({ ...data, agency_name: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <div>
        <label htmlFor="agency-slug" className="block text-sm font-medium text-slate-700 mb-1">
          Slug
        </label>
        <input
          id="agency-slug"
          type="text"
          placeholder="acme-accounting"
          value={(data.slug as string) ?? ""}
          onChange={(e) => onChange({ ...data, slug: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <p className="text-xs text-slate-500">Creates your agency workspace.</p>
    </div>
  );
}

function InviteUsersForm({
  data,
  onChange,
}: {
  data: Record<string, unknown>;
  onChange: (d: Record<string, unknown>) => void;
}) {
  const emails = (data.emails as string[]) ?? [];
  const [draft, setDraft] = useState("");

  const addEmail = () => {
    const trimmed = draft.trim();
    if (trimmed && !emails.includes(trimmed)) {
      onChange({ ...data, emails: [...emails, trimmed] });
    }
    setDraft("");
  };

  const removeEmail = (email: string) => {
    onChange({ ...data, emails: emails.filter((e) => e !== email) });
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="email"
          placeholder="colleague@example.com"
          aria-label="Email address"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addEmail();
            }
          }}
          className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          type="button"
          onClick={addEmail}
          className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          Add
        </button>
      </div>
      {emails.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {emails.map((email) => (
            <span
              key={email}
              className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-200"
            >
              {email}
              <button
                type="button"
                onClick={() => removeEmail(email)}
                className="ml-1 text-blue-400 hover:text-blue-700"
                aria-label={`Remove ${email}`}
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ConnectBankForm({
  data,
  onChange,
}: {
  data: Record<string, unknown>;
  onChange: (d: Record<string, unknown>) => void;
}) {
  const connected = Boolean(data.bank_connected);

  return (
    <div className="space-y-4 text-center">
      <button
        type="button"
        onClick={() => onChange({ ...data, bank_connected: !connected })}
        className={`px-6 py-3 font-semibold rounded-lg transition-colors ${
          connected
            ? "bg-green-600 text-white hover:bg-green-700"
            : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
      >
        {connected ? "Connected via Aiia" : "Connect via Aiia"}
      </button>
      <div className="flex items-center justify-center gap-2 text-sm">
        <span
          className={`inline-block w-2.5 h-2.5 rounded-full ${
            connected ? "bg-green-500" : "bg-slate-300"
          }`}
        />
        <span className={connected ? "text-green-700" : "text-slate-500"}>
          {connected ? "Bank connected" : "Not connected"}
        </span>
      </div>
    </div>
  );
}

function ImportChartForm({
  data,
  onChange,
}: {
  data: Record<string, unknown>;
  onChange: (d: Record<string, unknown>) => void;
}) {
  const fileName = (data.file_name as string) ?? "";

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onChange({ ...data, file_name: file.name });
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="csv-upload" className="block text-sm font-medium text-slate-700 mb-1">
          Upload CSV
        </label>
        <input
          id="csv-upload"
          type="file"
          accept=".csv"
          onChange={handleFile}
          className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
      </div>
      <div className="rounded-lg bg-slate-50 border border-dashed border-slate-300 p-6 text-center">
        <p className="text-sm text-slate-500">
          {fileName
            ? `Selected: ${fileName}`
            : "Upload a CSV file to preview your chart of accounts."}
        </p>
      </div>
    </div>
  );
}

function FirstClientForm({
  data,
  onChange,
}: {
  data: Record<string, unknown>;
  onChange: (d: Record<string, unknown>) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="client-name" className="block text-sm font-medium text-slate-700 mb-1">
          Client Name
        </label>
        <input
          id="client-name"
          type="text"
          placeholder="Fjord Industries AS"
          value={(data.client_name as string) ?? ""}
          onChange={(e) => onChange({ ...data, client_name: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <div>
        <label htmlFor="reg-number" className="block text-sm font-medium text-slate-700 mb-1">
          Registration Number
        </label>
        <input
          id="reg-number"
          type="text"
          placeholder="912 345 678"
          value={(data.registration_number as string) ?? ""}
          onChange={(e) => onChange({ ...data, registration_number: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <div>
        <label htmlFor="country" className="block text-sm font-medium text-slate-700 mb-1">
          Country
        </label>
        <select
          id="country"
          value={(data.country as string) ?? ""}
          onChange={(e) => onChange({ ...data, country: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select country</option>
          <option value="Norway">Norway</option>
          <option value="Sweden">Sweden</option>
          <option value="Finland">Finland</option>
        </select>
      </div>
      <div>
        <label htmlFor="industry" className="block text-sm font-medium text-slate-700 mb-1">
          Industry
        </label>
        <input
          id="industry"
          type="text"
          placeholder="Technology"
          value={(data.industry as string) ?? ""}
          onChange={(e) => onChange({ ...data, industry: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <p className="text-xs text-slate-500">
        <a
          href="https://calendly.com/clauderp/demo"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          Book a demo: https://calendly.com/clauderp/demo
        </a>
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Shared components                                                  */
/* ------------------------------------------------------------------ */

function ProgressBar({ currentStep }: { currentStep: number }) {
  return (
    <div className="w-full mb-10">
      {/* Step labels */}
      <div className="hidden sm:flex justify-between mb-2">
        {STEP_NAMES.map((name, idx) => {
          const stepNum = idx + 1;
          const isActive = stepNum === currentStep;
          const isComplete = stepNum < currentStep;
          return (
            <span
              key={name}
              className={`text-xs font-medium ${
                isActive
                  ? "text-blue-600"
                  : isComplete
                  ? "text-slate-500"
                  : "text-slate-400"
              }`}
            >
              {name}
            </span>
          );
        })}
      </div>

      {/* Bar */}
      <div className="flex items-center gap-1">
        {STEP_NAMES.map((name, idx) => {
          const stepNum = idx + 1;
          const isActive = stepNum === currentStep;
          const isComplete = stepNum < currentStep;
          return (
            <div
              key={name}
              className={`h-2 flex-1 rounded-full transition-colors ${
                isComplete
                  ? "bg-blue-600"
                  : isActive
                  ? "bg-blue-400"
                  : "bg-slate-200"
              }`}
            />
          );
        })}
      </div>

      {/* Mobile: show current step label */}
      <p className="sm:hidden text-center text-sm text-blue-600 font-medium mt-2">
        Step {currentStep} of {STEP_NAMES.length}: {STEP_NAMES[currentStep - 1]}
      </p>
    </div>
  );
}

function StepCard({
  stepNumber,
  name,
  isLast,
  onContinue,
  onBack,
  saving,
  children,
}: {
  stepNumber: number;
  name: string;
  isLast: boolean;
  onContinue: () => void;
  onBack: () => void;
  saving: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 max-w-lg w-full">
      <div className="mb-1 text-sm font-medium text-blue-600">
        Step {stepNumber} of {STEP_NAMES.length}
      </div>
      <h2 className="text-2xl font-bold text-slate-900 mb-6">{name}</h2>

      <div className="mb-8">{children}</div>

      <div className="flex justify-between">
        {stepNumber > 1 ? (
          <button
            type="button"
            onClick={onBack}
            disabled={saving}
            className="px-6 py-2.5 bg-white text-slate-700 font-semibold rounded-lg border border-slate-200 hover:border-slate-300 transition-colors disabled:opacity-50"
          >
            Back
          </button>
        ) : (
          <span />
        )}

        <button
          type="button"
          onClick={onContinue}
          disabled={saving}
          className="px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? "Saving..." : isLast ? "Complete Setup" : "Continue"}
        </button>
      </div>
    </div>
  );
}

function CompletedCard() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 max-w-lg w-full text-center">
      <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
        <svg
          className="w-8 h-8 text-green-600"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-slate-900 mb-2">Setup Complete!</h2>
      <p className="text-slate-500 mb-6">
        Your agency is ready to go. Head to the dashboard to get started.
      </p>
      <a
        href="/"
        className="inline-block px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
      >
        Go to Dashboard
      </a>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [completed, setCompleted] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Per-step form data keyed by step number
  const [stepData, setStepData] = useState<Record<number, Record<string, unknown>>>({
    1: {},
    2: {},
    3: {},
    4: {},
    5: {},
  });

  const updateStepData = useCallback(
    (step: number, data: Record<string, unknown>) => {
      setStepData((prev) => ({ ...prev, [step]: data }));
    },
    []
  );

  useEffect(() => {
    fetchState()
      .then((state) => {
        setCurrentStep(state.current_step);
        if (state.completed_at) setCompleted(true);
        if (state.step_data) {
          // Restore previously saved step data if the API returns it
          const restored: Record<number, Record<string, unknown>> = {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
          };
          for (const [key, value] of Object.entries(state.step_data)) {
            const num = Number(key);
            if (num >= 1 && num <= 5 && typeof value === "object" && value !== null) {
              restored[num] = value as Record<string, unknown>;
            }
          }
          setStepData(restored);
        }
      })
      .catch(() => {
        // If API is unreachable, start at step 1 (graceful degradation)
      })
      .finally(() => setLoading(false));
  }, []);

  const handleContinue = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const isLast = currentStep === STEP_NAMES.length;
      const allData = { ...stepData };
      if (isLast) {
        await saveState(currentStep, allData);
        setCompleted(true);
      } else {
        const nextStep = currentStep + 1;
        await saveState(nextStep, allData);
        setCurrentStep(nextStep);
      }
    } catch {
      setError("Failed to save progress. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [currentStep, stepData]);

  const handleBack = useCallback(async () => {
    if (currentStep <= 1) return;
    setSaving(true);
    setError(null);
    try {
      const prevStep = currentStep - 1;
      await saveState(prevStep, stepData);
      setCurrentStep(prevStep);
    } catch {
      setError("Failed to save progress. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [currentStep, stepData]);

  const renderStepContent = () => {
    const data = stepData[currentStep] ?? {};
    const onChange = (d: Record<string, unknown>) => updateStepData(currentStep, d);

    switch (currentStep) {
      case 1:
        return <AgencySetupForm data={data} onChange={onChange} />;
      case 2:
        return <InviteUsersForm data={data} onChange={onChange} />;
      case 3:
        return <ConnectBankForm data={data} onChange={onChange} />;
      case 4:
        return <ImportChartForm data={data} onChange={onChange} />;
      case 5:
        return <FirstClientForm data={data} onChange={onChange} />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        <p className="text-slate-400 text-sm">Loading...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 py-16 px-4">
      <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-2 tracking-tight">
        Welcome to BPO Nexus
      </h1>
      <p className="text-slate-500 mb-8">
        Let&#39;s get your agency set up in a few quick steps.
      </p>

      <div className="w-full max-w-2xl">
        <ProgressBar currentStep={completed ? STEP_NAMES.length + 1 : currentStep} />
      </div>

      {error && (
        <div className="mb-4 px-4 py-2 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
          {error}
        </div>
      )}

      {completed ? (
        <CompletedCard />
      ) : (
        <StepCard
          stepNumber={currentStep}
          name={STEP_NAMES[currentStep - 1]}
          isLast={currentStep === STEP_NAMES.length}
          onContinue={handleContinue}
          onBack={handleBack}
          saving={saving}
        >
          {renderStepContent()}
        </StepCard>
      )}
    </main>
  );
}
