"use client";

import { useState, useEffect, useRef, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ---------- types ---------- */
interface Matter {
  id: number;
  client_id: number;
  code: string | null;
  name: string;
  matter_type: string | null;
  opened_date: string | null;
  closed_date: string | null;
}

interface WIPAging {
  buckets_0_30: string;
  buckets_31_60: string;
  buckets_61_90: string;
  buckets_over_90: string;
}

/* ---------- helpers ---------- */
function authHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function pad(n: number): string {
  return n.toString().padStart(2, "0");
}

function fmtDuration(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

/* ================================================================ */

export default function ProfessionalServicesPage() {
  /* ----- matters ----- */
  const [matters, setMatters] = useState<Matter[]>([]);
  const [matterName, setMatterName] = useState("");
  const [matterCode, setMatterCode] = useState("");
  const [matterType, setMatterType] = useState("corporate");
  const [matterClientId, setMatterClientId] = useState("1");

  /* ----- time entry ----- */
  const [teDescription, setTeDescription] = useState("");
  const [teMatterId, setTeMatterId] = useState("");
  const [teBillable, setTeBillable] = useState(true);

  /* ----- timer ----- */
  const [timerRunning, setTimerRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [timerStart, setTimerStart] = useState<Date | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* ----- WIP ----- */
  const [wip, setWip] = useState<WIPAging | null>(null);

  /* ----- data loading ----- */
  const loadMatters = useCallback(async () => {
    try {
      const res = await fetch(`${API}/ps/matters`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setMatters(data.items ?? []);
      }
    } catch {
      /* ignore network errors in UI */
    }
  }, []);

  const loadWip = useCallback(async () => {
    try {
      const res = await fetch(`${API}/ps/wip/aging`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setWip(data);
      }
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    loadMatters();
    loadWip();
  }, [loadMatters, loadWip]);

  /* ----- timer controls ----- */
  const startTimer = () => {
    setTimerStart(new Date());
    setElapsed(0);
    setTimerRunning(true);
    intervalRef.current = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
  };

  const stopTimer = () => {
    setTimerRunning(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
  };

  const resetTimer = () => {
    stopTimer();
    setElapsed(0);
    setTimerStart(null);
  };

  /* ----- handlers ----- */
  const handleCreateMatter = async () => {
    if (!matterName) return;
    try {
      await fetch(`${API}/ps/matters`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({
          client_id: Number(matterClientId),
          code: matterCode || undefined,
          name: matterName,
          matter_type: matterType,
        }),
      });
      setMatterName("");
      setMatterCode("");
      loadMatters();
    } catch {
      /* ignore */
    }
  };

  const handleSubmitTime = async () => {
    if (!teMatterId || !timerStart) return;
    const end = new Date();
    const startStr = `${pad(timerStart.getHours())}:${pad(timerStart.getMinutes())}`;
    const endStr = `${pad(end.getHours())}:${pad(end.getMinutes())}`;
    const today = new Date().toISOString().slice(0, 10);

    try {
      await fetch(`${API}/ps/time-entries`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({
          matter_id: Number(teMatterId),
          date: today,
          start_time: startStr,
          end_time: endStr,
          description: teDescription,
          billable: teBillable,
        }),
      });
      resetTimer();
      setTeDescription("");
    } catch {
      /* ignore */
    }
  };

  /* ================================================================ */
  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Professional Services</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ---------- Matters list ---------- */}
        <section className="bg-white rounded-lg shadow p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">Matters</h2>

          {/* create form */}
          <div className="flex flex-wrap gap-2 mb-4">
            <input
              className="border rounded px-3 py-1 text-sm flex-1 min-w-[120px]"
              placeholder="Client ID"
              value={matterClientId}
              onChange={(e) => setMatterClientId(e.target.value)}
            />
            <input
              className="border rounded px-3 py-1 text-sm flex-1 min-w-[80px]"
              placeholder="Code"
              value={matterCode}
              onChange={(e) => setMatterCode(e.target.value)}
            />
            <input
              className="border rounded px-3 py-1 text-sm flex-1 min-w-[160px]"
              placeholder="Matter name"
              value={matterName}
              onChange={(e) => setMatterName(e.target.value)}
            />
            <select
              className="border rounded px-3 py-1 text-sm"
              value={matterType}
              onChange={(e) => setMatterType(e.target.value)}
            >
              <option value="corporate">Corporate</option>
              <option value="litigation">Litigation</option>
              <option value="conveyancing">Conveyancing</option>
              <option value="probate">Probate</option>
            </select>
            <button
              onClick={handleCreateMatter}
              className="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700"
            >
              Add Matter
            </button>
          </div>

          {/* table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-500">
                  <th className="py-2 pr-4">ID</th>
                  <th className="py-2 pr-4">Code</th>
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Opened</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {matters.map((m) => (
                  <tr key={m.id} className="border-b last:border-0">
                    <td className="py-2 pr-4">{m.id}</td>
                    <td className="py-2 pr-4">{m.code ?? "-"}</td>
                    <td className="py-2 pr-4 font-medium">{m.name}</td>
                    <td className="py-2 pr-4 capitalize">{m.matter_type}</td>
                    <td className="py-2 pr-4">{m.opened_date ?? "-"}</td>
                    <td className="py-2">
                      {m.closed_date ? (
                        <span className="text-xs bg-slate-200 text-slate-600 px-2 py-0.5 rounded">
                          Closed
                        </span>
                      ) : (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                          Open
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
                {matters.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-4 text-center text-slate-400">
                      No matters found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* ---------- WIP Aging ---------- */}
        <section className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">WIP Aging Summary</h2>
          {wip ? (
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">0 - 30 days</dt>
                <dd className="font-medium">R {Number(wip.buckets_0_30).toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">31 - 60 days</dt>
                <dd className="font-medium">R {Number(wip.buckets_31_60).toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">61 - 90 days</dt>
                <dd className="font-medium">R {Number(wip.buckets_61_90).toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">90+ days</dt>
                <dd className="font-medium text-red-600">
                  R {Number(wip.buckets_over_90).toLocaleString()}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="text-slate-400 text-sm">Loading...</p>
          )}
        </section>

        {/* ---------- Time Entry + Timer ---------- */}
        <section className="bg-white rounded-lg shadow p-6 lg:col-span-3">
          <h2 className="text-lg font-semibold mb-4">Time Entry</h2>

          <div className="flex flex-wrap items-end gap-4">
            {/* matter select */}
            <div>
              <label className="block text-xs text-slate-500 mb-1">Matter</label>
              <select
                className="border rounded px-3 py-1 text-sm w-48"
                value={teMatterId}
                onChange={(e) => setTeMatterId(e.target.value)}
              >
                <option value="">-- select --</option>
                {matters.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.code ?? m.id} - {m.name}
                  </option>
                ))}
              </select>
            </div>

            {/* description */}
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs text-slate-500 mb-1">Description</label>
              <input
                className="border rounded px-3 py-1 text-sm w-full"
                placeholder="Work performed..."
                value={teDescription}
                onChange={(e) => setTeDescription(e.target.value)}
              />
            </div>

            {/* billable toggle */}
            <label className="flex items-center gap-1 text-sm cursor-pointer select-none">
              <input
                type="checkbox"
                checked={teBillable}
                onChange={(e) => setTeBillable(e.target.checked)}
              />
              Billable
            </label>

            {/* timer display */}
            <div className="text-2xl font-mono tabular-nums w-28 text-center">
              {fmtDuration(elapsed)}
            </div>

            {/* timer buttons */}
            {!timerRunning ? (
              <button
                onClick={startTimer}
                className="bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700"
              >
                Start
              </button>
            ) : (
              <button
                onClick={stopTimer}
                className="bg-red-600 text-white px-4 py-1.5 rounded text-sm hover:bg-red-700"
              >
                Stop
              </button>
            )}

            <button
              onClick={resetTimer}
              className="border border-slate-300 text-slate-600 px-4 py-1.5 rounded text-sm hover:bg-slate-100"
            >
              Reset
            </button>

            <button
              onClick={handleSubmitTime}
              disabled={!timerStart || timerRunning}
              className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Submit
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
