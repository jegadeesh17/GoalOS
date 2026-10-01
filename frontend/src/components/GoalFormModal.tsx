import React, { useState, useEffect } from 'react';
import { Goal } from '../api/client';
import { Target, X } from 'lucide-react';

interface GoalFormModalProps {
  mode: 'create' | 'edit';
  initialGoal: Partial<Goal>;
  onCancel: () => void;
  onSubmit: (goal: Partial<Goal>) => Promise<void> | void;
}

const emptyGoal: Partial<Goal> = {
  title: '',
  category: 'Career',
  horizon: '1-month',
  priority: 1,
  reason: '',
  success_criteria: '',
  progress: 0.0,
  status: 'active',
};

export const GoalFormModal: React.FC<GoalFormModalProps> = ({ mode, initialGoal, onCancel, onSubmit }) => {
  const [goal, setGoal] = useState<Partial<Goal>>({ ...emptyGoal, ...initialGoal });
  const [saving, setSaving] = useState(false);
  const [cuesText, setCuesText] = useState((initialGoal.cues || []).join(', '));
  const [cueError, setCueError] = useState<string | null>(null);

  useEffect(() => {
    setGoal({ ...emptyGoal, ...initialGoal });
    setCuesText((initialGoal.cues || []).join(', '));
  }, [initialGoal]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onCancel]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.title?.trim()) return;
    const cues = cuesText.split(',').map((c) => c.trim()).filter(Boolean);
    if (cues.some((c) => c.length < 3)) {
      setCueError('Each cue needs at least 3 characters.');
      return;
    }
    setCueError(null);
    // Empty text/number inputs are omitted, not sent as '' or NaN (the API validates dates and numbers).
    const payload: Partial<Goal> = { ...goal };
    // Editing sends the list even when empty, so clearing the field clears the cues.
    if (cues.length > 0 || mode === 'edit') payload.cues = cues;
    else delete payload.cues;
    for (const key of ['deadline', 'metric_name', 'metric_unit'] as const) {
      if (!payload[key]?.toString().trim()) delete payload[key];
    }
    for (const key of ['start_value', 'target_value'] as const) {
      if (payload[key] == null || Number.isNaN(payload[key])) delete payload[key];
    }
    try {
      setSaving(true);
      await onSubmit(payload);
    } finally {
      setSaving(false);
    }
  };

  const hasMilestones = (initialGoal.milestones?.length || 0) > 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 !mt-0">
      <div className="absolute inset-0 bg-forest-950/25 animate-veil-in" onClick={onCancel} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="goal-form-title"
        className="relative bg-white rounded-3xl border border-emerald-100 max-w-lg w-full p-6 space-y-4 shadow-forest-lg max-h-[90vh] overflow-y-auto animate-fade-up"
      >
        <div className="flex items-center justify-between pb-2 border-b border-emerald-100/60">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-emerald-700 text-white">
              <Target className="w-4 h-4" />
            </div>
            <h3 id="goal-form-title" className="font-bold text-base text-slate-900">
              {mode === 'create' ? 'New goal' : 'Edit goal'}
            </h3>
          </div>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Close"
            className="text-slate-500 hover:text-slate-800 p-1 rounded-full hover:bg-slate-100 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Goal title *
            </label>
            <input
              type="text"
              required
              placeholder="e.g., Master Multi-Agent Systems"
              value={goal.title}
              onChange={(e) => setGoal({ ...goal, title: e.target.value })}
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-emerald-100 focus:ring-2 focus:ring-emerald-600 bg-white/95 text-slate-900"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Horizon
              </label>
              <select
                value={goal.horizon}
                onChange={(e) => setGoal({ ...goal, horizon: e.target.value })}
                className="w-full text-xs px-3 py-2 rounded-xl border border-emerald-100 bg-white/95 text-slate-800 font-medium"
              >
                <option value="1-month">1-Month Sprint</option>
                <option value="1-year">1-Year Horizon</option>
                <option value="5-year">5-Year Horizon</option>
                <option value="10-year">10-Year Vision</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Category
              </label>
              <select
                value={goal.category}
                onChange={(e) => setGoal({ ...goal, category: e.target.value })}
                className="w-full text-xs px-3 py-2 rounded-xl border border-emerald-100 bg-white/95 text-slate-800 font-medium"
              >
                <option value="Career">Career & Tech</option>
                <option value="Health">Health & Fitness</option>
                <option value="Wealth">Wealth & Finance</option>
                <option value="Learning">Learning & Mind</option>
                <option value="Relationships">Relationships</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Why this goal matters
            </label>
            <textarea
              rows={2}
              placeholder="Why is achieving this essential to your life trajectory?"
              value={goal.reason || ''}
              onChange={(e) => setGoal({ ...goal, reason: e.target.value })}
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-emerald-100 focus:ring-2 focus:ring-emerald-600 bg-white/95 resize-none text-slate-900"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Deadline
            </label>
            <input
              type="date"
              value={goal.deadline || ''}
              onChange={(e) => setGoal({ ...goal, deadline: e.target.value })}
              className="w-full text-sm px-3.5 py-2 rounded-xl border border-emerald-100 focus:ring-2 focus:ring-emerald-600 bg-white/95 text-slate-900"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Success criteria
            </label>
            <textarea
              rows={2}
              placeholder="How will you know this goal is truly done?"
              value={goal.success_criteria || ''}
              onChange={(e) => setGoal({ ...goal, success_criteria: e.target.value })}
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-emerald-100 focus:ring-2 focus:ring-emerald-600 bg-white/95 resize-none text-slate-900"
            />
          </div>

          <fieldset className="space-y-2 rounded-xl border border-emerald-100 px-3.5 pt-2 pb-3">
            <legend className="px-1 text-xs font-semibold text-slate-700">Number to track (optional)</legend>
            <p className="text-[11px] text-slate-500 font-normal">
              Give the goal a number and GoalOS can show whether you’re on pace, from a check-in each month. Leave it
              empty for goals that can’t be measured.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                aria-label="What you measure"
                placeholder="What you measure, e.g. Net worth"
                value={goal.metric_name || ''}
                onChange={(e) => setGoal({ ...goal, metric_name: e.target.value })}
                className="w-full text-sm px-3 py-2 rounded-xl border border-emerald-100 bg-white/95 text-slate-900 placeholder:text-slate-500"
              />
              <input
                type="text"
                aria-label="Unit"
                placeholder="Unit, e.g. crore INR"
                value={goal.metric_unit || ''}
                onChange={(e) => setGoal({ ...goal, metric_unit: e.target.value })}
                className="w-full text-sm px-3 py-2 rounded-xl border border-emerald-100 bg-white/95 text-slate-900 placeholder:text-slate-500"
              />
              <label className="block text-[11px] font-semibold text-slate-600">
                Starting value
                <input
                  type="number"
                  step="any"
                  placeholder="Optional"
                  value={goal.start_value ?? ''}
                  onChange={(e) => setGoal({ ...goal, start_value: e.target.value === '' ? undefined : Number(e.target.value) })}
                  className="mt-1 w-full text-sm font-normal px-3 py-2 rounded-xl border border-emerald-100 bg-white/95 text-slate-900 placeholder:text-slate-500"
                />
              </label>
              <label className="block text-[11px] font-semibold text-slate-600">
                Target value
                <input
                  type="number"
                  step="any"
                  placeholder="Where you want to get to"
                  value={goal.target_value ?? ''}
                  onChange={(e) => setGoal({ ...goal, target_value: e.target.value === '' ? undefined : Number(e.target.value) })}
                  className="mt-1 w-full text-sm font-normal px-3 py-2 rounded-xl border border-emerald-100 bg-white/95 text-slate-900 placeholder:text-slate-500"
                />
              </label>
            </div>
          </fieldset>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Task cues
              <input
                type="text"
                placeholder="e.g. apply, interview, resume"
                value={cuesText}
                onChange={(e) => setCuesText(e.target.value)}
                aria-describedby="cue-help"
                className="mt-1 w-full text-sm font-normal px-3.5 py-2 rounded-xl border border-emerald-100 focus:ring-2 focus:ring-emerald-600 bg-white/95 text-slate-900 placeholder:text-slate-500"
              />
            </label>
            <p id="cue-help" className="text-[11px] text-slate-500 mt-1 font-normal">
              Words that mark a task as serving this goal, separated by commas. “appl” also matches “apply” and
              “applications”. Tasks that match more than one goal stay in your list to link by hand.
            </p>
            {cueError && (
              <p className="text-[11px] text-rose-700 mt-1" role="alert">
                {cueError}
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center justify-between">
              <span>Manual progress</span>
              <span className="text-emerald-800 font-mono text-[11px] font-semibold">
                {Math.round((goal.progress || 0) * 100)}%
              </span>
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={goal.progress ?? 0}
              onChange={(e) => setGoal({ ...goal, progress: parseFloat(e.target.value) })}
              className="w-full accent-emerald-700 cursor-pointer"
              disabled={hasMilestones}
            />
            <p className="text-[11px] text-slate-500 mt-1 font-normal">
              {hasMilestones
                ? 'Progress is driven by milestone completion while this goal has milestones.'
                : 'No milestones yet — set progress manually until you add some.'}
            </p>
          </div>

          <div className="flex items-center justify-end space-x-2.5 pt-2 border-t border-emerald-100/60">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 rounded-full text-xs font-semibold text-slate-600 hover:bg-slate-100 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white px-5 py-2 rounded-full text-xs font-semibold shadow-forest-xs cursor-pointer"
            >
              {saving ? 'Saving…' : mode === 'create' ? 'Save goal' : 'Save changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
