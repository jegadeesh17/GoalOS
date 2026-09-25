import React, { useState } from 'react';
import { TelemetrySpan, TelemetrySummary, goalOSApi } from '../api/client';
import { ChevronDown, Cpu } from 'lucide-react';

const formatCount = (value: number): string => (value || 0).toLocaleString();

const formatLatency = (ms: number): string => {
  const value = ms || 0;
  return value >= 1000 ? `${(value / 1000).toFixed(2)}s` : `${Math.round(value)}ms`;
};

const formatCostUsd = (usd: number): string => {
  const value = usd || 0;
  // Sub-cent spend is common on small local models; keep it visible instead of rounding to $0.00.
  return value > 0 && value < 0.01 ? '<$0.01' : `$${value.toFixed(2)}`;
};

/** AI observability (tokens, spend, latency), tucked away until asked for. */
export const DiagnosticsPanel: React.FC = () => {
  const [requested, setRequested] = useState(false);
  const [telemetry, setTelemetry] = useState<TelemetrySummary | null>(null);
  const [traces, setTraces] = useState<TelemetrySpan[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleToggle = (e: React.SyntheticEvent<HTMLDetailsElement>) => {
    if (!e.currentTarget.open || requested) return;
    setRequested(true);
    Promise.all([goalOSApi.getTelemetrySummary(30), goalOSApi.getTelemetryTraces(15)])
      .then(([summary, recentTraces]) => {
        setTelemetry(summary);
        setTraces(recentTraces);
      })
      .catch((err) => {
        console.error('Failed to load AI telemetry:', err);
        setError('Diagnostics are unavailable right now.');
      });
  };

  const stats = telemetry
    ? [
        { label: 'Calls', value: formatCount(telemetry.total_calls) },
        { label: 'Prompt tokens', value: formatCount(telemetry.prompt_tokens) },
        { label: 'Completion tokens', value: formatCount(telemetry.completion_tokens) },
        { label: 'Estimated cost', value: formatCostUsd(telemetry.total_cost_usd) },
        { label: 'Latency', value: formatLatency(telemetry.avg_latency_ms), note: `p95 ${formatLatency(telemetry.p95_latency_ms)}` },
      ]
    : [];

  return (
    <details className="glass-panel rounded-3xl shadow-forest group" onToggle={handleToggle}>
      <summary className="flex items-center justify-between gap-4 p-6 sm:p-7 cursor-pointer rounded-3xl">
        <span>
          <span className="flex items-center gap-2 font-bold text-sm text-slate-900">
            <Cpu className="w-4 h-4 text-emerald-700" />
            Diagnostics
          </span>
          <span className="block text-xs text-slate-600 mt-0.5">AI calls, tokens, estimated cost and latency over the last 30 days.</span>
        </span>
        <ChevronDown className="w-4 h-4 text-slate-500 transition-transform group-open:rotate-180" />
      </summary>

      <div className="px-6 sm:px-7 pb-7 space-y-5">
        {error ? (
          <p className="text-sm text-slate-600">{error}</p>
        ) : !telemetry ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : telemetry.total_calls === 0 ? (
          <p className="text-sm text-slate-600">No AI calls yet. Numbers appear once the coach runs with remote AI turned on.</p>
        ) : (
          <>
            <dl className="grid grid-cols-2 lg:grid-cols-5 gap-x-6 gap-y-4">
              {stats.map((stat) => (
                <div key={stat.label}>
                  <dt className="text-xs font-medium text-slate-600">{stat.label}</dt>
                  <dd className="text-lg font-bold text-slate-900 tabular-nums mt-0.5">{stat.value}</dd>
                  {stat.note && <dd className="text-xs text-slate-500 tabular-nums">{stat.note}</dd>}
                </div>
              ))}
            </dl>

            {traces.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-emerald-100 text-slate-600 font-semibold">
                      <th className="pb-2.5 pr-4">Span</th>
                      <th className="pb-2.5 px-3">Model</th>
                      <th className="pb-2.5 px-3">Tokens</th>
                      <th className="pb-2.5 px-3">Latency</th>
                      <th className="pb-2.5 pl-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-emerald-50/80">
                    {traces.map((span) => (
                      <tr key={span.id ?? span.trace_id} className="text-slate-700 tabular-nums">
                        <td className="py-2.5 pr-4 font-semibold text-slate-900">{span.span_name}</td>
                        <td className="py-2.5 px-3 truncate max-w-[14rem]" title={span.model}>
                          {span.model}
                        </td>
                        <td className="py-2.5 px-3">{formatCount(span.total_tokens)}</td>
                        <td className="py-2.5 px-3">{formatLatency(span.latency_ms)}</td>
                        <td className="py-2.5 pl-3 text-right">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full font-semibold ${
                              span.status === 'success' ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-900'
                            }`}
                            title={span.error_message || undefined}
                          >
                            {span.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </details>
  );
};
