import React, { useState, useEffect } from 'react';
import { goalOSApi, Goal } from '../api/client';
import { 
  Sparkles, 
  Sun, 
  Moon, 
  Calendar, 
  Compass, 
  Target, 
  CheckCircle, 
  AlertCircle, 
  Brain, 
  Lightbulb, 
  ShieldCheck, 
  Sparkle 
} from 'lucide-react';

interface AICoachViewProps {
  initialMode?: 'morning' | 'evening' | 'weekly' | 'future-self' | 'goal-alignment';
}

export const AICoachView: React.FC<AICoachViewProps> = ({ initialMode = 'morning' }) => {
  const [mode, setMode] = useState<'morning' | 'evening' | 'weekly' | 'future-self' | 'goal-alignment'>(initialMode);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [selectedGoalId, setSelectedGoalId] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [coachingResult, setCoachingResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    goalOSApi.getGoals({ status: 'active' }).then((data) => {
      setGoals(data);
      if (data.length > 0) setSelectedGoalId(data[0].id);
    }).catch(console.error);
  }, []);

  const handleRunCoach = async () => {
    try {
      setLoading(true);
      setError(null);
      setCoachingResult(null);

      let result: any = null;
      if (mode === 'morning') {
        const todayLog = await goalOSApi.getTodayJournal();
        let tasks = [];
        if (todayLog.planned_tasks) {
          try { tasks = JSON.parse(todayLog.planned_tasks); } catch {}
        }
        result = await goalOSApi.morningCoach({
          target_date: todayLog.date,
          gratitude: todayLog.gratitude || '',
          plans_text: todayLog.top_priority || '',
          tasks: tasks,
          sleep_hours: todayLog.sleep_hours || undefined,
          sleep_quality: todayLog.sleep_quality || undefined,
          mood_morning: todayLog.mood_morning || undefined,
          intention: todayLog.intention || undefined,
          top_priority: todayLog.top_priority || undefined,
        });
      } else if (mode === 'evening') {
        const todayLog = await goalOSApi.getTodayJournal();
        result = await goalOSApi.eveningCoach({
          target_date: todayLog.date,
          journal_entry: todayLog.journal_entry || '',
          deep_work_hours: todayLog.deep_work_hours || undefined,
          mood_evening: todayLog.mood_evening || undefined,
          one_win: todayLog.one_win || '',
          one_lesson: todayLog.one_lesson || '',
          takeaway: todayLog.takeaway || '',
        });
      } else if (mode === 'weekly') {
        result = await goalOSApi.weeklyCoach();
      } else if (mode === 'future-self') {
        result = await goalOSApi.futureSelfCoach();
      } else if (mode === 'goal-alignment') {
        if (!selectedGoalId) {
          setError('Please select an active goal to evaluate.');
          setLoading(false);
          return;
        }
        result = await goalOSApi.goalAlignmentCoach(selectedGoalId);
      }

      setCoachingResult(result);
    } catch (err: any) {
      console.error('Coaching run failed:', err);
      setError(err?.response?.data?.detail || 'Coaching generation failed. Ensure your OpenRouter API key is configured or local fallback rules will apply.');
    } finally {
      setLoading(false);
    }
  };

  const modeOptions = [
    { id: 'morning', label: 'Morning Planning', icon: Sun, desc: 'Priorities, mindset & daily focus setup' },
    { id: 'evening', label: 'Evening Review', icon: Moon, desc: 'Win consolidation & lesson extraction' },
    { id: 'weekly', label: 'Weekly Sync', icon: Calendar, desc: 'Longitudinal pacing & weekly review' },
    { id: 'future-self', label: 'Future Self', icon: Compass, desc: '10-year identity & horizon alignment' },
    { id: 'goal-alignment', label: 'Goal Alignment', icon: Target, desc: 'Evaluate goals against daily execution' },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-3xl p-6 sm:p-7 shadow-celestial border border-white/80 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-extrabold uppercase tracking-wider text-indigo-700 mb-1.5">
              <span className="flex items-center space-x-1.5 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100 shadow-sm">
                <Sparkle className="w-3 h-3 text-amber-500 fill-amber-400" />
                <span>AI Coaching Engine</span>
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">AI Coach Studio</h2>
            <p className="text-xs text-slate-500 mt-1 font-medium">
              Deterministic memory grounding + multi-horizon agent coaching synthesis.
            </p>
          </div>

          <button
            onClick={handleRunCoach}
            disabled={loading}
            className="flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500 hover:opacity-95 disabled:opacity-50 text-white px-6 py-3 rounded-full text-xs font-extrabold shadow-md shadow-indigo-500/25 transition-all"
          >
            <Sparkles className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Synthesizing Coaching...' : 'Run AI Coach'}</span>
          </button>
        </div>

        {/* Pipeline Selector Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mt-6">
          {modeOptions.map((opt) => {
            const Icon = opt.icon;
            const isSelected = mode === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => {
                  setMode(opt.id);
                  setCoachingResult(null);
                  setError(null);
                }}
                className={`p-4 rounded-2xl border text-left transition-all ${
                  isSelected
                    ? 'bg-gradient-to-br from-white via-indigo-50/60 to-purple-50/50 border-indigo-300 ring-2 ring-indigo-200/80 shadow-celestial scale-[1.02]'
                    : 'glass-card-interactive border-slate-200/80 hover:border-indigo-200'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1.5">
                  <div className={`p-1.5 rounded-xl ${isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className={`text-xs font-black ${isSelected ? 'text-indigo-950' : 'text-slate-800'}`}>
                    {opt.label}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 leading-snug line-clamp-2 font-medium">{opt.desc}</p>
              </button>
            );
          })}
        </div>

        {/* Goal selector if goal-alignment mode */}
        {mode === 'goal-alignment' && (
          <div className="mt-4 pt-4 border-t border-indigo-100/60 flex items-center space-x-3">
            <span className="text-xs font-extrabold text-slate-700">Target Goal:</span>
            <select
              value={selectedGoalId || ''}
              onChange={(e) => setSelectedGoalId(Number(e.target.value))}
              className="text-xs px-3.5 py-2 rounded-2xl border border-indigo-100 bg-white/90 text-slate-800 shadow-sm font-semibold"
            >
              {goals.map((g) => (
                <option key={g.id} value={g.id}>
                  [{g.horizon}] {g.title}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-900 p-4 rounded-2xl flex items-start space-x-3 text-xs shadow-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">Notice</p>
            <p className="mt-0.5 font-medium">{error}</p>
          </div>
        </div>
      )}

      {/* Loading state animation */}
      {loading && (
        <div className="glass-panel rounded-3xl p-12 text-center space-y-4 shadow-celestial border border-white/80">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-pink-500 flex items-center justify-center mx-auto text-white shadow-md animate-bounce">
            <Brain className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-lg font-black text-slate-900">Synthesizing Coaching Guidance</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto font-medium">
              Querying memory vector store, active goals, and multi-day patterns...
            </p>
          </div>
        </div>
      )}

      {/* Coaching Output View */}
      {coachingResult && (
        <div className="space-y-6">
          {/* Main Mentor Directive Card */}
          <div className="glass-panel rounded-3xl p-7 relative overflow-hidden shadow-celestial-lg border border-indigo-200/80">
            <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-indigo-200/40 via-purple-200/30 to-pink-200/20 rounded-full blur-3xl -z-10"></div>

            <div className="flex items-center space-x-2 text-xs font-bold text-indigo-700 mb-2.5">
              <Lightbulb className="w-4 h-4 text-amber-500 fill-amber-400" />
              <span>Core Mentor Directive</span>
            </div>

            <h3 className="text-2xl font-black text-slate-900 leading-snug tracking-tight">
              &ldquo;{coachingResult.mentor_rule || coachingResult.rule || coachingResult.core_insight || coachingResult.coaching || 'Focus on relentless execution of today\'s #1 priority.'}&rdquo;
            </h3>

            {coachingResult.why_this_rule && (
              <p className="text-sm text-slate-700 mt-4 bg-white/80 p-4.5 rounded-2xl border border-indigo-100 shadow-sm leading-relaxed">
                <strong className="text-indigo-950 font-bold">Why this matters: </strong>
                {coachingResult.why_this_rule}
              </p>
            )}

            {/* Next Immediate Action */}
            {(coachingResult.next_action || coachingResult.immediate_action) && (
              <div className="mt-4 flex items-center space-x-3 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 text-emerald-950 p-4 rounded-2xl text-xs font-semibold shadow-sm">
                <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                <span>
                  <strong className="font-extrabold text-emerald-900">Next Action: </strong>
                  {coachingResult.next_action || coachingResult.immediate_action}
                </span>
              </div>
            )}

            {/* Meta & Evidence Badges */}
            <div className="mt-6 pt-4 border-t border-indigo-100/60 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center space-x-2">
                <span className="text-slate-500 font-medium">Source:</span>
                <span className="font-mono font-bold bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded-full border border-indigo-200/70">
                  {coachingResult.source || 'agent_coach'}
                </span>
                {coachingResult.confidence && (
                  <span className="font-mono text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200 font-bold">
                    {Math.round(coachingResult.confidence * 100)}% Confidence
                  </span>
                )}
              </div>

              {coachingResult.tools_used && Array.isArray(coachingResult.tools_used) && (
                <div className="flex items-center space-x-1.5 text-slate-500 font-medium">
                  <ShieldCheck className="w-4 h-4 text-indigo-600" />
                  <span>Grounded via: {coachingResult.tools_used.join(', ')}</span>
                </div>
              )}
            </div>
          </div>

          {/* Full Structured Schema */}
          <div className="glass-panel rounded-3xl p-6 shadow-celestial border border-white/80">
            <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-3">
              Full Structured Output
            </h4>
            <pre className="bg-white/90 text-slate-800 p-4 rounded-2xl text-xs font-mono overflow-x-auto border border-indigo-100 max-h-72 shadow-inner">
              {JSON.stringify(coachingResult, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
