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

  useEffect(() => {
    setGoal({ ...emptyGoal, ...initialGoal });
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
    try {
      setSaving(true);
      await onSubmit(goal);
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
                <option value="5-year">5-Year Vision</option>
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
