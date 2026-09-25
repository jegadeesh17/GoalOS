import React, { useState, useEffect, useMemo } from 'react';
import { AnalyticsDashboardData, goalOSApi } from '../api/client';
import { PageHeader } from './PageHeader';
import {
  TrendingUp,
  Clock,
  Moon,
  Smile,
  AlertTriangle,
  CheckCircle2,
  BookOpen,
  Activity,
  Hourglass
} from 'lucide-react';

interface Insight {
  kind: 'healthy' | 'warning';
  title: string;
  body?: string;
  items?: { name: string; count: number }[];
}

const DEFERRAL_TITLE = /^Repeated Task Deferral:\s*"(.+)"$/i;
const VISIBLE_INSIGHTS = 3;
const VISIBLE_SCORE_ROWS = 10;

/** Momentum first, every postponed task folded into one card, then the rest. */
const buildInsights = (patterns: any[]): Insight[] => {
  const healthy: Insight[] = [];
  const warnings: Insight[] = [];
  const deferred: { name: string; count: number }[] = [];

  for (const pattern of patterns) {
    const title: string = pattern.title || pattern.name || 'Pattern';
    const body: string = pattern.description || pattern.message || '';
    const deferral = DEFERRAL_TITLE.exec(title);
    if (deferral) {
      const count = /^(\d+)x/.exec(body);
      deferred.push({ name: deferral[1], count: count ? Number(count[1]) : 1 });
      continue;
    }
    const isWarning = pattern.pattern_type === 'warning' || pattern.level === 'warning';
    (isWarning ? warnings : healthy).push({ kind: isWarning ? 'warning' : 'healthy', title, body });
  }

  const grouped: Insight[] = deferred.length
    ? [
        {
          kind: 'warning',
          title: 'Tasks you keep postponing',
          body: 'Give each one a 15-minute first step and make it the first task of tomorrow.',
          items: deferred.sort((a, b) => b.count - a.count),
        },
      ]
    : [];

  return [...healthy, ...grouped, ...warnings];
};

export const AnalyticsView: React.FC = () => {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllInsights, setShowAllInsights] = useState(false);
  const [showAllScores, setShowAllScores] = useState(false);

  useEffect(() => {
    goalOSApi.getAnalyticsDashboard()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load analytics dashboard:', err);
        setError('Analytics couldn’t load. Check that GoalOS is running, then open this tab again.');
        setLoading(false);
      });
  }, []);

  const insights = useMemo(() => buildInsights(data?.patterns || []), [data]);

  const header = <PageHeader title="Analytics" subtitle="How your recent days have been going." />;

  if (loading) {
    return (
      <div className="space-y-6">
        {header}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5 motion-safe:animate-pulse" aria-hidden="true">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-28 bg-white/60 rounded-3xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        {header}
        <div className="glass-panel rounded-3xl p-8 text-center text-sm text-slate-600">{error || 'No analytics yet.'}</div>
      </div>
    );
  }

  const stats = [
    { label: 'Days logged', value: `${data.total_logs}`, unit: 'days', note: 'Recent journal entries', icon: BookOpen },
    { label: 'Deep work', value: `${data.avg_deep_work_hours}`, unit: 'hrs', note: 'Average focused hours per day', icon: Clock },
    { label: 'Sleep', value: `${data.avg_sleep_hours}`, unit: 'hrs', note: 'Average per night · aim for 7.5–8', icon: Moon },
    { label: 'Morning mood', value: `${data.avg_morning_mood}`, unit: '/ 5', note: 'How mornings have felt', icon: Smile },
  ];

  const visibleInsights = showAllInsights ? insights : insights.slice(0, VISIBLE_INSIGHTS);
  const visibleScores = showAllScores ? data.recent_scores : data.recent_scores.slice(0, VISIBLE_SCORE_ROWS);

  return (
    <div className="space-y-6">
      {header}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="glass-panel rounded-3xl p-4 sm:p-5 shadow-forest">
              <p className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                <Icon className="w-3.5 h-3.5 text-emerald-700" />
                {stat.label}
              </p>
              <p className="text-2xl font-bold text-slate-900 mt-1.5 tabular-nums">
                {stat.value} <span className="text-sm font-semibold text-slate-500">{stat.unit}</span>
              </p>
              <p className="text-xs text-slate-500 mt-0.5">{stat.note}</p>
            </div>
          );
        })}
      </div>

      {insights.length > 0 && (
        <section className="glass-panel rounded-3xl p-6 sm:p-7 shadow-forest" aria-labelledby="insights-title">
          <h2 id="insights-title" className="font-bold text-sm text-slate-900 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-700" />
            Patterns from your recent days
          </h2>

          <ul className="mt-2 divide-y divide-emerald-100/70">
            {visibleInsights.map((insight, idx) => (
              <li key={`${insight.title}-${idx}`} className="flex items-start gap-3 py-4">
                {insight.kind === 'healthy' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                ) : insight.items ? (
                  <Hourglass className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                )}
                <div className="min-w-0 max-w-3xl">
                  <h3 className="text-sm font-semibold text-slate-900">{insight.title}</h3>
                  {insight.items && (
                    <ul className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-sm text-slate-800">
                      {insight.items.map((item) => (
                        <li key={item.name}>
                          {item.name} <span className="text-slate-500 tabular-nums">×{item.count}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {insight.body && <p className="text-sm text-slate-600 mt-1 leading-relaxed">{insight.body}</p>}
                </div>
              </li>
            ))}
          </ul>

          {insights.length > VISIBLE_INSIGHTS && (
            <button
              type="button"
              onClick={() => setShowAllInsights(!showAllInsights)}
              className="mt-1 text-xs font-semibold text-emerald-800 hover:text-emerald-950 cursor-pointer"
            >
              {showAllInsights ? 'Show fewer' : `Show all ${insights.length}`}
            </button>
          )}
        </section>
      )}

      <section className="glass-panel rounded-3xl p-6 sm:p-7 space-y-3.5 shadow-forest" aria-labelledby="scores-title">
        <div>
          <h2 id="scores-title" className="font-bold text-sm text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-700" />
            Daily scores
          </h2>
          <p className="text-xs text-slate-600 mt-0.5 max-w-2xl">
            Calculated from task completion, deep work, sleep and goal alignment.
          </p>
        </div>

        {data.recent_scores.length === 0 ? (
          <p className="text-sm text-slate-600 py-2">No scores yet. They appear after your first few journal entries.</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-emerald-100 text-slate-600 font-semibold">
                    <th className="pb-2.5 pr-4">Date</th>
                    <th className="pb-2.5 px-3">Goal alignment</th>
                    <th className="pb-2.5 px-3">Consistency</th>
                    <th className="pb-2.5 px-3">Health</th>
                    <th className="pb-2.5 px-3">Productivity</th>
                    <th className="pb-2.5 pl-3 text-right">Overall</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-emerald-50/80">
                  {visibleScores.map((s: any, idx: number) => (
                    <tr key={idx} className="text-slate-700 tabular-nums">
                      <td className="py-2.5 pr-4 font-semibold text-slate-900">{s.date}</td>
                      <td className="py-2.5 px-3">{Math.round(s.goal_alignment_score || 0)}%</td>
                      <td className="py-2.5 px-3">{Math.round(s.consistency_score || 0)}%</td>
                      <td className="py-2.5 px-3">{Math.round(s.health_score || 0)}%</td>
                      <td className="py-2.5 px-3">{Math.round(s.productivity_score || 0)}%</td>
                      <td className="py-2.5 pl-3 text-right font-bold text-emerald-800">
                        {Math.round(s.overall_growth_score || 0)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.recent_scores.length > VISIBLE_SCORE_ROWS && (
              <button
                type="button"
                onClick={() => setShowAllScores(!showAllScores)}
                className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 cursor-pointer"
              >
                {showAllScores ? 'Show fewer days' : `Show all ${data.recent_scores.length} days`}
              </button>
            )}
          </>
        )}
      </section>
    </div>
  );
};
