import React, { useState, useEffect } from 'react';
import { Goal, Milestone, goalOSApi } from '../api/client';
import { GoalFormModal } from './GoalFormModal';
import { PageHeader } from './PageHeader';
import {
  Plus,
  CheckCircle2,
  Circle,
  Trash2,
  Pencil,
  Target,
  Calendar,
  Compass
} from 'lucide-react';

const HORIZON_COLUMNS = [
  { key: '1-month', title: '1-month sprints', desc: 'What you’re building momentum on now', icon: Target },
  { key: '1-year', title: '1-year horizons', desc: 'Milestones that compound over the year', icon: Calendar },
  { key: '5-year', title: '5-year vision', desc: 'The life you’re growing toward', icon: Compass },
];

export const GoalsView: React.FC = () => {
  const [horizons, setHorizons] = useState<Record<string, Goal[]>>({
    '1-month': [],
    '1-year': [],
    '5-year': [],
  });
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [addingMilestoneFor, setAddingMilestoneFor] = useState<number | null>(null);
  const [newMilestoneText, setNewMilestoneText] = useState('');

  const loadGoals = async () => {
    try {
      setLoading(true);
      const data = await goalOSApi.getGoalsHorizons();
      setHorizons(data);
    } catch (err) {
      console.error('Failed to load goals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGoals();
  }, []);

  const handleCreateGoal = async (goal: Partial<Goal>) => {
    try {
      await goalOSApi.createGoal(goal);
      setIsCreateOpen(false);
      loadGoals();
    } catch (err) {
      console.error('Failed to create goal:', err);
    }
  };

  const handleUpdateGoal = async (goal: Partial<Goal>) => {
    if (!editingGoal) return;
    try {
      await goalOSApi.updateGoal(editingGoal.id, goal);
      setEditingGoal(null);
      loadGoals();
    } catch (err) {
      console.error('Failed to update goal:', err);
    }
  };

  const handleDeleteGoal = async (id: number) => {
    if (!confirm('Are you sure you want to delete this goal and its milestones?')) return;
    try {
      await goalOSApi.deleteGoal(id);
      loadGoals();
    } catch (err) {
      console.error('Failed to delete goal:', err);
    }
  };

  const handleDeleteMilestone = async (id: number) => {
    try {
      await goalOSApi.deleteMilestone(id);
      loadGoals();
    } catch (err) {
      console.error('Failed to delete milestone:', err);
    }
  };

  const handleAddMilestone = async (goalId: number) => {
    const text = newMilestoneText.trim();
    if (!text) return;
    try {
      await goalOSApi.createMilestone(goalId, {
        goal_id: goalId,
        title: text,
        status: 'active',
        progress: 0.0,
      });
      setNewMilestoneText('');
      loadGoals();
    } catch (err) {
      console.error('Failed to add milestone:', err);
    }
  };

  const handleToggleMilestone = async (ms: Milestone) => {
    try {
      const nextStatus = ms.status === 'completed' ? 'active' : 'completed';
      const nextProgress = nextStatus === 'completed' ? 1.0 : 0.0;
      await goalOSApi.updateMilestone(ms.id, {
        status: nextStatus,
        progress: nextProgress,
      });
      loadGoals();
    } catch (err) {
      console.error('Failed to update milestone:', err);
    }
  };

  const closeMilestoneInput = () => {
    setAddingMilestoneFor(null);
    setNewMilestoneText('');
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Goals"
        subtitle="From your five-year vision down to this month’s sprint."
        actions={
          <button
            type="button"
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center justify-center gap-1.5 bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2 rounded-full text-xs font-semibold shadow-forest-xs transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            New goal
          </button>
        }
      />

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 motion-safe:animate-pulse" aria-hidden="true">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-96 bg-white/60 rounded-3xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {HORIZON_COLUMNS.map((col) => {
            const columnGoals = horizons[col.key] || [];
            const Icon = col.icon;
            return (
              <section key={col.key} className="space-y-4" aria-labelledby={`horizon-${col.key}`}>
                <div className="px-1">
                  <div className="flex items-center justify-between">
                    <h2 id={`horizon-${col.key}`} className="flex items-center gap-2 text-sm font-bold text-slate-900">
                      <Icon className="w-4 h-4 text-emerald-700" />
                      {col.title}
                    </h2>
                    <span className="text-xs font-medium text-slate-500 tabular-nums">{columnGoals.length}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{col.desc}</p>
                </div>

                {columnGoals.length === 0 ? (
                  <div className="rounded-3xl border border-dashed border-emerald-200 px-5 py-8 text-center text-sm text-slate-500">
                    Nothing here yet.
                  </div>
                ) : (
                  columnGoals.map((goal) => {
                    const milestones = goal.milestones || [];
                    const completedMilestones = milestones.filter((m) => m.status === 'completed');
                    const progressPercent =
                      milestones.length > 0
                        ? Math.round((completedMilestones.length / milestones.length) * 100)
                        : Math.round(goal.progress * 100);
                    const isAdding = addingMilestoneFor === goal.id;

                    return (
                      <article key={goal.id} className="glass-panel rounded-3xl p-5 space-y-4 shadow-forest">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <span className="inline-block text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full mb-1.5">
                              {(goal.category || 'General').charAt(0).toUpperCase() + (goal.category || 'General').slice(1).toLowerCase()}
                            </span>
                            <h3 className="font-bold text-[15px] text-slate-900 leading-snug">{goal.title}</h3>
                          </div>

                          <div className="flex items-center flex-shrink-0 -mr-1">
                            <button
                              type="button"
                              onClick={() => setEditingGoal(goal)}
                              className="text-slate-400 hover:text-emerald-700 transition-colors p-1.5 rounded-full cursor-pointer"
                              aria-label={`Edit ${goal.title}`}
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteGoal(goal.id)}
                              className="text-slate-400 hover:text-rose-600 transition-colors p-1.5 rounded-full cursor-pointer"
                              aria-label={`Delete ${goal.title}`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>

                        {goal.reason && <p className="voice italic text-[15px] text-forest-900">{goal.reason}</p>}

                        <div>
                          <div className="flex justify-between text-xs font-medium text-slate-600 mb-1.5">
                            <span>Progress</span>
                            <span className="text-emerald-800 font-semibold tabular-nums">{progressPercent}%</span>
                          </div>
                          <div
                            className="w-full h-1.5 rounded-full bg-emerald-50 ring-1 ring-inset ring-emerald-100 overflow-hidden"
                            role="progressbar"
                            aria-valuenow={progressPercent}
                            aria-valuemin={0}
                            aria-valuemax={100}
                            aria-label={`${goal.title} progress`}
                          >
                            <div
                              className="h-full rounded-full bg-emerald-600 transition-[width] duration-500"
                              style={{ width: `${progressPercent}%` }}
                            />
                          </div>
                        </div>

                        <div className="pt-3 border-t border-emerald-100/70 space-y-1.5">
                          {milestones.length > 0 && (
                            <>
                              <p className="text-xs font-medium text-slate-600">
                                Milestones{' '}
                                <span className="text-slate-500 tabular-nums">
                                  · {completedMilestones.length} of {milestones.length}
                                </span>
                              </p>
                              <ul className="space-y-0.5">
                                {milestones.map((ms) => {
                                  const isCompleted = ms.status === 'completed';
                                  return (
                                    <li
                                      key={ms.id}
                                      className="flex items-center justify-between text-sm px-1.5 py-1 -mx-1.5 rounded-lg hover:bg-emerald-50/50 transition-colors group/ms"
                                    >
                                      <button
                                        type="button"
                                        onClick={() => handleToggleMilestone(ms)}
                                        className="flex items-center gap-2 text-left flex-1 min-w-0 cursor-pointer"
                                        aria-pressed={isCompleted}
                                      >
                                        {isCompleted ? (
                                          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                                        ) : (
                                          <Circle className="w-4 h-4 text-emerald-300 flex-shrink-0" />
                                        )}
                                        <span className={`truncate ${isCompleted ? 'line-through text-slate-500' : 'text-slate-800'}`}>
                                          {ms.title}
                                        </span>
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => handleDeleteMilestone(ms.id)}
                                        aria-label={`Delete milestone ${ms.title}`}
                                        className="text-slate-400 hover:text-rose-600 transition-opacity p-1 flex-shrink-0 opacity-0 group-hover/ms:opacity-100 focus-visible:opacity-100 [@media(hover:none)]:opacity-100 cursor-pointer"
                                      >
                                        <Trash2 className="w-3.5 h-3.5" />
                                      </button>
                                    </li>
                                  );
                                })}
                              </ul>
                            </>
                          )}

                          {isAdding ? (
                            <div className="flex items-center gap-1.5 pt-1">
                              <input
                                type="text"
                                autoFocus
                                aria-label={`New milestone for ${goal.title}`}
                                placeholder="Name the next milestone"
                                value={newMilestoneText}
                                onChange={(e) => setNewMilestoneText(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') handleAddMilestone(goal.id);
                                  if (e.key === 'Escape') closeMilestoneInput();
                                }}
                                className="flex-1 text-sm px-3 py-1.5 rounded-lg border border-emerald-200 bg-white text-slate-900 placeholder:text-slate-500"
                              />
                              <button
                                type="button"
                                onClick={() => handleAddMilestone(goal.id)}
                                className="px-2.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold cursor-pointer"
                              >
                                Add
                              </button>
                              <button
                                type="button"
                                onClick={closeMilestoneInput}
                                className="px-2 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 cursor-pointer"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              onClick={() => {
                                setAddingMilestoneFor(goal.id);
                                setNewMilestoneText('');
                              }}
                              className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-800 hover:text-emerald-950 pt-0.5 cursor-pointer"
                            >
                              <Plus className="w-3.5 h-3.5" />
                              Add milestone
                            </button>
                          )}
                        </div>
                      </article>
                    );
                  })
                )}
              </section>
            );
          })}
        </div>
      )}

      {isCreateOpen && (
        <GoalFormModal
          mode="create"
          initialGoal={{}}
          onCancel={() => setIsCreateOpen(false)}
          onSubmit={handleCreateGoal}
        />
      )}

      {editingGoal && (
        <GoalFormModal
          mode="edit"
          initialGoal={editingGoal}
          onCancel={() => setEditingGoal(null)}
          onSubmit={handleUpdateGoal}
        />
      )}
    </div>
  );
};
