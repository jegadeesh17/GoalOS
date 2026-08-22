import React, { useState, useEffect } from 'react';
import { DailyLog, TaskItem, goalOSApi, Goal } from '../api/client';
import { 
  Sun, 
  Moon, 
  CheckCircle2, 
  Circle, 
  Plus, 
  Trash2, 
  Save, 
  Sparkles, 
  ChevronLeft, 
  ChevronRight, 
  Clock, 
  Heart, 
  Zap, 
  Smile,
  Target
} from 'lucide-react';

interface JournalViewProps {
  onTriggerCoach?: (mode: 'morning' | 'evening') => void;
}

export const JournalView: React.FC<JournalViewProps> = ({ onTriggerCoach }) => {
  const [currentDate, setCurrentDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [log, setLog] = useState<DailyLog | null>(null);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [activeTab, setActiveTab] = useState<'morning' | 'evening'>('morning');
  const [loading, setLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [newTaskText, setNewTaskText] = useState('');
  const [newTaskGoalId, setNewTaskGoalId] = useState<number | undefined>(undefined);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [logData, goalsData] = await Promise.all([
          goalOSApi.getJournalByDate(currentDate),
          goalOSApi.getGoals({ status: 'active' }),
        ]);
        setLog(logData);
        setGoals(goalsData);

        if (logData.planned_tasks) {
          try {
            const parsed = JSON.parse(logData.planned_tasks);
            if (Array.isArray(parsed)) setTasks(parsed);
          } catch {
            setTasks([]);
          }
        } else {
          setTasks([]);
        }
      } catch (err) {
        console.error('Failed to load journal log:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [currentDate]);

  const handleDateChange = (offsetDays: number) => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + offsetDays);
    setCurrentDate(d.toISOString().split('T')[0]);
  };

  const handleSave = async () => {
    if (!log) return;
    try {
      setSaveStatus('Saving to SQLite...');
      const payload: Partial<DailyLog> & { date: string } = {
        ...log,
        date: currentDate,
        planned_tasks: JSON.stringify(tasks),
      };
      const updated = await goalOSApi.upsertJournal(payload);
      setLog(updated);
      const timeStr = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: 'numeric', second: 'numeric' }).format(new Date());
      setSaveStatus(`Journal Saved at ${timeStr}`);
      setTimeout(() => setSaveStatus(null), 4000);
    } catch (err) {
      console.error('Failed to save journal:', err);
      setSaveStatus('Failed to save log');
    }
  };

  const handleAddTask = () => {
    if (!newTaskText.trim()) return;
    const newTask: TaskItem = {
      id: Date.now().toString(),
      text: newTaskText.trim(),
      priority: 1,
      completed: false,
      goal_id: newTaskGoalId || null,
    };
    setTasks([...tasks, newTask]);
    setNewTaskText('');
    setNewTaskGoalId(undefined);
  };

  const toggleTask = (index: number) => {
    const updated = [...tasks];
    updated[index].completed = !updated[index].completed;
    setTasks(updated);
  };

  const removeTask = (index: number) => {
    const updated = tasks.filter((_, i) => i !== index);
    setTasks(updated);
  };

  if (loading || !log) {
    return (
      <div className="glass-panel rounded-3xl p-8 animate-pulse">
        <div className="h-5 bg-slate-100 rounded-full w-1/4 mb-4"></div>
        <div className="h-48 bg-slate-50/60 rounded-2xl"></div>
      </div>
    );
  }

  const isToday = currentDate === new Date().toISOString().split('T')[0];

  return (
    <div className="space-y-6">
      {/* Date Header & Controls */}
      <div className="glass-panel rounded-3xl p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-celestial border border-white/80">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleDateChange(-1)}
            className="p-1.5 rounded-xl border border-indigo-100 text-slate-600 hover:bg-white hover:text-indigo-600 transition-all shadow-sm"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <div>
            <div className="flex items-center space-x-2">
              <input
                type="date"
                value={currentDate}
                onChange={(e) => setCurrentDate(e.target.value)}
                className="font-bold text-lg text-slate-900 bg-transparent border-0 focus:ring-2 focus:ring-indigo-500 rounded-lg p-0 cursor-pointer"
              />
              {isToday && (
                <span className="text-xs font-semibold bg-indigo-600 text-white px-2.5 py-0.5 rounded-full shadow-sm">
                  Today
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 font-normal">Daily Intentions & Execution Journal</p>
          </div>

          <button
            onClick={() => handleDateChange(1)}
            className="p-1.5 rounded-xl border border-indigo-100 text-slate-600 hover:bg-white hover:text-indigo-600 transition-all shadow-sm"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Tab switcher & Save Action */}
        <div className="flex items-center space-x-3">
          <div className="flex bg-slate-100/80 p-1 rounded-full border border-slate-200/60 backdrop-blur-md text-xs font-semibold">
            <button
              onClick={() => setActiveTab('morning')}
              className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full transition-all ${
                activeTab === 'morning'
                  ? 'bg-amber-500 text-white shadow-sm font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sun className="w-3.5 h-3.5" />
              <span>Morning Planning</span>
            </button>
            <button
              onClick={() => setActiveTab('evening')}
              className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full transition-all ${
                activeTab === 'evening'
                  ? 'bg-indigo-600 text-white shadow-sm font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Moon className="w-3.5 h-3.5" />
              <span>Evening Review</span>
            </button>
          </div>

          <button
            onClick={handleSave}
            className="flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-1.5 rounded-full text-xs font-semibold shadow-sm transition-all"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Journal</span>
          </button>
        </div>
      </div>

      {saveStatus && (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 text-emerald-950 text-xs font-medium px-4 py-2.5 rounded-2xl flex items-center justify-between shadow-sm animate-fadeIn">
          <span>{saveStatus}</span>
        </div>
      )}

      {/* Main Journal Body */}
      {activeTab === 'morning' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Morning Intentions */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-4 shadow-celestial border border-white/80">
              <h3 className="font-bold text-slate-900 flex items-center space-x-2 text-sm">
                <Sun className="w-4 h-4 text-amber-500" />
                <span>Morning Intentions & Focus</span>
              </h3>

              <div className="space-y-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    1. Top Priority for Today
                  </label>
                  <input
                    type="text"
                    placeholder="If only one thing gets done today, what must it be?"
                    value={log.top_priority || ''}
                    onChange={(e) => setLog({ ...log, top_priority: e.target.value })}
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/80 shadow-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    2. Primary Intention & Mindset
                  </label>
                  <input
                    type="text"
                    placeholder="How do you choose to show up today?"
                    value={log.intention || ''}
                    onChange={(e) => setLog({ ...log, intention: e.target.value })}
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/80 shadow-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    3. Gratitude & Grounding
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Three specific things you are grateful for right now..."
                    value={log.gratitude || ''}
                    onChange={(e) => setLog({ ...log, gratitude: e.target.value })}
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/80 shadow-sm resize-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    4. Potential Obstacles & Countermeasures
                  </label>
                  <input
                    type="text"
                    placeholder="What might try to derail you, and how will you handle it?"
                    value={log.anxiety || ''}
                    onChange={(e) => setLog({ ...log, anxiety: e.target.value })}
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/80 shadow-sm"
                  />
                </div>
              </div>
            </div>

            {/* Planned Tasks Linked to Horizon Goals */}
            <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-3.5 shadow-celestial border border-white/80">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-900 flex items-center space-x-2 text-sm">
                  <Target className="w-4 h-4 text-indigo-600" />
                  <span>Planned Tasks & Goal Alignment</span>
                </h3>
                <span className="text-xs text-indigo-700 font-semibold bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-100">
                  {tasks.filter((t) => t.completed).length} / {tasks.length} Completed
                </span>
              </div>

              {/* Task list */}
              <div className="space-y-2">
                {tasks.length === 0 ? (
                  <p className="text-xs text-slate-400 italic py-1">No tasks added yet for today.</p>
                ) : (
                  tasks.map((task, idx) => {
                    const linkedGoal = goals.find((g) => g.id === task.goal_id);
                    return (
                      <div
                        key={task.id || idx}
                        className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                          task.completed
                            ? 'bg-slate-50/70 border-slate-200 text-slate-400'
                            : 'glass-card-interactive border-indigo-100/80 text-slate-800'
                        }`}
                      >
                        <div className="flex items-center space-x-2.5 flex-1 min-w-0 mr-2">
                          <button
                            type="button"
                            onClick={() => toggleTask(idx)}
                            className="text-slate-400 hover:text-indigo-600 transition-colors flex-shrink-0"
                          >
                            {task.completed ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            ) : (
                              <Circle className="w-4 h-4 text-indigo-300" />
                            )}
                          </button>
                          <span className={`text-xs truncate ${task.completed ? 'line-through' : 'font-medium'}`}>
                            {task.text}
                          </span>
                          {linkedGoal && (
                            <span className="text-xs font-medium bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 px-2 py-0.5 rounded-md border border-indigo-200 flex-shrink-0">
                              {linkedGoal.title}
                            </span>
                          )}
                        </div>

                        <button
                          type="button"
                          onClick={() => removeTask(idx)}
                          className="text-slate-300 hover:text-rose-500 transition-colors p-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Add Task Input */}
              <div className="pt-1 flex flex-col sm:flex-row items-center gap-2">
                <input
                  type="text"
                  placeholder="New task description..."
                  value={newTaskText}
                  onChange={(e) => setNewTaskText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddTask()}
                  className="flex-1 text-xs px-3.5 py-2 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm w-full"
                />

                <select
                  value={newTaskGoalId || ''}
                  onChange={(e) => setNewTaskGoalId(e.target.value ? Number(e.target.value) : undefined)}
                  className="text-xs px-3 py-2 rounded-xl border border-indigo-100 bg-white text-slate-700 w-full sm:w-auto shadow-sm"
                >
                  <option value="">No goal linked</option>
                  {goals.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.title}
                    </option>
                  ))}
                </select>

                <button
                  type="button"
                  onClick={handleAddTask}
                  className="w-full sm:w-auto bg-gradient-to-r from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 text-indigo-900 border border-indigo-200 px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1 transition-all shadow-sm"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add</span>
                </button>
              </div>
            </div>
          </div>

          {/* Morning Vitals Pod */}
          <div className="space-y-6">
            <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-4 shadow-celestial border border-white/80">
              <h3 className="font-bold text-slate-900 text-sm">Morning Vitals</h3>

              {/* Sleep Hours */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center justify-between">
                  <span className="flex items-center space-x-1.5">
                    <Clock className="w-3.5 h-3.5 text-indigo-500" />
                    <span>Sleep Duration</span>
                  </span>
                  <span className="text-indigo-700 font-mono font-bold text-xs">{log.sleep_hours || 7.0} hrs</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="14"
                  step="0.5"
                  value={log.sleep_hours || 7.0}
                  onChange={(e) => setLog({ ...log, sleep_hours: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* Sleep Quality (1-5) */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center space-x-1.5">
                  <Heart className="w-3.5 h-3.5 text-rose-500" />
                  <span>Sleep Quality (1-5)</span>
                </label>
                <div className="grid grid-cols-5 gap-1.5">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setLog({ ...log, sleep_quality: val })}
                      className={`py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                        log.sleep_quality === val
                          ? 'bg-indigo-600 text-white border-transparent shadow-sm'
                          : 'bg-white/80 text-slate-700 border-indigo-100 hover:bg-white'
                      }`}
                    >
                      {val}★
                    </button>
                  ))}
                </div>
              </div>

              {/* Energy Level (1-5) */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center space-x-1.5">
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  <span>Morning Energy (1-5)</span>
                </label>
                <div className="grid grid-cols-5 gap-1.5">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setLog({ ...log, energy_level: val })}
                      className={`py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                        log.energy_level === val
                          ? 'bg-amber-500 text-white border-amber-500 shadow-sm'
                          : 'bg-white/80 text-slate-700 border-indigo-100 hover:bg-white'
                      }`}
                    >
                      {val}
                    </button>
                  ))}
                </div>
              </div>

              {/* Morning Mood (1-5) */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center space-x-1.5">
                  <Smile className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Morning Mood (1-5)</span>
                </label>
                <div className="grid grid-cols-5 gap-1.5">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setLog({ ...log, mood_morning: val })}
                      className={`py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                        log.mood_morning === val
                          ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                          : 'bg-white/80 text-slate-700 border-indigo-100 hover:bg-white'
                      }`}
                    >
                      {val}
                    </button>
                  ))}
                </div>
              </div>

              {/* AI Coaching shortcut */}
              {onTriggerCoach && (
                <div className="pt-2 border-t border-indigo-100/60">
                  <button
                    type="button"
                    onClick={() => {
                      handleSave();
                      onTriggerCoach('morning');
                    }}
                    className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-amber-50 via-rose-50 to-indigo-50 hover:from-amber-100 hover:to-indigo-100 text-indigo-950 border border-indigo-200/80 py-2.5 rounded-2xl text-xs font-semibold transition-all shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    <span>Run Morning AI Coach</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Evening Reflections Tab */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-4 shadow-celestial border border-white/80">
              <h3 className="font-bold text-slate-900 flex items-center space-x-2 text-sm">
                <Moon className="w-4 h-4 text-indigo-600" />
                <span>Evening Review & Retrospective</span>
              </h3>

              <div className="space-y-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    1. One Meaningful Win Today
                  </label>
                  <input
                    type="text"
                    placeholder="What went right? Celebrate even small progress."
                    value={log.one_win || ''}
                    onChange={(e) => setLog({ ...log, one_win: e.target.value })}
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/80 shadow-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    2. One Honest Lesson Learned
                  </label>
                  <input
                    type="text"
                    placeholder="What friction occurred and what does it teach you?"
                    value={log.one_lesson || ''}
                    onChange={(e) => setLog({ ...log, one_lesson: e.target.value })}
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/80 shadow-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    3. Journal Reflections
                  </label>
                  <textarea
                    rows={6}
                    placeholder="Free-form reflection on today's decisions, horizons, and mental state..."
                    value={log.journal_entry || ''}
                    onChange={(e) => setLog({ ...log, journal_entry: e.target.value })}
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/80 shadow-sm resize-none font-sans"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Evening Metrics */}
          <div className="space-y-6">
            <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-4 shadow-celestial border border-white/80">
              <h3 className="font-bold text-slate-900 text-sm">Evening Vitals</h3>

              {/* Deep Work Hours */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center justify-between">
                  <span>Deep Work Blocks</span>
                  <span className="text-indigo-700 font-mono font-bold text-xs">{log.deep_work_hours || 0.0} hrs</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="12"
                  step="0.5"
                  value={log.deep_work_hours || 0.0}
                  onChange={(e) => setLog({ ...log, deep_work_hours: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* Evening Mood (1-5) */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Evening Mood (1-5)
                </label>
                <div className="grid grid-cols-5 gap-1.5">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setLog({ ...log, mood_evening: val })}
                      className={`py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                        log.mood_evening === val
                          ? 'bg-indigo-600 text-white border-transparent shadow-sm'
                          : 'bg-white/80 text-slate-700 border-indigo-100 hover:bg-white'
                      }`}
                    >
                      {val}
                    </button>
                  ))}
                </div>
              </div>

              {/* Workout toggle */}
              <div className="pt-1">
                <label className="flex items-center space-x-2.5 cursor-pointer p-3 rounded-xl border border-indigo-100 bg-white/80 hover:bg-white transition-all shadow-sm">
                  <input
                    type="checkbox"
                    checked={!!log.workout_completed}
                    onChange={(e) => setLog({ ...log, workout_completed: e.target.checked })}
                    className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 border-slate-300"
                  />
                  <span className="text-xs font-semibold text-slate-800">Workout Completed</span>
                </label>
              </div>

              {/* Evening Coach shortcut */}
              {onTriggerCoach && (
                <div className="pt-2 border-t border-indigo-100/60">
                  <button
                    type="button"
                    onClick={() => {
                      handleSave();
                      onTriggerCoach('evening');
                    }}
                    className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 text-indigo-950 border border-indigo-200/80 py-2.5 rounded-2xl text-xs font-semibold transition-all shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Run Evening AI Review</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
