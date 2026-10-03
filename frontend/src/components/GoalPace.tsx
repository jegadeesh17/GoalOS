import React, { useEffect, useState } from 'react';
import { Goal, GoalPacePoint, GoalPacing, goalOSApi } from '../api/client';
import { formatDate, localDateStr } from '../lib/date';

const number = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 });

const withUnit = (value: number, unit?: string | null): string =>
  unit ? `${number.format(value)} ${unit}` : number.format(value);

const monthName = (month: string): string => {
  const [year, mon] = month.split('-').map(Number);
  return new Date(year, mon - 1, 1).toLocaleDateString('en-US', { month: 'short' });
};

const STATUS_LABEL: Record<string, { text: string; tone: string }> = {
  ahead: { text: 'Ahead of pace', tone: 'bg-emerald-50 text-emerald-800' },
  on_pace: { text: 'On pace', tone: 'bg-emerald-50 text-emerald-800' },
  behind: { text: 'Behind pace', tone: 'bg-amber-50 text-amber-900' },
};

interface GoalPaceProps {
  goal: Goal;
  pacing?: GoalPacing;
  onChanged: () => void;
}

/** A measured goal's target, where it stands against the pace needed, and a monthly check-in. */
export const GoalPace: React.FC<GoalPaceProps> = ({ goal, pacing, onChanged }) => {
  const [checkingIn, setCheckingIn] = useState(false);
  const [month, setMonth] = useState(localDateStr().slice(0, 7));
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [failed, setFailed] = useState(false);
  const [editingPath, setEditingPath] = useState(false);
  const [points, setPoints] = useState<GoalPacePoint[]>([]);
  const [pointDue, setPointDue] = useState('');
  const [pointValue, setPointValue] = useState('');
  const [pointFailed, setPointFailed] = useState(false);

  const loadPoints = async () => {
    try {
      setPoints(await goalOSApi.getGoalPacePoints(goal.id));
    } catch (err) {
      console.error('Failed to load the expected path:', err);
    }
  };

  useEffect(() => {
    if (editingPath) void loadPoints();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editingPath, goal.id]);

  if (goal.target_value == null) return null;

  const unit = goal.metric_unit;
  const target = withUnit(goal.target_value, unit);
  const deadline = goal.deadline ? formatDate(goal.deadline, { day: 'numeric', month: 'short', year: 'numeric' }) : null;
  const label = pacing ? STATUS_LABEL[pacing.status] : undefined;

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = Number(value);
    if (value.trim() === '' || Number.isNaN(parsed)) return;
    setSaving(true);
    setFailed(false);
    try {
      await goalOSApi.putGoalMeasurement(goal.id, { month, value: parsed });
      setCheckingIn(false);
      setValue('');
      onChanged();
    } catch (err) {
      console.error('Failed to save check-in:', err);
      setFailed(true);
    } finally {
      setSaving(false);
    }
  };

  const addPoint = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = Number(pointValue);
    if (!pointDue || pointValue.trim() === '' || Number.isNaN(parsed)) return;
    setPointFailed(false);
    try {
      await goalOSApi.putGoalPacePoint(goal.id, { due: pointDue, value: parsed });
      setPointDue('');
      setPointValue('');
      await loadPoints();
      onChanged();
    } catch (err) {
      console.error('Failed to save the path point:', err);
      setPointFailed(true);
    }
  };

  const removePoint = async (due: string) => {
    setPointFailed(false);
    try {
      await goalOSApi.deleteGoalPacePoint(goal.id, due);
      await loadPoints();
      onChanged();
    } catch (err) {
      console.error('Failed to remove the path point:', err);
      setPointFailed(true);
    }
  };

  // A point the pace calculation skips: before the starting date or on/after the deadline.
  const isIgnored = (due: string): boolean =>
    (pacing?.baseline != null && due <= pacing.baseline.date) || (goal.deadline != null && due >= goal.deadline);

  let reading: React.ReactNode = null;
  if (pacing && label && pacing.latest && pacing.expected_now !== null) {
    reading = (
      <>
        <span className="font-semibold text-slate-900">{withUnit(pacing.latest.value, unit)}</span> in{' '}
        {monthName(pacing.latest.month)}, against about {withUnit(pacing.expected_now, unit)} {pacing.path === 'custom' ? 'on your expected path' : 'needed'} by then.
        {pacing.projection && (
          <>
            {' '}
            At this rate you’d reach about {withUnit(pacing.projection.value_at_deadline, unit)}
            {pacing.projection.on_track ? ', enough to hit it.' : ', short of the target.'}
          </>
        )}
      </>
    );
  } else if (pacing?.status === 'baseline_only') {
    reading = 'Starting value saved. One more check-in shows how you’re pacing.';
  } else if (pacing?.status === 'no_deadline') {
    reading = 'Add a deadline in Edit to measure pace.';
  } else {
    reading = 'No check-ins yet.';
  }

  return (
    <div className="pt-3 border-t border-emerald-100/70 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-slate-600">
          Target <span className="text-slate-800 font-semibold">{target}</span>
          {goal.metric_name && <span className="text-slate-500"> · {goal.metric_name}</span>}
          {deadline && <span className="text-slate-500"> · by {deadline}</span>}
        </p>
        {label && (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${label.tone}`}>{label.text}</span>
        )}
      </div>

      <p className="text-sm text-slate-700 leading-relaxed">{reading}</p>

      {checkingIn ? (
        <form onSubmit={save} className="flex flex-wrap items-center gap-1.5">
          <input
            type="month"
            aria-label={`Check-in month for ${goal.title}`}
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="text-sm px-2.5 py-1.5 rounded-lg border border-emerald-200 bg-white text-slate-900"
            required
          />
          <input
            type="number"
            step="any"
            autoFocus
            aria-label={`Value${unit ? ` in ${unit}` : ''} for ${goal.title}`}
            placeholder={unit ? `Value (${unit})` : 'Value'}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-32 text-sm px-2.5 py-1.5 rounded-lg border border-emerald-200 bg-white text-slate-900 placeholder:text-slate-500"
            required
          />
          <button
            type="submit"
            disabled={saving}
            className="px-2.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-60 text-white rounded-lg text-xs font-semibold cursor-pointer"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button
            type="button"
            onClick={() => {
              setCheckingIn(false);
              setFailed(false);
            }}
            className="px-2 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 cursor-pointer"
          >
            Cancel
          </button>
          {failed && <p className="basis-full text-xs text-amber-800">Couldn’t save that. Try again.</p>}
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setCheckingIn(true)}
          className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 cursor-pointer"
        >
          Check in for a month
        </button>
      )}

      <div className="pt-1">
        <button
          type="button"
          onClick={() => setEditingPath((open) => !open)}
          aria-expanded={editingPath}
          className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 cursor-pointer"
        >
          {editingPath ? 'Hide your expected path' : pacing?.path === 'custom' ? 'Edit your expected path' : 'Set your expected path'}
        </button>

        {editingPath && (
          <div className="mt-2 space-y-2">
            <p className="text-xs text-slate-600 leading-relaxed">
              {goal.deadline
                ? 'Add the values you expect along the way, such as where you expect to be each year. Pace is judged along these points, joined by straight lines, instead of one line to the target.'
                : 'Add a deadline in Edit first, then set the values you expect along the way.'}
            </p>

            {points.length > 0 && (
              <ul className="space-y-1">
                {points.map((point) => (
                  <li key={point.due} className="flex items-center justify-between gap-2 text-sm text-slate-800">
                    <span>
                      By {formatDate(point.due, { day: 'numeric', month: 'short', year: 'numeric' })} ·{' '}
                      <span className="font-semibold tabular-nums">{withUnit(point.value, unit)}</span>
                      {isIgnored(point.due) && <span className="text-xs text-amber-800"> · outside the goal’s dates, so not used</span>}
                    </span>
                    <button
                      type="button"
                      onClick={() => void removePoint(point.due)}
                      aria-label={`Remove the point for ${point.due}`}
                      className="text-xs font-semibold text-slate-500 hover:text-rose-700 cursor-pointer"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {goal.deadline && (
              <form onSubmit={addPoint} className="flex flex-wrap items-center gap-1.5">
                <input
                  type="date"
                  aria-label={`Date for the expected value of ${goal.title}`}
                  value={pointDue}
                  max={goal.deadline}
                  onChange={(e) => setPointDue(e.target.value)}
                  className="text-sm px-2.5 py-1.5 rounded-lg border border-emerald-200 bg-white text-slate-900"
                  required
                />
                <input
                  type="number"
                  step="any"
                  aria-label={`Expected value${unit ? ` in ${unit}` : ''} for ${goal.title}`}
                  placeholder={unit ? `Expected (${unit})` : 'Expected value'}
                  value={pointValue}
                  onChange={(e) => setPointValue(e.target.value)}
                  className="w-36 text-sm px-2.5 py-1.5 rounded-lg border border-emerald-200 bg-white text-slate-900 placeholder:text-slate-500"
                  required
                />
                <button
                  type="submit"
                  className="px-2.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Add point
                </button>
              </form>
            )}
            {pointFailed && <p className="text-xs text-amber-800">Couldn’t save that. Try again.</p>}
          </div>
        )}
      </div>
    </div>
  );
};
