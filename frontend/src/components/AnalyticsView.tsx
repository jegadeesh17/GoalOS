import React, { useState, useEffect } from 'react';
import { AnalyticsDashboardData, goalOSApi } from '../api/client';
import { 
  TrendingUp, 
  Clock, 
  Moon, 
  Smile, 
  AlertTriangle, 
  CheckCircle2, 
  Flame,
  Activity,
  BarChart3
} from 'lucide-react';

export const AnalyticsView: React.FC = () => {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
