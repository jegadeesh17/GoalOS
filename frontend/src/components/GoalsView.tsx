import React, { useState, useEffect } from 'react';
import { Goal, Milestone, goalOSApi } from '../api/client';
import { 
  Plus, 
  CheckCircle2, 
  Circle, 
  Trash2, 
  Flag, 
  X,
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
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newGoal, setNewGoal] = useState<Partial<Goal>>({
    title: '',
    category: 'Career',
    horizon: '1-month',
    priority: 1,
    reason: '',
    success_criteria: '',
    progress: 0.0,
    status: 'active',
  });
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

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGoal.title?.trim()) return;
    try {
      await goalOSApi.createGoal(newGoal);
      setIsModalOpen(false);
      setNewGoal({
        title: '',
        category: 'Career',
        horizon: '1-month',
        priority: 1,
        reason: '',
        success_criteria: '',
        progress: 0.0,
        status: 'active',
      });
      loadGoals();
    } catch (err) {
      console.error('Failed to create goal:', err);
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
      gradient: 'from-emerald-400 to-teal-500'
    },
    { 
      key: '1-year', 
      title: '1-Year Horizons', 
      desc: 'Strategic compounding milestones & skill expansion', 
      icon: Calendar,
      gradient: 'from-indigo-600 to-purple-600'
    },
    { 
      key: '5-year', 
      title: '5-Year Vision', 
      desc: 'Long-term life trajectory & identity architecture', 
      icon: Compass,
      gradient: 'from-amber-400 to-rose-400'
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
      <div className="glass-panel rounded-3xl p-6 sm:p-7 shadow-celestial border border-white/80 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-indigo-700 mb-1">
            <span className="flex items-center space-x-1 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-100 shadow-sm font-semibold">
              <Target className="w-3.5 h-3.5 text-indigo-600" />
              <span>Multi-Horizon Architecture</span>
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Goals & Horizons Board</h2>
          <p className="text-xs text-slate-500 mt-0.5 font-normal">
            Bridge 5-year life vision down to daily 1-month execution sprints.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center justify-center space-x-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-full text-xs font-semibold shadow-sm transition-all"
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
              <div className="glass-panel rounded-3xl p-4 sm:p-5 shadow-celestial border border-white/80">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-700">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-sm text-slate-900">{col.title}</h3>
                  </div>
                  <span className="text-xs font-semibold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full border border-indigo-100">
                    {columnGoals.length}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1 font-normal">{col.desc}</p>
              </div>

              {/* Goal Cards List */}
              <div className="space-y-3.5">
                {columnGoals.length === 0 ? (
                  <div className="glass-panel rounded-3xl border border-dashed border-indigo-200/70 p-6 text-center text-xs text-slate-400 font-normal">
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
                        className="glass-card-interactive rounded-3xl p-5 space-y-3 border border-white/80 shadow-celestial"
                      >
                        {/* Title & Category Badge */}
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="text-xs uppercase font-semibold bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 px-2 py-0.5 rounded-md border border-indigo-200">
                                {goal.category}
                              </span>
                              <span className="text-xs font-mono text-slate-400">P{goal.priority}</span>
                            </div>
                            <h4 className="font-bold text-sm text-slate-900 leading-snug">{goal.title}</h4>
                          </div>

                          <button
                            type="button"
                            onClick={() => handleDeleteGoal(goal.id)}
                            className="text-slate-300 hover:text-rose-500 transition-colors p-1"
                            title="Delete goal"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>

                        {goal.reason && (
                          <p className="text-xs text-slate-600 bg-white/80 p-2.5 rounded-xl border border-indigo-100/70">
                            <strong className="text-slate-800">Motivation:</strong> {goal.reason}
                          </p>
                        )}

                        {/* Progress Bar */}
                        <div>
                          <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                            <span>Progress</span>
                            <span className="text-indigo-700 font-bold">{progressPercent}%</span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden p-0.5 border border-indigo-100">
                            <div
                              className={`bg-gradient-to-r ${col.gradient} h-full rounded-full transition-all duration-500`}
                              style={{ width: `${progressPercent}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* Milestones Checklist */}
                        <div className="space-y-1.5 pt-2.5 border-t border-indigo-100/60">
                          <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                            <span className="flex items-center space-x-1">
                              <Flag className="w-3.5 h-3.5 text-indigo-600" />
                              <span>Milestones</span>
                            </span>
                            <span className="text-xs text-indigo-600 font-medium">
                              {completedMilestones.length}/{milestones.length}
                            </span>
                          </div>

                          <div className="space-y-1">
                            {milestones.map((ms) => {
                              const isCompleted = ms.status === 'completed';
                              return (
                                <div
                                  key={ms.id}
                                  className="flex items-center justify-between text-xs p-1.5 rounded-lg hover:bg-white transition-all"
                                >
                                  <button
                                    type="button"
                                    onClick={() => handleToggleMilestone(ms)}
                                    className="flex items-center space-x-2 text-left flex-1 min-w-0"
                                  >
                                    {isCompleted ? (
                                      <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                                    ) : (
                                      <Circle className="w-4 h-4 text-indigo-300 flex-shrink-0" />
                                    )}
                                    <span className={`truncate ${isCompleted ? 'line-through text-slate-400' : 'text-slate-800 font-normal'}`}>
                                      {ms.title}
                                    </span>
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
                              className="flex-1 text-xs px-2.5 py-1.5 rounded-lg border border-indigo-100 bg-white/90 focus:ring-1 focus:ring-indigo-500 shadow-sm"
                            />
                            <button
                              type="button"
                              onClick={() => handleAddMilestone(goal.id)}
                              className="p-1.5 bg-gradient-to-r from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 text-indigo-900 rounded-lg text-xs font-semibold border border-indigo-200"
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
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel rounded-3xl border border-white max-w-lg w-full p-6 space-y-4 shadow-celestial-lg animate-fadeIn">
            <div className="flex items-center justify-between pb-2 border-b border-indigo-100/60">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-indigo-600 text-white">
                  <Target className="w-4 h-4" />
                </div>
                <h3 className="font-bold text-base text-slate-900">Add New Goal</h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateGoal} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Goal Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Master Multi-Agent Systems"
                  value={newGoal.title}
                  onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
                  className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Horizon
                  </label>
                  <select
                    value={newGoal.horizon}
                    onChange={(e) => setNewGoal({ ...newGoal, horizon: e.target.value })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-indigo-100 bg-white/90 text-slate-800 shadow-sm font-medium"
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
                    value={newGoal.category}
                    onChange={(e) => setNewGoal({ ...newGoal, category: e.target.value })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-indigo-100 bg-white/90 text-slate-800 shadow-sm font-medium"
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
                  value={newGoal.reason || ''}
                  onChange={(e) => setNewGoal({ ...newGoal, reason: e.target.value })}
                  className="w-full text-sm px-3.5 py-2 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm resize-none"
                />
              </div>

              <div className="flex items-center justify-end space-x-2.5 pt-2 border-t border-indigo-100/60">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-full text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-full text-xs font-semibold shadow-sm"
                >
                  Save Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
