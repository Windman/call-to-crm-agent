"use client";

import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

// Зеркало Pydantic-моделей из agent.py
type ToolStep = { tool: string; args: Record<string, unknown>; result: string; is_error: boolean };
type AgentRun = { steps: ToolStep[]; report: string; model_calls: number };

// Одно SSE-событие — текст из строк "event: ..." и "data: ...":
//   "event: step\ndata: {...}"  →  { event: "step", data: "{...}" }
function parseEvent(raw: string): { event: string; data: string } {
  let event = "message"; // имя по умолчанию в стандарте SSE, если строки "event:" нет
  let data = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event: ")) event = line.slice("event: ".length);
    else if (line.startsWith("data: ")) data += line.slice("data: ".length);
  }
  return { event, data };
}

// Читает тело ответа по мере поступления и вызывает onEvent для каждого ПОЛНОГО события.
// EventSource не подходит: он умеет только GET, а у нас POST с транскриптом в теле.
async function readEvents(body: ReadableStream<Uint8Array>, onEvent: (event: string, data: string) => void) {
  const reader = body.getReader();
  // Байты → текст 
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    // Ждём следующий кусок (≈ await stream.ReadAsync). done = сервер закрыл поток.
    const { value, done } = await reader.read();
    if (done) return;
    // stream: true — если русская буква (2 байта) разрезана между кусками, декодер дождётся второй половины
    buffer += decoder.decode(value, { stream: true });
    // Кусок сети ≠ событие: одно событие может прийти в двух кусках, два события — в одном.
    // События разделены пустой строкой; последняя часть может быть недописанной → оставляем в буфере.
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const { event, data } = parseEvent(part);
      onEvent(event, data);
    }
  }
}

export default function Home() {
  const [transcript, setTranscript] = useState("");
  // Шаги копятся по одному, пока агент работает
  const [steps, setSteps] = useState<ToolStep[]>([]);
  // Итог (отчёт, model_calls) — приходит последним событием "done"
  const [run, setRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    setLoading(true);
    setError(null);
    setSteps([]);
    setRun(null);
    try {
      const response = await fetch(`${API_URL}/runs/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });

      // Ошибки ДО начала потока (нет HUBSPOT_TOKEN, 422) по-прежнему приходят как JSON с detail
      if (!response.ok) {
        const responseJson = await response.json().catch(()=>null)
        const details = responseJson?.detail
        if (typeof  details === "string") {
            setError(`HTTP ${response.status}: ${details}`);
        } else {
            setError(`HTTP ${response.status}: ${response.statusText}`);
        }
      } else if (!response.body) {
        setError("Empty response body");
      } else {
        let finished = false;
        await readEvents(response.body, (event, data) => {
          if (event === "step") {
            const step = JSON.parse(data) as ToolStep;
            // Функциональное обновление: React передаёт актуальный список.
            // setSteps([...steps, step]) взял бы `steps` из момента клика — то есть [] — и каждый шаг затирал бы предыдущий.
            setSteps((prev) => [...prev, step]);
          } else if (event === "done") {
            setRun(JSON.parse(data) as AgentRun);
            finished = true;
          } else if (event === "error") {
            // Ошибка ПОСЛЕ начала потока: статус уже 200, поэтому она приходит событием
            const { detail } = JSON.parse(data) as { detail: string };
            setError(`Agent failed: ${detail}`);
            finished = true;
          }
        });
        // Поток закрылся без "done" и без "error" — например, упал сервер
        if (!finished) setError("The stream ended without a result (see the API terminal)");
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
        {loading ? `Running… (${steps.length} steps so far)` : "Run"}
      </button>

      {error && (
        <div className="rounded border border-red-500 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {/* Список показываем, как только пришёл первый шаг, не дожидаясь конца */}
      {(steps.length > 0 || run) && (
        <section className="space-y-3">
          <p className="text-sm text-gray-500">
            Steps: {steps.length}
            {run && <> · model calls: {run.model_calls}</>}
          </p>

          <ol className="space-y-3">
            {steps.map((step, i) => (
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
            {/* Пока агент работает — «заглушка» под следующий шаг */}
            {loading && (
              <li className="animate-pulse rounded border border-dashed border-gray-300 p-3 text-sm text-gray-400">
                Waiting for the next step…
              </li>
            )}
          </ol>

          {run && (
            <>
              <h2 className="text-lg font-semibold">Report</h2>
              <pre className="whitespace-pre-wrap rounded border p-3 text-sm">{run.report}</pre>
            </>
          )}
        </section>
      )}
    </main>
  );
}
