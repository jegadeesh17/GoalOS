import React, { useCallback, useEffect, useState } from 'react';
import { CalendarDays, Lightbulb, RefreshCw } from 'lucide-react';
import { Lever, MonthlySnapshot, goalOSApi } from '../api/client';
import { formatDate } from '../lib/date';

const SLEEP_GAP_REASONS: Record<string, string> = {
  no_awake_line: 'no wake and bed line',
  unreadable_awake_line: 'a wake or bed time that could not be read',
  no_previous_day: 'no entry the day before',
  previous_bedtime_unreadable: 'a missing or unreadable bedtime the night before',
  implausible_bedtime: 'a bedtime that looks like an AM/PM slip',
};

const number = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 });

const monthDate = (month: string, offset = 0): Date => {
  const [year, mon] = month.split('-').map(Number);
  return new Date(year, mon - 1 + offset, 1);
};

const monthLabel = (month: string, style: 'short' | 'long' = 'short'): string =>
  monthDate(month).toLocaleDateString('en-US', { month: style === 'long' ? 'long' : 'short', year: 'numeric' });

const fmt = (value: number | null | undefined, suffix = ''): string =>
  value == null ? '–' : `${number.format(value)}${suffix}`;

interface DeltaProps {
  value: number | undefined;
  unit: string;
  versus: string;
  /** Whether a higher number is the better direction. Omit for neutral measures like wake time. */
  higherIsBetter?: boolean;
}

const Delta: React.FC<DeltaProps> = ({ value, unit, versus, higherIsBetter }) => {
  if (value === undefined) return null;
  const flat = Math.abs(value) < 0.05;
  const tone =
    flat || higherIsBetter === undefined
      ? 'text-slate-500'
      : (value > 0) === higherIsBetter
        ? 'text-emerald-700'
        : 'text-amber-800';
  const sign = value > 0 ? '+' : value < 0 ? '−' : '';
  return (
    <p className={`text-xs font-semibold mt-0.5 tabular-nums ${tone}`}>
      {flat ? 'No change' : `${sign}${number.format(Math.abs(value))} ${unit}`}
      <span className="font-normal text-slate-500"> vs {versus}</span>
    </p>
  );
};

const LeverRow: React.FC<{ lever: Lever }> = ({ lever }) => (
  <li className="py-3.5">
    <div className="flex items-center gap-2 flex-wrap">
      <h4 className="text-sm font-semibold text-slate-900">{lever.label}</h4>
      <span
        className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
          lever.tier === 'strong' ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-900'
        }`}
      >
        {lever.tier === 'strong' ? 'Strong pattern' : 'Possible pattern'}
      </span>
    </div>
    {lever.contrast && <p className="text-sm text-slate-700 mt-1 leading-relaxed">{lever.contrast}</p>}
    <p className="text-xs text-slate-500 mt-1">
      {lever.n} days compared · {lever.caveat}
    </p>
  </li>
);

export const MonthlyReview: React.FC = () => {
  const [snapshots, setSnapshots] = useState<MonthlySnapshot[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (keepSelection: boolean) => {
    try {
      const data = await goalOSApi.getMonthlyAnalytics();
      setSnapshots(data);
      const latest = data.length > 0 ? data[data.length - 1].month : null;
      setSelected((current) => (keepSelection && current && data.some((s) => s.month === current) ? current : latest));
      setError(null);
    } catch (err) {
      console.error('Failed to load monthly analytics:', err);
      setError('Monthly analytics couldn’t load. Check that GoalOS is running, then open this tab again.');
    }
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  const refresh = async () => {
    setRefreshing(true);
    try {
      await goalOSApi.recomputeMonthlyAnalytics();
      await load(true);
    } catch (err) {
      console.error('Failed to recalculate monthly analytics:', err);
      setError('Recalculating didn’t work. Try again in a moment.');
    } finally {
      setRefreshing(false);
    }
  };

  const snapshot = snapshots?.find((s) => s.month === selected) ?? null;

  return (
    <section className="glass-panel rounded-3xl p-6 sm:p-7 space-y-6 shadow-forest" aria-labelledby="monthly-title">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="monthly-title" className="font-bold text-sm text-slate-900 flex items-center gap-2">
            <CalendarDays className="w-4 h-4 text-emerald-700" />
            Month by month
          </h2>
          <p className="text-xs text-slate-600 mt-0.5 max-w-2xl">
            Saved every time you import, so months can be compared and the trend toward your goals stays visible.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800 hover:text-emerald-950 disabled:opacity-60 cursor-pointer flex-shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'motion-safe:animate-spin' : ''}`} />
          {refreshing ? 'Recalculating…' : 'Recalculate'}
        </button>
      </div>

      {error && <p className="text-sm text-slate-600">{error}</p>}
      {!error && snapshots === null && (
        <div className="h-40 bg-white/60 rounded-2xl motion-safe:animate-pulse" aria-hidden="true" />
      )}
      {!error && snapshots?.length === 0 && (
        <p className="text-sm text-slate-600">No months saved yet. They appear after your first journal import.</p>
      )}

      {snapshots && snapshots.length > 0 && snapshot && (
        <>
          <div role="group" aria-label="Choose a month" className="flex flex-wrap gap-2">
            {snapshots.map((s) => (
              <button
                key={s.month}
                type="button"
                aria-pressed={s.month === selected}
                onClick={() => setSelected(s.month)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
                  s.month === selected
                    ? 'bg-emerald-700 text-white'
                    : 'bg-emerald-50 text-emerald-900 hover:bg-emerald-100'
                }`}
              >
                {monthLabel(s.month)}
              </button>
            ))}
          </div>

          <MonthDetail snapshot={snapshot} />
        </>
      )}
    </section>
  );
};

const MonthDetail: React.FC<{ snapshot: MonthlySnapshot }> = ({ snapshot }) => {
  const { metrics: m, insights, goal_results: goals } = snapshot;
  const versus = monthDate(snapshot.month, -1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  const d = m.delta_vs_previous;
  const solidShare = m.days_logged ? Math.round((m.tasks.solid_days / m.days_logged) * 100) : null;
  const sleepGaps = Object.entries(m.sleep.unknown_reasons);
  const gapNights = sleepGaps.reduce((total, [, count]) => total + count, 0);

  const planSize = insights?.observations.plan_size ?? [];
  const fivePlus = planSize.find((b) => b.bucket === '5+');
  const three = planSize.find((b) => b.bucket === '3');
  const position = insights?.observations.task_position ?? [];
  const first = position.find((p) => p.position === '1');
  const fifth = position.find((p) => p.position === '5+');

  return (
    <div className="space-y-7">
      <div className="flex items-center gap-3 flex-wrap">
        <h3 className="font-serif text-xl text-slate-900">{monthLabel(snapshot.month, 'long')}</h3>
        {snapshot.status === 'provisional' && (
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200/80">
            Provisional
            {snapshot.data_through && ` · data through ${formatDate(snapshot.data_through, { day: 'numeric', month: 'short' })}`}
          </span>
        )}
      </div>

      <dl className="grid grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-5">
        <div>
          <dt className="text-xs font-semibold text-slate-600">Tasks done</dt>
          <dd className="text-2xl font-bold text-slate-900 mt-1 tabular-nums">{fmt(m.tasks.completion_rate, '%')}</dd>
          <p className="text-xs text-slate-500 mt-0.5">
            {m.tasks.done} of {m.tasks.planned} · {fmt(m.tasks.per_day)} planned a day
          </p>
          <Delta value={d.completion_rate} unit="pts" versus={versus} higherIsBetter />
        </div>
        <div>
          <dt className="text-xs font-semibold text-slate-600">Solid days</dt>
          <dd className="text-2xl font-bold text-slate-900 mt-1 tabular-nums">
            {m.tasks.solid_days} <span className="text-sm font-semibold text-slate-500">of {m.days_logged}</span>
          </dd>
          <p className="text-xs text-slate-500 mt-0.5">
            Half or more ticked · {m.tasks.zero_days} with none{solidShare !== null && ` · ${solidShare}%`}
          </p>
          <Delta value={d.solid_day_share} unit="pts" versus={versus} higherIsBetter />
        </div>
        <div>
          <dt className="text-xs font-semibold text-slate-600">Sleep</dt>
          <dd className="text-2xl font-bold text-slate-900 mt-1 tabular-nums">
            {fmt(m.sleep.avg_hours)} <span className="text-sm font-semibold text-slate-500">h</span>
          </dd>
          <p className="text-xs text-slate-500 mt-0.5">
            {m.sleep.nights_known > 0
              ? `${m.sleep.nights_known} nights · ${m.sleep.under_6} under 6 h`
              : 'No wake and bed times this month'}
          </p>
          <Delta value={d.avg_sleep_hours} unit="h" versus={versus} higherIsBetter />
        </div>
        <div>
          <dt className="text-xs font-semibold text-slate-600">Wake-up</dt>
          <dd className="text-2xl font-bold text-slate-900 mt-1 tabular-nums">{m.sleep.wake.avg_clock ?? '–'}</dd>
          <p className="text-xs text-slate-500 mt-0.5">
            {m.sleep.wake.sd !== null ? `Varies ±${fmt(m.sleep.wake.sd)} h` : 'Not enough days'}
            {m.sleep.bedtime.avg_clock && ` · bed ${m.sleep.bedtime.avg_clock}`}
          </p>
          <Delta
            value={d.wake_hour === undefined ? undefined : Math.round(d.wake_hour * 60)}
            unit="min"
            versus={versus}
          />
        </div>
      </dl>

      {m.tasks.weekly.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-600">Tasks done, week by week</h4>
          <ul className="flex items-end gap-3 mt-2.5">
            {m.tasks.weekly.map((w) => (
              <li
                key={w.week_start}
                className="flex flex-col items-center gap-1 flex-1 max-w-[72px]"
                aria-label={`Week of ${formatDate(w.week_start, { day: 'numeric', month: 'short' })}: ${
                  w.rate === null ? 'no tasks' : `${w.rate}% done`
                }`}
              >
                <div className="h-20 w-full rounded-lg bg-emerald-50 overflow-hidden flex items-end" aria-hidden="true">
                  <div className="w-full bg-emerald-600" style={{ height: `${w.rate ?? 0}%` }} />
                </div>
                <span className="text-xs font-semibold tabular-nums text-slate-800">{fmt(w.rate, '%')}</span>
                <span className="text-[11px] text-slate-500 tabular-nums">
                  {formatDate(w.week_start, { day: 'numeric', month: 'short' })}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {insights && (
        <div>
          <h4 className="font-bold text-sm text-slate-900">What moves your days</h4>
          {insights.findings.length > 0 ? (
            <ul className="divide-y divide-emerald-100/70 mt-1">
              {insights.findings.map((lever) => (
                <LeverRow key={lever.lever} lever={lever} />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-600 mt-1.5 max-w-2xl">
              Nothing clear yet. A pattern needs about 30 matched days; this window has {insights.window_days} logged.
            </p>
          )}
          {(fivePlus && three) || (first && fifth) ? (
            <ul className="text-sm text-slate-700 mt-2 space-y-1">
              {fivePlus && three && (
                <li>
                  Planning 5 or more tasks ({fivePlus.days} days) got {fmt(fivePlus.avg_done)} done a day, against{' '}
                  {fmt(three.avg_done)} when you planned 3 ({three.days} days).
                </li>
              )}
              {first && fifth && (
                <li>
                  The first task on your list was done {fmt(first.rate, '%')} of the time, the fifth or later{' '}
                  {fmt(fifth.rate, '%')}.
                </li>
              )}
            </ul>
          ) : null}
        </div>
      )}

      {insights && insights.focus.length > 0 && (
        <div>
          <h4 className="font-bold text-sm text-slate-900">Try next month</h4>
          <ul className="mt-2 space-y-2">
            {insights.focus.map((line) => (
              <li key={line} className="flex items-start gap-2.5 text-sm text-slate-800 leading-relaxed">
                <Lightbulb className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      {m.stuck_tasks.length > 0 && (
        <div>
          <h4 className="font-bold text-sm text-slate-900">Tasks that keep coming back</h4>
          <ul className="mt-2 space-y-1 text-sm text-slate-800">
            {m.stuck_tasks.map((t) => (
              <li key={t.task}>
                <span className="font-serif text-[15px]">{t.task}</span>{' '}
                <span className="text-slate-500 tabular-nums">
                  planned ×{t.planned}, done ×{t.done}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {goals.length > 0 && (
        <div>
          <h4 className="font-bold text-sm text-slate-900">Your goals that month</h4>
          <ul className="mt-2 divide-y divide-emerald-100/70">
            {goals.map((g) => (
              <li key={g.goal_id} className="flex items-baseline justify-between gap-4 py-2 text-sm">
                <span>
                  <span className="font-serif text-[15px] text-slate-900">{g.goal_title}</span>{' '}
                  <span className="text-xs text-slate-500">{g.horizon}</span>
                </span>
                <span className="font-semibold text-emerald-800 tabular-nums">
                  {g.progress_at_close === null ? '–' : `${Math.round(g.progress_at_close * 100)}%`}
                </span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-slate-500 mt-1.5">
            Recorded {formatDate(goals[0].as_of, { day: 'numeric', month: 'short' })}. Later edits to a goal don’t change a closed month.
          </p>
        </div>
      )}

      {(gapNights > 0 || m.sleep.bedtime.excluded > 0) && (
        <p className="text-xs text-slate-500 max-w-2xl">
          {gapNights > 0 &&
            `Sleep couldn’t be worked out for ${gapNights} ${gapNights === 1 ? 'night' : 'nights'}: ${sleepGaps
              .map(([reason, count]) => `${SLEEP_GAP_REASONS[reason] ?? reason} (${count})`)
              .join(', ')}. `}
          {m.sleep.bedtime.excluded > 0 &&
            `${m.sleep.bedtime.excluded} ${m.sleep.bedtime.excluded === 1 ? 'bedtime' : 'bedtimes'} looked like AM/PM slips and ${m.sleep.bedtime.excluded === 1 ? 'was' : 'were'} left out of the averages.`}
        </p>
      )}
    </div>
  );
};
