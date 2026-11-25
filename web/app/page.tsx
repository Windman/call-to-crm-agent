"use client";

import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

// Зеркало Pydantic-моделей из agent.py
type ToolStep = { tool: string; args: Record<string, unknown>; result: string; is_error: boolean };
type AgentRun = { steps: ToolStep[]; report: string; model_calls: number };

export default function Home() {
  const [transcript, setTranscript] = useState("");
  const [run, setRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    setLoading(true);
    setError(null);
    setRun(null);
    try {
      const response = await fetch(`${API_URL}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });

      if (!response.ok) {
        setError(`HTTP ${response.status}: ${await response.text()}`);
      } else {
        // Put state → React re-render the page
        setRun((await response.json()) as AgentRun);
      }
    } catch (e) {
      // CORS, API is not running etc
      setError(`Request failed: ${String(e)} (is the API running? see the browser console)`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl space-y-4 p-8">
      <h1 className="text-2xl font-semibold">Call-to-CRM Agent</h1>

      <textarea
        value={transcript}
        onChange={(e) => setTranscript(e.target.value)}
        rows={10}
        placeholder="Paste a call transcript…"
        className="w-full rounded border p-2 font-mono text-sm"
      />

      <button
        onClick={handleRun}
        disabled={loading || !transcript.trim()}
        className="rounded bg-black px-4 py-2 text-white disabled:opacity-40"
      >
        {loading ? "Running… (~20 s)" : "Run"}
      </button>

      {error && (
        <div className="rounded border border-red-500 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {run && (
        <section className="space-y-3">
          <p className="text-sm text-gray-500">
            Steps: {run.steps.length} · model calls: {run.model_calls}
          </p>

          <ol className="space-y-3">
            {run.steps.map((step, i) => (
              <li
                key={i}
                className={`rounded border p-3 ${step.is_error ? "border-red-500 bg-red-50" : "border-gray-300"}`}
              >
                <div className="font-mono font-semibold">
                  {i + 1}. {step.tool}
                  {step.is_error && <span className="ml-2 text-red-600">error</span>}
                </div>
                <pre className="mt-2 overflow-x-auto text-xs">{JSON.stringify(step.args, null, 2)}</pre>
                <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-gray-600">{step.result}</pre>
              </li>
            ))}
          </ol>

          <h2 className="text-lg font-semibold">Report</h2>
          <pre className="whitespace-pre-wrap rounded border p-3 text-sm">{run.report}</pre>
        </section>
      )}
    </main>
  );
}
