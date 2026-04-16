'use client';

import { useState, useEffect } from 'react';
import { hasConsentChoice, setConsent } from '@/lib/consent';

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);
  const [showManage, setShowManage] = useState(false);
  const [analyticsEnabled, setAnalyticsEnabled] = useState(false);

  useEffect(() => {
    if (!hasConsentChoice()) {
      setVisible(true);
    }
  }, []);

  function handleAcceptAll() {
    setConsent(true);
    setVisible(false);
  }

  function handleRejectAll() {
    setConsent(false);
    setVisible(false);
  }

  function handleSavePreferences() {
    setConsent(analyticsEnabled);
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 inset-x-0 z-50 p-4">
      <div className="mx-auto max-w-3xl rounded-xl bg-white shadow-2xl border border-slate-200 p-6">
        {!showManage ? (
          <>
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Cookie Preferences</h3>
              <p className="mt-1 text-sm text-slate-600">
                We use essential cookies to make our site work. With your consent, we may also use
                analytics cookies to improve our services. You can change your preferences at any time.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleRejectAll}
                className="px-5 py-2.5 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Reject All
              </button>
              <button
                onClick={() => setShowManage(true)}
                className="px-5 py-2.5 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Manage
              </button>
              <button
                onClick={handleAcceptAll}
                className="px-5 py-2.5 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                Accept All
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Manage Cookie Preferences</h3>
            </div>
            <div className="space-y-4 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-900">Essential Cookies</p>
                  <p className="text-xs text-slate-500">Required for the site to function. Cannot be disabled.</p>
                </div>
                <div className="h-6 w-11 rounded-full bg-blue-600 relative cursor-not-allowed">
                  <div className="absolute right-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-900">Analytics Cookies</p>
                  <p className="text-xs text-slate-500">Help us understand how visitors use our site.</p>
                </div>
                <button
                  onClick={() => setAnalyticsEnabled(!analyticsEnabled)}
                  className={`h-6 w-11 rounded-full relative transition-colors ${
                    analyticsEnabled ? 'bg-blue-600' : 'bg-slate-300'
                  }`}
                >
                  <div
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                      analyticsEnabled ? 'right-0.5' : 'left-0.5'
                    }`}
                  />
                </button>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => setShowManage(false)}
                className="px-5 py-2.5 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleSavePreferences}
                className="px-5 py-2.5 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                Save Preferences
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
