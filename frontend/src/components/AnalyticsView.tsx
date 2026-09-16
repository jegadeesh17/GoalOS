import React, { useState, useEffect } from 'react';
import { AnalyticsDashboardData, TelemetrySpan, TelemetrySummary, goalOSApi } from '../api/client';
import {
  TrendingUp,
  Clock,
  Moon,
  Smile,
  AlertTriangle,
  CheckCircle2,
  Flame,
  Activity,
  BarChart3,
  Cpu,
  Coins,
  Gauge,
  Timer
} from 'lucide-react';

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

export const AnalyticsView: React.FC = () => {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetrySummary | null>(null);
  const [traces, setTraces] = useState<TelemetrySpan[]>([]);

  useEffect(() => {
    goalOSApi.getAnalyticsDashboard()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load analytics dashboard:', err);
        setError('Unable to load analytics data right now.');
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    // Telemetry is supplementary: failures here must never blank the analytics page.
    Promise.all([goalOSApi.getTelemetrySummary(30), goalOSApi.getTelemetryTraces(15)])
      .then(([summary, recentTraces]) => {
        setTelemetry(summary);
        setTraces(recentTraces);
      })
      .catch((err) => {
        console.error('Failed to load AI telemetry:', err);
      });
  }, []);

  if (loading) {
    return (
      <div className="glass-panel rounded-3xl p-8 animate-pulse space-y-6">
        <div className="h-5 bg-slate-100 rounded-full w-1/4"></div>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="h-28 bg-slate-50/60 rounded-2xl"></div>
          <div className="h-28 bg-slate-50/60 rounded-2xl"></div>
          <div className="h-28 bg-slate-50/60 rounded-2xl"></div>
          <div className="h-28 bg-slate-50/60 rounded-2xl"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-panel rounded-3xl p-8 text-center text-xs text-slate-500">
        {error || 'No analytics data available.'}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel rounded-3xl p-6 sm:p-7 shadow-forest border border-emerald-100/70">
        <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-forest-700 mb-1">
          <span className="flex items-center space-x-1 bg-emerald-50/90 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200/70 shadow-forest-xs font-semibold">
            <BarChart3 className="w-3.5 h-3.5 text-emerald-700" />
            <span>Progress & Metrics</span>
          </span>
        </div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Progress & Analytics</h2>
        <p className="text-xs text-slate-500 mt-0.5 font-normal">
          Track daily consistency, deep work pacing, and goal progress over time.
        </p>
      </div>

      {/* 4 Top Pods */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* Logged Days */}
        <div className="glass-card-interactive rounded-3xl p-4 border border-emerald-100/70 shadow-forest">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Logged Days</span>
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-earth-amber to-earth-clay text-white flex items-center justify-center shadow-forest-xs">
              <Flame className="w-3.5 h-3.5" />
            </div>
          </div>
          <p className="text-xl font-bold text-slate-900 mt-1.5">{data.total_logs} Days</p>
          <p className="text-xs text-slate-400 mt-0.5 font-normal">Journal entries recorded</p>
        </div>

        {/* Avg Deep Work */}
        <div className="glass-card-interactive rounded-3xl p-4 border border-emerald-100/70 shadow-forest">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Avg Deep Work</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-700 text-white flex items-center justify-center shadow-forest-xs">
              <Clock className="w-3.5 h-3.5" />
            </div>
          </div>
          <p className="text-xl font-bold text-emerald-800 mt-1.5">{data.avg_deep_work_hours} hrs</p>
          <p className="text-xs text-slate-400 mt-0.5 font-normal">Focused blocks per day</p>
        </div>

        {/* Avg Sleep */}
        <div className="glass-card-interactive rounded-3xl p-4 border border-emerald-100/70 shadow-forest">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Avg Sleep</span>
            <div className="w-8 h-8 rounded-xl bg-teal-700 text-white flex items-center justify-center shadow-forest-xs">
              <Moon className="w-3.5 h-3.5" />
            </div>
          </div>
          <p className="text-xl font-bold text-teal-800 mt-1.5">{data.avg_sleep_hours} hrs</p>
          <p className="text-xs text-slate-400 mt-0.5 font-normal">Target: 7.5 - 8.0 hrs</p>
        </div>

        {/* Vitality Mood */}
        <div className="glass-card-interactive rounded-3xl p-4 border border-emerald-100/70 shadow-forest">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Morning Mood</span>
            <div className="w-8 h-8 rounded-xl bg-forest-600 text-white flex items-center justify-center shadow-forest-xs">
              <Smile className="w-3.5 h-3.5" />
            </div>
          </div>
          <p className="text-xl font-bold text-forest-700 mt-1.5">{data.avg_morning_mood} / 5</p>
          <p className="text-xs text-slate-400 mt-0.5 font-normal">Subjective vitality rating</p>
        </div>
      </div>

      {/* Behavioral Patterns Engine */}
      {data.patterns && data.patterns.length > 0 && (
        <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-3.5 shadow-forest border border-emerald-100/70">
          <h3 className="font-bold text-sm text-slate-900 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-emerald-700" />
            <span>Detected Multi-Day Patterns</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.patterns.map((pattern: any, idx: number) => {
              const isWarning = pattern.pattern_type === 'warning' || pattern.level === 'warning';
              return (
                <div
                  key={idx}
                  className={`p-3.5 rounded-2xl border flex items-start space-x-2.5 text-xs transition-all ${
                    isWarning
                      ? 'bg-gradient-to-r from-amber-50 to-orange-50/50 border-amber-200 text-amber-950 shadow-forest-xs'
                      : 'bg-gradient-to-r from-emerald-50 to-teal-50/50 border-emerald-200 text-emerald-950 shadow-forest-xs'
                  }`}
                >
                  {isWarning ? (
                    <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h4 className="font-bold text-xs">{pattern.title || pattern.name || 'Pattern'}</h4>
                    <p className="text-slate-700 mt-0.5 leading-relaxed font-normal">{pattern.description || pattern.message || JSON.stringify(pattern)}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* AI Observability & APM */}
      {telemetry && (
        <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-3.5 shadow-forest border border-emerald-100/70">
          <div>
            <h3 className="font-bold text-sm text-slate-900 flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-emerald-700" />
              <span>AI Observability &amp; APM</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 font-normal">
              Token consumption, estimated spend, and latency across the last 30 days of coach calls.
            </p>
          </div>

          {telemetry.total_calls === 0 ? (
            <p className="text-xs text-slate-400 italic py-2">
              No AI calls recorded yet. Telemetry appears once the coach runs with remote AI enabled.
            </p>
          ) : (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                <div className="p-3.5 rounded-2xl bg-white/80 border border-emerald-100/70 shadow-forest-xs">
                  <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    <Activity className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Total Calls</span>
                  </div>
                  <p className="text-lg font-bold text-slate-900 mt-1.5">{formatCount(telemetry.total_calls)}</p>
                </div>

                <div className="p-3.5 rounded-2xl bg-white/80 border border-emerald-100/70 shadow-forest-xs">
                  <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    <BarChart3 className="w-3.5 h-3.5 text-teal-700" />
                    <span>Prompt Tokens</span>
                  </div>
                  <p className="text-lg font-bold text-teal-800 mt-1.5">{formatCount(telemetry.prompt_tokens)}</p>
                </div>

                <div className="p-3.5 rounded-2xl bg-white/80 border border-emerald-100/70 shadow-forest-xs">
                  <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    <BarChart3 className="w-3.5 h-3.5 text-forest-600" />
                    <span>Completion Tokens</span>
                  </div>
                  <p className="text-lg font-bold text-forest-700 mt-1.5">{formatCount(telemetry.completion_tokens)}</p>
                </div>

                <div className="p-3.5 rounded-2xl bg-white/80 border border-emerald-100/70 shadow-forest-xs">
                  <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    <Coins className="w-3.5 h-3.5 text-earth-amber" />
                    <span>Est. Cost</span>
                  </div>
                  <p className="text-lg font-bold text-slate-900 mt-1.5">{formatCostUsd(telemetry.total_cost_usd)}</p>
                </div>

                <div className="p-3.5 rounded-2xl bg-white/80 border border-emerald-100/70 shadow-forest-xs">
                  <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    <Gauge className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Latency</span>
                  </div>
                  <p className="text-lg font-bold text-emerald-800 mt-1.5">{formatLatency(telemetry.avg_latency_ms)}</p>
                  <p className="text-xs text-slate-400 mt-0.5 font-normal flex items-center space-x-1">
                    <Timer className="w-3 h-3" />
                    <span>P95 {formatLatency(telemetry.p95_latency_ms)}</span>
                  </p>
                </div>
              </div>

              {traces.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-emerald-100 text-slate-500 font-semibold uppercase tracking-wider">
                        <th className="pb-2.5 pr-4">Span</th>
                        <th className="pb-2.5 px-3">Model</th>
                        <th className="pb-2.5 px-3">Tokens</th>
                        <th className="pb-2.5 px-3">Latency</th>
                        <th className="pb-2.5 pl-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-emerald-50/80">
                      {traces.map((span) => (
                        <tr key={span.id ?? span.trace_id} className="hover:bg-white/90 font-mono text-slate-700 transition-colors">
                          <td className="py-3 pr-4 font-sans font-semibold text-slate-900">{span.span_name}</td>
                          <td className="py-3 px-3 truncate max-w-[14rem]" title={span.model}>{span.model}</td>
                          <td className="py-3 px-3">{formatCount(span.total_tokens)}</td>
                          <td className="py-3 px-3">{formatLatency(span.latency_ms)}</td>
                          <td className="py-3 pl-3 text-right">
                            <span
                              className={`inline-block px-2 py-0.5 rounded-full font-sans font-semibold border ${
                                span.status === 'success'
                                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                  : 'bg-amber-50 text-amber-900 border-amber-200'
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
      )}

      {/* Recent Scores Table */}
      <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-3.5 shadow-forest border border-emerald-100/70">
        <div>
          <h3 className="font-bold text-sm text-slate-900 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-emerald-700" />
            <span>Daily Execution Scores</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5 font-normal">
            Objective metrics calculated from your daily task completion, deep work, sleep, and goal alignment.
          </p>
        </div>

        {data.recent_scores.length === 0 ? (
          <p className="text-xs text-slate-400 italic py-2">No daily score records found yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-emerald-100 text-slate-500 font-semibold uppercase tracking-wider">
                  <th className="pb-2.5 pr-4">Date</th>
                  <th className="pb-2.5 px-3">Goal Alignment</th>
                  <th className="pb-2.5 px-3">Consistency</th>
                  <th className="pb-2.5 px-3">Health</th>
                  <th className="pb-2.5 px-3">Productivity</th>
                  <th className="pb-2.5 pl-3 text-right">Overall Growth</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-emerald-50/80">
                {data.recent_scores.map((s: any, idx: number) => (
                  <tr key={idx} className="hover:bg-white/90 font-mono text-slate-700 transition-colors">
                    <td className="py-3 pr-4 font-sans font-semibold text-slate-900">{s.date}</td>
                    <td className="py-3 px-3">{Math.round(s.goal_alignment_score || 0)}%</td>
                    <td className="py-3 px-3">{Math.round(s.consistency_score || 0)}%</td>
                    <td className="py-3 px-3">{Math.round(s.health_score || 0)}%</td>
                    <td className="py-3 px-3">{Math.round(s.productivity_score || 0)}%</td>
                    <td className="py-3 pl-3 text-right font-bold text-emerald-800">
                      {Math.round(s.overall_growth_score || 0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
