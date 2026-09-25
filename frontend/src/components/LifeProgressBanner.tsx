import React from 'react';
import { LifeSummary, YearProductivityData } from '../api/client';
import { Flame } from 'lucide-react';

interface LifeProgressBannerProps {
  summary: LifeSummary | null;
  yearSummary?: YearProductivityData | null;
  loading: boolean;
  perspective: 'year' | 'lifespan';
}

const Dot = () => <span className="text-slate-300 font-normal" aria-hidden="true"> · </span>;

/** A thin horizon: productive share in ink, elapsed share in mist, today as an amber sun. */
const HorizonBar: React.FC<{ elapsedPct: number; filledPct: number; label: string }> = ({ elapsedPct, filledPct, label }) => (
  <div role="img" aria-label={label} className="relative mt-4 h-1.5 rounded-full bg-white/80 ring-1 ring-inset ring-emerald-100">
    <div className="absolute inset-y-0 left-0 rounded-full bg-emerald-100" style={{ width: `${Math.min(100, elapsedPct)}%` }} />
    <div className="absolute inset-y-0 left-0 rounded-full bg-emerald-700" style={{ width: `${Math.min(100, filledPct)}%` }} />
    <span
      className="absolute top-1/2 w-2.5 h-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-400 ring-2 ring-white"
      style={{ left: `${Math.min(100, elapsedPct)}%` }}
    />
  </div>
);

export const LifeProgressBanner: React.FC<LifeProgressBannerProps> = ({ summary, yearSummary, loading, perspective }) => {
  if (loading || (!summary && !yearSummary)) {
    return (
      <div className="px-1 sm:px-2 space-y-4 motion-safe:animate-pulse" aria-hidden="true">
        <div className="h-8 bg-white/70 rounded-full w-2/3 max-w-xl" />
        <div className="h-1.5 bg-white/70 rounded-full w-full" />
      </div>
    );
  }

  if (perspective === 'year' && yearSummary) {
    const y = yearSummary;
    const elapsedPct = (y.days_elapsed / y.total_days) * 100;
    const productivePct = (y.productive_days_count / y.total_days) * 100;

    return (
      <section aria-label="Year horizon" className="px-1 sm:px-2">
        <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-2">
          <h1 className="font-serif font-medium text-[1.6rem] sm:text-[2rem] leading-tight tracking-[-0.015em] text-forest-950">
            Day {y.days_elapsed} of {y.total_days}
            <Dot />
            <span className="text-emerald-700">{y.productive_days_count} productive days</span>
            <Dot />
            <span className="text-slate-500">{y.days_remaining} still unwritten</span>
          </h1>

          {y.best_streak > 0 && (
            <p className="flex items-center gap-1.5 text-xs font-medium text-slate-600 pb-1.5">
              <Flame className={`w-3.5 h-3.5 ${y.current_streak > 0 ? 'text-amber-500 fill-amber-400' : 'text-slate-400'}`} />
              {y.current_streak > 0 ? (
                <span>
                  {y.current_streak}-day run <span className="text-slate-500">· best {y.best_streak}</span>
                </span>
              ) : (
                <span>Best run: {y.best_streak} days</span>
              )}
            </p>
          )}
        </div>

        <HorizonBar
          elapsedPct={elapsedPct}
          filledPct={productivePct}
          label={`${y.productive_days_count} productive days so far; ${Math.round(elapsedPct)}% of ${y.year} has passed.`}
        />
      </section>
    );
  }

  if (!summary) return null;

  return (
    <section aria-label="Life horizon" className="px-1 sm:px-2">
      <h1 className="font-serif font-medium text-[1.6rem] sm:text-[2rem] leading-tight tracking-[-0.015em] text-forest-950">
        Week {summary.weeks_lived.toLocaleString()} of {summary.total_weeks.toLocaleString()}
        <Dot />
        <span className="text-emerald-700">age {Math.floor(summary.age_years)}</span>
        <Dot />
        <span className="text-slate-500">{summary.weeks_remaining.toLocaleString()} weeks ahead</span>
      </h1>

      <HorizonBar
        elapsedPct={summary.percentage_lived}
        filledPct={summary.percentage_lived}
        label={`${summary.percentage_lived}% of a ${summary.target_age}-year horizon lived.`}
      />
    </section>
  );
};
