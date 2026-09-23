import React, { useState } from 'react';
import { LifeSummary, YearProductivityData } from '../api/client';
import { Hourglass, CalendarDays, TrendingUp, Flame, ArrowRightLeft } from 'lucide-react';

interface LifeProgressBannerProps {
  summary: LifeSummary | null;
  yearSummary?: YearProductivityData | null;
  loading: boolean;
}

export const LifeProgressBanner: React.FC<LifeProgressBannerProps> = ({
  summary,
  yearSummary,
  loading,
}) => {
  const [perspective, setPerspective] = useState<'year' | 'lifespan'>('year');

  if (loading || (!summary && !yearSummary)) {
    return (
      <div className="glass-panel rounded-3xl p-6 animate-pulse">
        <div className="h-5 bg-slate-100 rounded-full w-1/3 mb-4"></div>
        <div className="h-4 bg-slate-100 rounded-full w-full"></div>
      </div>
    );
  }

  // If yearSummary is not available, default to lifespan
  const showYearView = perspective === 'year' && yearSummary;

  return (
    <div className="glass-panel rounded-3xl p-6 sm:p-7 relative overflow-hidden shadow-forest transition-all border border-emerald-100/70">
      {/* ---------------- PERSPECTIVE 1: Year Productivity Horizon (Default) ---------------- */}
      {showYearView && yearSummary && (
        <>
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Left Year Stats */}
            <div className="space-y-1">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center space-x-1.5 bg-emerald-50/90 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200/70 shadow-forest-xs text-xs font-semibold">
                  <Flame className="w-3 h-3 text-emerald-700 fill-emerald-600" />
                  <span>{yearSummary.year} Productivity Horizon</span>
                </div>

                {/* Perspective Switcher */}
                {summary && (
                  <button
                    onClick={() => setPerspective('lifespan')}
                    className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-emerald-800 transition-colors font-medium cursor-pointer"
                    title="Switch to 70-Year Horizon"
                  >
                    <ArrowRightLeft className="w-3 h-3" />
                    <span>70-Year View</span>
                  </button>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight flex items-baseline gap-2 pt-1">
                <span>{yearSummary.productive_days_count} Productive Days</span>
                <span className="text-sm font-normal text-slate-500">
                  of {yearSummary.days_elapsed} days elapsed
                </span>
              </h1>

              <p className="text-sm text-slate-600 font-normal pt-0.5">
                Day <strong className="text-slate-900 font-semibold">{yearSummary.days_elapsed}</strong> of{' '}
                <strong className="text-slate-900 font-semibold">{yearSummary.total_days}</strong> &middot;{' '}
                <strong className="text-slate-900 font-semibold">{yearSummary.days_remaining} Days Remaining</strong> in {yearSummary.year}
              </p>
            </div>

            {/* Right Stats Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="glass-card-interactive rounded-2xl p-3.5 border border-emerald-100/60 bg-gradient-to-br from-white to-emerald-50/40">
                <div className="flex items-center space-x-1.5 text-xs text-emerald-800 font-medium">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-700" />
                  <span>Productivity Rate</span>
                </div>
                <p className="text-xl font-bold text-emerald-700 mt-1">
                  {yearSummary.productivity_rate}%
                </p>
              </div>

              <div className="glass-card-interactive rounded-2xl p-3.5 border border-emerald-100/60 bg-gradient-to-br from-white to-amber-50/40">
                <div className="flex items-center space-x-1.5 text-xs text-amber-800 font-medium">
                  <Flame className="w-3.5 h-3.5 text-amber-600 fill-amber-500" />
                  <span>Active Streak</span>
                </div>
                <p className="text-xl font-bold text-amber-800 mt-1">
                  {yearSummary.current_streak} <span className="text-xs font-normal text-amber-700">Days (Best: {yearSummary.best_streak})</span>
                </p>
              </div>

              <div className="glass-card-interactive rounded-2xl p-3.5 border border-emerald-100/60 col-span-2 sm:col-span-1 bg-gradient-to-br from-white to-teal-50/40">
                <div className="flex items-center space-x-1.5 text-xs text-teal-800 font-medium">
                  <CalendarDays className="w-3.5 h-3.5 text-teal-700" />
                  <span>Days Remaining</span>
                </div>
                <p className="text-xl font-bold text-teal-800 mt-1">{yearSummary.days_remaining}</p>
              </div>
            </div>
          </div>

          {/* Year Horizon Progress Bar */}
          <div className="mt-5 pt-4 border-t border-emerald-100/60">
            <div className="flex justify-between text-xs font-medium text-slate-500 mb-1.5">
              <span className="flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                <span>Jan 1, {yearSummary.year}</span>
              </span>
              <span className="text-emerald-800 font-semibold">
                {Math.round((yearSummary.days_elapsed / yearSummary.total_days) * 100)}% of Year Elapsed
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
                <span>Dec 31, {yearSummary.year}</span>
              </span>
            </div>

            {/* Dual Progress Bar: Year Elapsed with Productive Fill */}
            <div className="w-full bg-slate-100/90 rounded-full h-2.5 overflow-hidden p-0.5 border border-emerald-100/80 shadow-inner relative">
              {/* Year Elapsed Sub-track */}
              <div
                className="bg-emerald-100/80 h-full rounded-full transition-all duration-500 absolute top-0.5 left-0.5"
                style={{ width: `${Math.min(100, (yearSummary.days_elapsed / yearSummary.total_days) * 100)}%` }}
              ></div>
              {/* Productive Days Fill */}
              <div
                className="bg-gradient-to-r from-emerald-600 via-teal-500 to-emerald-500 h-full rounded-full transition-all duration-700 ease-out shadow-xs relative z-10"
                style={{ width: `${Math.min(100, (yearSummary.productive_days_count / yearSummary.total_days) * 100)}%` }}
              ></div>
            </div>
          </div>
        </>
      )}

      {/* ---------------- PERSPECTIVE 2: 70-Year Lifespan Memento Mori (Secondary) ---------------- */}
      {(!showYearView || !yearSummary) && summary && (
        <>
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Left Lifespan Stats */}
            <div className="space-y-1">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center space-x-1.5 bg-emerald-50/90 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200/70 shadow-forest-xs text-xs font-semibold">
                  <Hourglass className="w-3 h-3 text-emerald-700" />
                  <span>70-Year Life Horizon</span>
                </div>

                {/* Perspective Switcher */}
                {yearSummary && (
                  <button
                    onClick={() => setPerspective('year')}
                    className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-emerald-800 transition-colors font-medium cursor-pointer"
                    title="Switch to Year Productivity"
                  >
                    <ArrowRightLeft className="w-3 h-3" />
                    <span>Year Productivity</span>
                  </button>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight flex items-baseline gap-1.5 pt-1">
                <span>Week {summary.weeks_lived.toLocaleString()}</span>
                <span className="text-sm font-normal text-slate-500">of {summary.total_weeks.toLocaleString()}</span>
              </h1>

              <p className="text-sm text-slate-600 font-normal pt-0.5">
                Age <strong className="text-slate-900 font-semibold">{summary.age_years}</strong> &middot; Target Horizon:{' '}
                <strong className="text-slate-900 font-semibold">{summary.target_age} Years</strong>
              </p>
            </div>

            {/* Right Stats Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="glass-card-interactive rounded-2xl p-3.5 border border-emerald-100/60">
                <div className="flex items-center space-x-1.5 text-xs text-slate-600 font-medium">
                  <Hourglass className="w-3.5 h-3.5 text-emerald-700" />
                  <span>Weeks Remaining</span>
                </div>
                <p className="text-xl font-bold text-slate-900 mt-1">
                  {summary.weeks_remaining.toLocaleString()}
                </p>
              </div>

              <div className="glass-card-interactive rounded-2xl p-3.5 border border-emerald-100/60 bg-gradient-to-br from-white to-emerald-50/40">
                <div className="flex items-center space-x-1.5 text-xs text-emerald-800 font-medium">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-700" />
                  <span>Life Elapsed</span>
                </div>
                <p className="text-xl font-bold text-emerald-700 mt-1">{summary.percentage_lived}%</p>
              </div>

              <div className="glass-card-interactive rounded-2xl p-3.5 border border-emerald-100/60 col-span-2 sm:col-span-1 bg-gradient-to-br from-white to-amber-50/40">
                <div className="flex items-center space-x-1.5 text-xs text-amber-800 font-medium">
                  <CalendarDays className="w-3.5 h-3.5 text-amber-700" />
                  <span>Target Year</span>
                </div>
                <p className="text-xl font-bold text-amber-800 mt-1">{summary.target_date.split('-')[0]}</p>
              </div>
            </div>
          </div>

          {/* Horizon Progress Bar */}
          <div className="mt-5 pt-4 border-t border-emerald-100/60">
            <div className="flex justify-between text-xs font-medium text-slate-500 mb-1.5">
              <span className="flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                <span>Birth: {summary.birth_date}</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
                <span>Age {summary.target_age} Horizon</span>
              </span>
            </div>

            <div className="w-full bg-slate-100/90 rounded-full h-2.5 overflow-hidden p-0.5 border border-emerald-100/80 shadow-inner">
              <div
                className="bg-gradient-to-r from-emerald-600 via-teal-500 to-earth-amber h-full rounded-full transition-all duration-700 ease-out shadow-xs"
                style={{ width: `${Math.min(100, summary.percentage_lived)}%` }}
              ></div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
