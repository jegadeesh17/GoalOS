import React from 'react';
import { LifeSummary } from '../api/client';
import { Hourglass, CalendarDays, TrendingUp } from 'lucide-react';

interface LifeProgressBannerProps {
  summary: LifeSummary | null;
  loading: boolean;
}

export const LifeProgressBanner: React.FC<LifeProgressBannerProps> = ({ summary, loading }) => {
  if (loading || !summary) {
    return (
      <div className="glass-panel rounded-3xl p-6 animate-pulse">
        <div className="h-6 bg-slate-100 rounded-full w-1/3 mb-4"></div>
        <div className="h-4 bg-slate-100 rounded-full w-full"></div>
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-3xl p-6 sm:p-7 relative overflow-hidden shadow-celestial transition-all border border-white/80">
      {/* Background Ambient Gradient Glow */}
      <div className="absolute -top-12 -right-12 w-64 h-64 bg-gradient-to-br from-indigo-200/50 via-purple-200/40 to-pink-200/30 rounded-full blur-3xl pointer-events-none -z-10"></div>
      <div className="absolute -bottom-12 -left-12 w-64 h-64 bg-gradient-to-tr from-amber-100/60 via-indigo-100/40 to-cyan-100/40 rounded-full blur-3xl pointer-events-none -z-10"></div>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        {/* Left Lifespan Stats */}
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-indigo-700">
            <span className="flex items-center space-x-1.5 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100 shadow-sm font-extrabold">
              <Hourglass className="w-3.5 h-3.5 text-indigo-600" />
              <span>70-Year Life Horizon</span>
            </span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight flex items-baseline gap-2">
            <span>Week {summary.weeks_lived.toLocaleString()}</span>
            <span className="text-base sm:text-lg font-medium text-slate-400">of {summary.total_weeks.toLocaleString()}</span>
          </h1>

          <p className="text-sm text-slate-600 font-medium">
            You are <strong className="text-indigo-950 font-bold">{summary.age_years} years old</strong>. You have lived{' '}
            <strong className="text-indigo-700 font-bold">{summary.percentage_lived}%</strong> of your 70-year calendar.
          </p>
        </div>

        {/* Right Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5">
          <div className="glass-card-interactive rounded-2xl p-3.5 border border-white/80">
            <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-semibold">
              <Hourglass className="w-3.5 h-3.5 text-indigo-600" />
              <span>Weeks Remaining</span>
            </div>
            <p className="text-2xl font-black text-slate-900 mt-1">{summary.weeks_remaining.toLocaleString()}</p>
          </div>

          <div className="glass-card-interactive rounded-2xl p-3.5 border border-white/80 bg-gradient-to-br from-white to-emerald-50/40">
            <div className="flex items-center space-x-1.5 text-xs text-emerald-700 font-semibold">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
              <span>Life Elapsed</span>
            </div>
            <p className="text-2xl font-black text-emerald-600 mt-1">{summary.percentage_lived}%</p>
          </div>

          <div className="glass-card-interactive rounded-2xl p-3.5 border border-white/80 col-span-2 sm:col-span-1 bg-gradient-to-br from-white to-amber-50/40">
            <div className="flex items-center space-x-1.5 text-xs text-amber-700 font-semibold">
              <CalendarDays className="w-3.5 h-3.5 text-amber-500" />
              <span>Target Year</span>
            </div>
            <p className="text-2xl font-black text-amber-700 mt-1">{summary.target_date.split('-')[0]}</p>
          </div>
        </div>
      </div>

      {/* Luminous Gradient Horizon Bar */}
      <div className="mt-6 pt-5 border-t border-indigo-100/60">
        <div className="flex justify-between text-xs font-semibold text-slate-500 mb-2">
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
            <span>Birth: {summary.birth_date}</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            <span>Age {summary.target_age} Horizon</span>
          </span>
        </div>

        <div className="w-full bg-slate-100/80 rounded-full h-3.5 overflow-hidden p-0.5 border border-indigo-100/80 shadow-inner">
          <div
            className="bg-gradient-to-r from-indigo-600 via-purple-500 via-pink-400 to-amber-400 h-full rounded-full transition-all duration-1000 ease-out shadow-sm"
            style={{ width: `${Math.min(100, summary.percentage_lived)}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};
