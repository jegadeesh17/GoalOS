import React, { useEffect, useState } from 'react';
import { DailyLog, YearDayBlock, TaskItem, goalOSApi } from '../api/client';
import { 
  X, 
  Calendar, 
  CheckCircle2, 
  Circle, 
  Clock, 
  Sparkles, 
  Target, 
  Trophy, 
  Lightbulb, 
  ExternalLink, 
  Flame, 
  Moon, 
  Zap, 
  AlertCircle 
} from 'lucide-react';

interface DayDetailDrawerProps {
  dateStr: string | null;
  daySummary: YearDayBlock | null;
  onClose: () => void;
  onOpenInJournal: (dateStr: string) => void;
}

export const DayDetailDrawer: React.FC<DayDetailDrawerProps> = ({
  dateStr,
  daySummary,
  onClose,
  onOpenInJournal,
}) => {
  const [log, setLog] = useState<DailyLog | null>(null);
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState<TaskItem[]>([]);

  useEffect(() => {
    if (!dateStr) return;

    let isMounted = true;
    const fetchDayData = async () => {
      try {
        setLoading(true);
        const data = await goalOSApi.getJournalByDate(dateStr);
        if (isMounted) {
          setLog(data);

          // Parse tasks
          if (data.planned_tasks) {
            try {
              const parsed = JSON.parse(data.planned_tasks);
              if (Array.isArray(parsed)) {
                setTasks(parsed);
              } else {
                setTasks([]);
              }
            } catch {
              const lines = data.planned_tasks.split('\n').filter(Boolean);
              setTasks(
                lines.map((text, idx) => ({
                  id: `${Date.now()}-${idx}`,
                  text: text.replace(/^\d+[\.\)]\s*/, '').replace(/\(tick\)|\(x\)/gi, '').trim(),
                  priority: 1,
                  completed: text.toLowerCase().includes('tick') || text.includes('✓'),
                }))
              );
            }
          } else {
            setTasks([]);
          }
        }
      } catch (err) {
        console.error('Failed to load day details:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDayData();

    return () => {
      isMounted = false;
    };
  }, [dateStr]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!dateStr) return null;

  const dateObj = new Date(dateStr + 'T00:00:00');
  const formattedDate = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(dateObj);

  const isToday = daySummary?.status === 'today';
  const isFuture = daySummary?.status === 'future';
  const isProductive = daySummary?.is_productive;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs transition-opacity duration-300 ease-out" 
        onClick={onClose} 
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-lg bg-white/95 backdrop-blur-2xl shadow-2xl border-l border-emerald-100 flex flex-col h-full z-10 overflow-y-auto animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="p-6 border-b border-emerald-100/70 bg-gradient-to-b from-emerald-50/50 to-white sticky top-0 z-20 backdrop-blur-md">
          <div className="flex items-center justify-between gap-3 mb-2">
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-xl bg-emerald-100/70 text-emerald-800">
                <Calendar className="w-5 h-5 text-emerald-700" />
              </span>
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 font-mono">
                  Day {daySummary?.day_of_year || '--'} of 365
                </span>
                <h3 className="text-lg font-bold text-slate-900 leading-snug">{formattedDate}</h3>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100/80 rounded-full transition-all cursor-pointer"
              aria-label="Close day inspector"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Status Badge */}
          <div className="flex items-center gap-2 mt-3">
            {isProductive ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-300 shadow-forest-xs">
                <Flame className="w-3.5 h-3.5 text-emerald-700 fill-emerald-600" />
                <span>Productive Day</span>
              </span>
            ) : isToday ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300 shadow-forest-xs">
                <Sparkles className="w-3.5 h-3.5 text-amber-700" />
                <span>Today (In Progress)</span>
              </span>
            ) : isFuture ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Future Horizon</span>
              </span>
            ) : daySummary?.has_log ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-slate-500" />
                <span>Logged &middot; Light Execution</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-50 text-slate-500 border border-slate-200">
                <AlertCircle className="w-3.5 h-3.5 text-slate-400" />
                <span>No Journal Log Recorded</span>
              </span>
            )}

            {daySummary?.productivity_score !== null && daySummary?.productivity_score !== undefined && (
              <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                <span>Score:</span>
                <strong className="font-bold">{Math.round(daySummary.productivity_score)}/100</strong>
              </span>
            )}
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-6 space-y-6">
          {loading ? (
            <div className="space-y-4 animate-pulse">
              <div className="h-20 bg-slate-100 rounded-2xl"></div>
              <div className="h-32 bg-slate-100 rounded-2xl"></div>
              <div className="h-28 bg-slate-100 rounded-2xl"></div>
            </div>
          ) : !daySummary?.has_log && !log?.top_priority && !log?.journal_entry ? (
            <div className="text-center py-10 px-4 glass-panel rounded-2xl border border-dashed border-emerald-200/80">
              <Calendar className="w-10 h-10 text-emerald-600/40 mx-auto mb-3" />
              <h4 className="text-sm font-bold text-slate-800">No Structured Data Yet</h4>
              <p className="text-xs text-slate-500 max-w-xs mx-auto mt-1 mb-5">
                {isFuture
                  ? 'This day is in the future. Plan ahead or set goals to get ready.'
                  : 'You have not recorded a journal entry or morning/evening reflection for this date.'}
              </p>
              <button
                onClick={() => {
                  onOpenInJournal(dateStr);
                  onClose();
                }}
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-xl shadow-forest-xs transition-all cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{isFuture ? 'Plan Ahead in Journal' : 'Log This Day in Journal'}</span>
              </button>
            </div>
          ) : (
            <>
              {/* Metric Highlights Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="glass-card-interactive p-3 rounded-2xl border border-emerald-100/70 bg-gradient-to-br from-white to-emerald-50/30">
                  <div className="flex items-center space-x-1 text-[11px] font-medium text-emerald-800">
                    <Clock className="w-3 h-3 text-emerald-600" />
                    <span>Deep Work</span>
                  </div>
                  <div className="text-base font-bold text-slate-900 mt-1">
                    {log?.deep_work_hours !== null && log?.deep_work_hours !== undefined
                      ? `${log.deep_work_hours} hrs`
                      : '--'}
                  </div>
                </div>

                <div className="glass-card-interactive p-3 rounded-2xl border border-emerald-100/70 bg-gradient-to-br from-white to-teal-50/30">
                  <div className="flex items-center space-x-1 text-[11px] font-medium text-teal-800">
                    <Target className="w-3 h-3 text-teal-600" />
                    <span>Tasks Rate</span>
                  </div>
                  <div className="text-base font-bold text-slate-900 mt-1">
                    {daySummary?.tasks_total_count && daySummary.tasks_total_count > 0
                      ? `${daySummary.tasks_completed_count}/${daySummary.tasks_total_count}`
                      : log?.task_completion_rate !== null && log?.task_completion_rate !== undefined
                      ? `${Math.round(log.task_completion_rate * 100)}%`
                      : '--'}
                  </div>
                </div>

                <div className="glass-card-interactive p-3 rounded-2xl border border-emerald-100/70 bg-gradient-to-br from-white to-amber-50/30">
                  <div className="flex items-center space-x-1 text-[11px] font-medium text-amber-800">
                    <Moon className="w-3 h-3 text-amber-600" />
                    <span>Sleep</span>
                  </div>
                  <div className="text-base font-bold text-slate-900 mt-1">
                    {log?.sleep_hours ? `${log.sleep_hours} hrs` : '--'}
                  </div>
                </div>

                <div className="glass-card-interactive p-3 rounded-2xl border border-emerald-100/70 bg-gradient-to-br from-white to-slate-50/40">
                  <div className="flex items-center space-x-1 text-[11px] font-medium text-slate-700">
                    <Zap className="w-3 h-3 text-emerald-600" />
                    <span>Energy</span>
                  </div>
                  <div className="text-base font-bold text-slate-900 mt-1">
                    {log?.energy_level ? `${log.energy_level}/5` : '--'}
                  </div>
                </div>
              </div>

              {/* Top Priority & Morning Routine */}
              <div className="glass-panel p-4 rounded-2xl border border-emerald-100/80 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-900 flex items-center space-x-1.5">
                    <Target className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Morning Priorities</span>
                  </span>
                  {log?.morning_completed && (
                    <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full">
                      Routine Done
                    </span>
                  )}
                </div>

                {log?.top_priority ? (
                  <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-50/80 to-teal-50/50 border border-emerald-200/80">
                    <div className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider">
                      #1 Priority
                    </div>
                    <div className="text-sm font-semibold text-slate-900 mt-0.5">
                      {log.top_priority}
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-400 italic">No top priority specified</div>
                )}

                {(log?.supporting_task_1 || log?.supporting_task_2) && (
                  <div className="space-y-1.5 pt-1">
                    {log.supporting_task_1 && (
                      <div className="text-xs text-slate-700 flex items-center space-x-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <span>{log.supporting_task_1}</span>
                      </div>
                    )}
                    {log.supporting_task_2 && (
                      <div className="text-xs text-slate-700 flex items-center space-x-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <span>{log.supporting_task_2}</span>
                      </div>
                    )}
                  </div>
                )}

                {log?.intention && (
                  <div className="pt-2 border-t border-emerald-50">
                    <span className="text-[11px] font-medium text-slate-500">Intention:</span>
                    <p className="text-xs font-serif italic text-slate-800 mt-0.5">"{log.intention}"</p>
                  </div>
                )}

                {log?.gratitude && (
                  <div className="pt-1">
                    <span className="text-[11px] font-medium text-slate-500">Gratitude:</span>
                    <p className="text-xs text-slate-700 mt-0.5">{log.gratitude}</p>
                  </div>
                )}
              </div>

              {/* Tasks List */}
              {tasks.length > 0 && (
                <div className="glass-panel p-4 rounded-2xl border border-emerald-100/80 space-y-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-800">
                    <span className="flex items-center space-x-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                      <span>Planned Tasks</span>
                    </span>
                    <span className="text-slate-500 font-mono font-normal">
                      {tasks.filter((t) => t.completed).length} / {tasks.length} Done
                    </span>
                  </div>

                  <div className="space-y-1.5 pt-1 max-h-48 overflow-y-auto">
                    {tasks.map((task, idx) => (
                      <div
                        key={task.id || idx}
                        className={`flex items-start space-x-2.5 text-xs p-2 rounded-xl transition-all ${
                          task.completed
                            ? 'bg-emerald-50/60 text-slate-500 line-through'
                            : 'bg-white/70 text-slate-800 border border-slate-100'
                        }`}
                      >
                        {task.completed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                        ) : (
                          <Circle className="w-4 h-4 text-slate-300 mt-0.5 shrink-0" />
                        )}
                        <span className="flex-1 leading-snug">{task.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Evening Reflection & Wins */}
              <div className="glass-panel p-4 rounded-2xl border border-emerald-100/80 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-900 flex items-center space-x-1.5">
                    <Trophy className="w-3.5 h-3.5 text-amber-600" />
                    <span>Evening Reflection</span>
                  </span>
                  {log?.evening_completed && (
                    <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full">
                      Reflection Done
                    </span>
                  )}
                </div>

                {log?.one_win && (
                  <div className="p-3 rounded-xl bg-gradient-to-r from-amber-50/60 to-white border border-amber-200/70">
                    <div className="text-[11px] font-semibold text-amber-900 uppercase tracking-wider flex items-center space-x-1">
                      <Sparkles className="w-3 h-3 text-amber-600" />
                      <span>The Big Win</span>
                    </div>
                    <div className="text-xs font-medium text-slate-900 mt-1">{log.one_win}</div>
                  </div>
                )}

                {log?.one_lesson && (
                  <div className="p-3 rounded-xl bg-gradient-to-r from-teal-50/60 to-white border border-teal-200/70">
                    <div className="text-[11px] font-semibold text-teal-900 uppercase tracking-wider flex items-center space-x-1">
                      <Lightbulb className="w-3 h-3 text-teal-700" />
                      <span>Core Lesson</span>
                    </div>
                    <div className="text-xs font-medium text-slate-900 mt-1">{log.one_lesson}</div>
                  </div>
                )}

                {log?.takeaway && (
                  <div className="text-xs text-slate-700 pt-1">
                    <span className="font-semibold text-slate-900">Key Takeaway: </span>
                    {log.takeaway}
                  </div>
                )}

                {log?.journal_entry && (
                  <div className="pt-2 border-t border-emerald-50">
                    <span className="text-[11px] font-medium text-slate-500">Journal Notes:</span>
                    <p className="text-xs text-slate-700 mt-1 whitespace-pre-wrap leading-relaxed max-h-36 overflow-y-auto font-sans p-2.5 rounded-xl bg-slate-50/80">
                      {log.journal_entry}
                    </p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer CTA */}
        <div className="p-4 border-t border-emerald-100/70 bg-white/95 sticky bottom-0 z-20 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-all cursor-pointer"
          >
            Close
          </button>

          <button
            onClick={() => {
              onOpenInJournal(dateStr);
              onClose();
            }}
            className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-xl shadow-forest-xs transition-all cursor-pointer"
          >
            <span>Open & Edit in Journal</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
