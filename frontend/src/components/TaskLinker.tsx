import React, { useCallback, useEffect, useState } from 'react';
import { Goal, TaskReview, goalOSApi } from '../api/client';
import { formatDate } from '../lib/date';

const PAGE = 8;

interface TaskLinkerProps {
  goals: Goal[];
  /** Called after a link is saved, so goal attention can refresh. */
  onChanged: () => void;
}

/** Completed tasks whose goal is not known yet. Saving a choice applies to every day the task was written. */
export const TaskLinker: React.FC<TaskLinkerProps> = ({ goals, onChanged }) => {
  const [review, setReview] = useState<TaskReview | null>(null);
  const [limit, setLimit] = useState(PAGE);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  const load = useCallback(async (count: number) => {
    try {
      setReview(await goalOSApi.getTaskReview(count));
    } catch (err) {
      console.error('Failed to load tasks to link:', err);
    }
  }, []);

  useEffect(() => {
    load(limit);
  }, [limit, load]);

  const choose = async (key: string, goalId: number | null) => {
    setSavingKey(key);
    setFailed(false);
    try {
      await goalOSApi.putTaskLink(key, goalId === null ? { kind: 'none' } : { kind: 'goal', goal_id: goalId });
      await load(limit);
      onChanged();
    } catch (err) {
      console.error('Failed to save task link:', err);
      setFailed(true);
    } finally {
      setSavingKey(null);
    }
  };

  if (!review || goals.length === 0) return null;
  const remaining = review.unreviewed_completed_keys;

  if (remaining === 0) {
    return (
      <section className="px-1" aria-labelledby="link-title">
        <h2 id="link-title" className="text-sm font-bold text-slate-900">
          Tasks to link
        </h2>
        <p className="text-xs text-slate-600 mt-0.5">Every task you completed is linked to a goal, or marked as serving none.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel rounded-3xl p-6 sm:p-7 space-y-4 shadow-forest" aria-labelledby="link-title">
      <div>
        <h2 id="link-title" className="text-sm font-bold text-slate-900">
          Tasks to link <span className="font-medium text-slate-500 tabular-nums">· {remaining}</span>
        </h2>
        <p className="text-xs text-slate-600 mt-0.5 max-w-2xl">
          Goal alignment counts the tasks you completed that served a goal. Pick the goal each task served, or “No goal”
          for chores. Your choice applies every time you wrote that task. Cues on a goal (in Edit) link tasks for you.
        </p>
      </div>

      <ul className="divide-y divide-emerald-100/70">
        {review.items.map((item) => (
          <li key={item.key} className="py-3 first:pt-0 last:pb-0 space-y-2">
            <p className="text-slate-900">
              <span className="voice text-[15px]">{item.text}</span>
              <span className="text-xs text-slate-500 tabular-nums ml-2">
                ×{item.done} · last {formatDate(item.last_date, { day: 'numeric', month: 'short' })}
              </span>
            </p>
            <div className="flex flex-wrap gap-1.5" role="group" aria-label={`Goal for ${item.text}`}>
              {goals.map((goal) => (
                <button
                  key={goal.id}
                  type="button"
                  disabled={savingKey === item.key}
                  onClick={() => choose(item.key, goal.id)}
                  className="px-2.5 py-1 rounded-full text-xs font-semibold text-emerald-900 bg-emerald-50 hover:bg-emerald-100 disabled:opacity-50 transition-colors cursor-pointer"
                >
                  {goal.title.trim()}
                </button>
              ))}
              <button
                type="button"
                disabled={savingKey === item.key}
                onClick={() => choose(item.key, null)}
                className="px-2.5 py-1 rounded-full text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 transition-colors cursor-pointer"
              >
                No goal
              </button>
            </div>
          </li>
        ))}
      </ul>

      {failed && (
        <p className="text-xs text-rose-700" role="alert">
          That choice didn’t save. Check that GoalOS is running and try again.
        </p>
      )}

      {remaining > review.items.length && (
        <button
          type="button"
          onClick={() => setLimit(limit + PAGE)}
          className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 cursor-pointer"
        >
          Show more ({remaining - review.items.length} left)
        </button>
      )}
    </section>
  );
};
