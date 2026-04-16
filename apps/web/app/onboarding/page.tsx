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
  const res = await fetch(`${API_BASE}/onboarding/state`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch onboarding state");
  return res.json();
}

async function saveState(
  currentStep: number,
  stepData?: Record<string, unknown>
): Promise<OnboardingState> {
  const res = await fetch(`${API_BASE}/onboarding/state`, {
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
}: {
  stepNumber: number;
  name: string;
  isLast: boolean;
  onContinue: () => void;
  onBack: () => void;
  saving: boolean;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 max-w-lg w-full">
      <div className="mb-1 text-sm font-medium text-blue-600">
        Step {stepNumber} of {STEP_NAMES.length}
      </div>
      <h2 className="text-2xl font-bold text-slate-900 mb-6">{name}</h2>

      <div className="rounded-lg bg-slate-50 border border-dashed border-slate-300 p-10 flex items-center justify-center mb-8">
        <p className="text-slate-400 text-sm">
          {name} form content will go here.
        </p>
      </div>

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

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [completed, setCompleted] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchState()
      .then((state) => {
        setCurrentStep(state.current_step);
        if (state.completed_at) setCompleted(true);
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
      if (isLast) {
        await saveState(currentStep);
        setCompleted(true);
      } else {
        const nextStep = currentStep + 1;
        await saveState(nextStep);
        setCurrentStep(nextStep);
      }
    } catch {
      setError("Failed to save progress. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [currentStep]);

  const handleBack = useCallback(async () => {
    if (currentStep <= 1) return;
    setSaving(true);
    setError(null);
    try {
      const prevStep = currentStep - 1;
      await saveState(prevStep);
      setCurrentStep(prevStep);
    } catch {
      setError("Failed to save progress. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [currentStep]);

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
        />
      )}
    </main>
  );
}
