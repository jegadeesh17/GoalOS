import React, { useState, useEffect } from 'react';
import { Goal, Milestone, goalOSApi } from '../api/client';
import { GoalFormModal } from './GoalFormModal';
import {
  Plus,
  CheckCircle2,
  Circle,
  Trash2,
  Flag,
  Pencil,
  Target,
  Calendar,
  Compass
} from 'lucide-react';

export const GoalsView: React.FC = () => {
  const [horizons, setHorizons] = useState<Record<string, Goal[]>>({
    '1-month': [],
    '1-year': [],
    '5-year': [],
  });
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [newMilestoneText, setNewMilestoneText] = useState<Record<number, string>>({});

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
    const text = newMilestoneText[goalId];
    if (!text || !text.trim()) return;
    try {
      await goalOSApi.createMilestone(goalId, {
        goal_id: goalId,
        title: text.trim(),
        status: 'active',
        progress: 0.0,
      });
      setNewMilestoneText({ ...newMilestoneText, [goalId]: '' });
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

  const horizonColumns = [
    { 
      key: '1-month', 
      title: '1-Month Sprints', 
      desc: 'Immediate tactical focus & habit momentum', 
      icon: Target,
      gradient: 'from-emerald-600 to-teal-600'
    },
    { 
      key: '1-year', 
      title: '1-Year Horizons', 
      desc: 'Strategic compounding milestones & skill expansion', 
      icon: Calendar,
      gradient: 'from-teal-600 to-emerald-700'
    },
    { 
      key: '5-year', 
      title: '5-Year Vision', 
      desc: 'Long-term life trajectory & identity architecture', 
      icon: Compass,
      gradient: 'from-earth-amber to-emerald-600'
    },
  ];

  if (loading) {
    return (
      <div className="glass-panel rounded-3xl p-8 animate-pulse space-y-6">
        <div className="h-5 bg-slate-100 rounded-full w-1/4"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-96 bg-slate-50/60 rounded-2xl"></div>
          <div className="h-96 bg-slate-50/60 rounded-2xl"></div>
          <div className="h-96 bg-slate-50/60 rounded-2xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Create Action */}
      <div className="glass-panel rounded-3xl p-6 sm:p-7 shadow-forest border border-emerald-100/70 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-forest-700 mb-1">
            <span className="flex items-center space-x-1 bg-emerald-50/90 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200/70 shadow-forest-xs font-semibold">
              <Target className="w-3.5 h-3.5 text-emerald-700" />
              <span>Multi-Horizon Architecture</span>
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Goals & Horizons Board</h2>
          <p className="text-xs text-slate-500 mt-0.5 font-normal">
            Bridge 5-year life vision down to daily 1-month execution sprints.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center justify-center space-x-1.5 bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2 rounded-full text-xs font-semibold shadow-forest-xs transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Goal</span>
        </button>
      </div>

      {/* 3 Horizon Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {horizonColumns.map((col) => {
          const columnGoals = horizons[col.key] || [];
          const Icon = col.icon;
          return (
            <div key={col.key} className="space-y-4">
              {/* Column Header */}
              <div className="glass-panel rounded-3xl p-4 sm:p-5 shadow-forest border border-emerald-100/70">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200/60">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-sm text-slate-900">{col.title}</h3>
                  </div>
                  <span className="text-xs font-semibold bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200/70">
                    {columnGoals.length}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1 font-normal">{col.desc}</p>
              </div>

              {/* Goal Cards List */}
              <div className="space-y-3.5">
                {columnGoals.length === 0 ? (
                  <div className="glass-panel rounded-3xl border border-dashed border-emerald-200/70 p-6 text-center text-xs text-slate-400 font-normal">
                    No active goals in this horizon.
                  </div>
                ) : (
                  columnGoals.map((goal) => {
                    const milestones = goal.milestones || [];
                    const completedMilestones = milestones.filter((m) => m.status === 'completed');
                    const progressPercent = milestones.length > 0 
                      ? Math.round((completedMilestones.length / milestones.length) * 100)
                      : Math.round(goal.progress * 100);

                    return (
                      <div
                        key={goal.id}
                        className="glass-card-interactive rounded-3xl p-5 space-y-3 border border-emerald-100/80 shadow-forest"
                      >
                        {/* Title & Category Badge */}
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="text-xs uppercase font-semibold bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-900 px-2 py-0.5 rounded-md border border-emerald-200/80">
                                {goal.category}
                              </span>
                              <span className="text-xs font-mono text-slate-400">P{goal.priority}</span>
                            </div>
                            <h4 className="font-bold text-sm text-slate-900 leading-snug">{goal.title}</h4>
                          </div>

                          <div className="flex items-center space-x-0.5 flex-shrink-0">
                            <button
                              type="button"
                              onClick={() => setEditingGoal(goal)}
                              className="text-slate-400 hover:text-emerald-700 transition-colors p-1 cursor-pointer"
                              title="Edit goal"
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteGoal(goal.id)}
                              className="text-slate-400 hover:text-rose-600 transition-colors p-1 cursor-pointer"
                              title="Delete goal"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        {goal.reason && (
                          <p className="text-xs text-slate-700 bg-white/90 p-2.5 rounded-xl border border-emerald-100/70 leading-relaxed">
                            <strong className="text-slate-900 font-semibold">Motivation:</strong> {goal.reason}
                          </p>
                        )}

                        {/* Progress Bar */}
                        <div>
                          <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                            <span>Progress</span>
                            <span className="text-emerald-800 font-bold">{progressPercent}%</span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden p-0.5 border border-emerald-100">
                            <div
                              className={`bg-gradient-to-r ${col.gradient} h-full rounded-full transition-all duration-500`}
                              style={{ width: `${progressPercent}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* Milestones Checklist */}
                        <div className="space-y-1.5 pt-2.5 border-t border-emerald-100/60">
                          <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                            <span className="flex items-center space-x-1">
                              <Flag className="w-3.5 h-3.5 text-emerald-700" />
                              <span>Milestones</span>
                            </span>
                            <span className="text-xs text-emerald-700 font-medium">
                              {completedMilestones.length}/{milestones.length}
                            </span>
                          </div>

                          <div className="space-y-1">
                            {milestones.map((ms) => {
                              const isCompleted = ms.status === 'completed';
                              return (
                                <div
                                  key={ms.id}
                                  className="flex items-center justify-between text-xs p-1.5 rounded-lg hover:bg-white transition-all group/ms"
                                >
                                  <button
                                    type="button"
                                    onClick={() => handleToggleMilestone(ms)}
                                    className="flex items-center space-x-2 text-left flex-1 min-w-0 cursor-pointer"
                                  >
                                    {isCompleted ? (
                                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                                    ) : (
                                      <Circle className="w-4 h-4 text-emerald-300 flex-shrink-0" />
                                    )}
                                    <span className={`truncate ${isCompleted ? 'line-through text-slate-400' : 'text-slate-800 font-normal'}`}>
                                      {ms.title}
                                    </span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteMilestone(ms.id)}
                                    title="Delete milestone"
                                    className="text-slate-300 hover:text-rose-600 transition-colors p-1 flex-shrink-0 opacity-0 group-hover/ms:opacity-100 cursor-pointer"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              );
                            })}
                          </div>

                          {/* Add milestone inline input */}
                          <div className="flex items-center space-x-1.5 pt-1">
                            <input
                              type="text"
                              placeholder="New milestone..."
                              value={newMilestoneText[goal.id] || ''}
                              onChange={(e) => setNewMilestoneText({ ...newMilestoneText, [goal.id]: e.target.value })}
                              onKeyDown={(e) => e.key === 'Enter' && handleAddMilestone(goal.id)}
                              className="flex-1 text-xs px-2.5 py-1.5 rounded-lg border border-emerald-100 bg-white/95 focus:ring-1 focus:ring-emerald-600 shadow-xs text-slate-900"
                            />
                            <button
                              type="button"
                              onClick={() => handleAddMilestone(goal.id)}
                              className="p-1.5 bg-gradient-to-r from-emerald-50 to-teal-50 hover:from-emerald-100 hover:to-teal-100 text-emerald-950 rounded-lg text-xs font-semibold border border-emerald-200/80 cursor-pointer"
                            >
                              <Plus className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Goal Modal */}
      {isCreateOpen && (
        <GoalFormModal
          mode="create"
          initialGoal={{}}
          onCancel={() => setIsCreateOpen(false)}
          onSubmit={handleCreateGoal}
        />
      )}

      {/* Edit Goal Modal */}
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
