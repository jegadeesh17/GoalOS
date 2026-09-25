import React from 'react';
import { YearDayBlock } from '../api/client';
import { formatDate } from '../lib/date';

export type DayTier = 'strong' | 'productive' | 'logged' | 'unlogged' | 'future';

export const dayTier = (day: YearDayBlock): DayTier => {
  if (day.is_productive) return (day.productivity_score ?? 0) >= 70 ? 'strong' : 'productive';
  if (day.has_log) return 'logged';
  return day.status === 'future' ? 'future' : 'unlogged';
};

const TIER_RANK: Record<DayTier, number> = { future: 0, unlogged: 0, logged: 1, productive: 2, strong: 3 };

/** How "written" a day is; the dot inks when this rises. */
export const tierRank = (day: YearDayBlock | undefined): number => (day ? TIER_RANK[dayTier(day)] : 0);

export const TIER_LABEL: Record<DayTier, string> = {
  strong: 'Strong day',
  productive: 'Productive',
  logged: 'Logged',
  unlogged: 'Not logged',
  future: 'Still ahead',
};

export const TIER_FILL: Record<DayTier, string> = {
  strong: 'bg-emerald-800',
  productive: 'bg-emerald-600',
  logged: 'bg-emerald-100 border border-emerald-400/80',
  unlogged: 'bg-slate-200/80',
  future: 'border border-dashed border-emerald-200',
};

/** Screen-reader sentence for a day, e.g. "Thursday, September 3, productive, score 76". */
export const describeDay = (day: YearDayBlock): string => {
  const parts = [formatDate(day.date, { weekday: 'long', month: 'long', day: 'numeric' })];
  if (day.status === 'today') parts.push('today');
  parts.push(TIER_LABEL[dayTier(day)].toLowerCase());
  if (day.productivity_score !== null && day.productivity_score !== undefined) {
    parts.push(`score ${Math.round(day.productivity_score)}`);
  }
  if (day.deep_work_hours) parts.push(`${day.deep_work_hours}h deep work`);
  return parts.join(', ');
};

interface DayDotProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  day: YearDayBlock;
  selected?: boolean;
  inking?: boolean;
  size?: 'sm' | 'md';
}

export const DayDot = React.forwardRef<HTMLButtonElement, DayDotProps>(
  ({ day, selected = false, inking = false, size = 'sm', className = '', ...rest }, ref) => {
    const tier = dayTier(day);
    const isToday = day.status === 'today';
    // An unwritten today is the sun; once written it takes its ink and keeps the amber ring.
    const fill = isToday && tier === 'unlogged' ? 'bg-amber-400' : TIER_FILL[tier];
    const dimensions = size === 'md' ? 'w-6 h-6' : 'w-6 h-6 sm:w-5 sm:h-5';

    return (
      <button
        ref={ref}
        type="button"
        aria-label={describeDay(day)}
        className={`relative shrink-0 rounded-full cursor-pointer transition-transform duration-150 ease-out motion-safe:hover:scale-125 ${dimensions} ${fill} ${
          isToday ? 'day-today' : ''
        } ${inking ? 'day-ink' : ''} ${selected ? `ring-2 ring-emerald-700 ring-offset-white ${isToday ? 'ring-offset-4' : 'ring-offset-2'}` : ''} ${className}`}
        {...rest}
      />
    );
  },
);

DayDot.displayName = 'DayDot';
