import React, { useState, useEffect, useRef } from 'react';
import { goalOSApi, Goal, CoachSession, CoachMessage } from '../api/client';
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
  Sparkle,
  ListChecks,
  MessageCircle,
  Plus,
  Trash2,
  Send,
  ChevronDown
} from 'lucide-react';

interface AICoachViewProps {
  initialMode?: 'morning' | 'evening' | 'weekly' | 'future-self' | 'goal-alignment';
}

type SubView = 'pipelines' | 'chat';

const ChatBubble: React.FC<{ message: CoachMessage }> = ({ message }) => {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-emerald-700 text-white rounded-2xl rounded-br-md px-4 py-2.5 text-sm shadow-forest-xs whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  const toolNames = (message.tool_calls || []).map((t) => t.tool).filter(Boolean);

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-1.5">
        <div className="glass-card-interactive rounded-2xl rounded-bl-md px-4 py-3 text-sm text-slate-800 border border-emerald-100/80 shadow-forest-xs leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>
        {(message.agent_name || toolNames.length > 0) && (
          <div className="flex items-center flex-wrap gap-x-2.5 gap-y-1 px-1 text-[11px] text-slate-400 font-medium">
            {message.agent_name && <span className="text-emerald-700 font-semibold">{message.agent_name}</span>}
            {toolNames.length > 0 && (
              <span className="flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3 text-emerald-500" />
                <span>{toolNames.join(', ')}</span>
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export const AICoachView: React.FC<AICoachViewProps> = ({ initialMode = 'morning' }) => {
  const [subView, setSubView] = useState<SubView>('pipelines');

  // --- Guided Pipelines state ---
  const [mode, setMode] = useState<'morning' | 'evening' | 'weekly' | 'future-self' | 'goal-alignment'>(initialMode);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [selectedGoalId, setSelectedGoalId] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [coachingResult, setCoachingResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRawOutput, setShowRawOutput] = useState(false);

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
      setShowRawOutput(false);

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
    { id: 'morning', label: 'Morning Planning', icon: Sun, desc: 'Daily focus, priorities & mindset setup' },
    { id: 'evening', label: 'Evening Review', icon: Moon, desc: 'Win consolidation & lesson extraction' },
    { id: 'weekly', label: 'Weekly Sync', icon: Calendar, desc: 'Weekly review & progress check' },
    { id: 'future-self', label: 'Future Self', icon: Compass, desc: '10-year identity & horizon alignment' },
    { id: 'goal-alignment', label: 'Goal Alignment', icon: Target, desc: 'Check active goals against actual execution' },
  ] as const;

  // --- Coach Chat state ---
  const [sessions, setSessions] = useState<CoachSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionsLoaded, setSessionsLoaded] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<CoachMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [remoteAiConsent, setRemoteAiConsent] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadSessions = async () => {
    try {
      setSessionsLoading(true);
      const data = await goalOSApi.listCoachSessions(30);
      setSessions(data);
    } catch (err) {
      console.error('Failed to load coach sessions:', err);
    } finally {
      setSessionsLoading(false);
      setSessionsLoaded(true);
    }
  };

  useEffect(() => {
    if (subView === 'chat' && !sessionsLoaded) loadSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subView]);

  useEffect(() => {
    goalOSApi
      .getSettings()
      .then((s) => setRemoteAiConsent(!!s.remote_ai_consent))
      .catch((err) => console.error('Failed to load AI consent setting:', err));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatSending]);

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setChatError(null);
  };

  const handleSelectSession = async (id: string) => {
    if (id === activeSessionId) return;
    try {
      setChatError(null);
      const session = await goalOSApi.getCoachSession(id);
      setActiveSessionId(session.id);
      setMessages(session.messages);
    } catch (err) {
      console.error('Failed to load coach session:', err);
      setChatError('Could not load that conversation.');
    }
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation permanently?')) return;
    try {
      await goalOSApi.deleteCoachSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) handleNewChat();
    } catch (err) {
      console.error('Failed to delete coach session:', err);
    }
  };

  const handleSendChat = async () => {
    const text = chatInput.trim();
    if (!text || chatSending) return;

    const optimisticMessage: CoachMessage = {
      id: `local-${Date.now()}`,
      session_id: activeSessionId || '',
      role: 'user',
      content: text,
    };
    setMessages((prev) => [...prev, optimisticMessage]);
    setChatInput('');
    setChatSending(true);
    setChatError(null);

    try {
      const res = await goalOSApi.sendChatMessage({
        message: text,
        session_id: activeSessionId || undefined,
        remote_ai_consent: remoteAiConsent,
      });
      setActiveSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: `local-reply-${Date.now()}`,
          session_id: res.session_id,
          role: 'assistant',
          content: res.reply,
          agent_name: res.agent_name,
          tool_calls: res.tools_used.map((t) => ({ tool: t })),
          citations: res.citations,
        },
      ]);
      loadSessions();
    } catch (err: any) {
      console.error('Chat message failed:', err);
      setChatError(err?.response?.data?.detail || 'Message failed to send. Please try again.');
    } finally {
      setChatSending(false);
    }
  };

  const handleChatKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  };

  // Render the pipeline-specific fields each coach actually returns. Without this,
  // future-self (message) and goal-alignment (alignment_narrative/neglected_goals/…)
  // never surface, and every pipeline falls back to the same generic directive.
  const renderStructuredBody = (r: any) => (
    <>
      {r.message && (
        <div className="mt-1.5 space-y-2 text-[15px] leading-relaxed text-forest-950 font-serif">
          {String(r.message).split(/\n\n+/).map((para: string, i: number) => (
            <p key={i}>{para}</p>
          ))}
          {typeof r.written_from_age !== 'undefined' && (
            <p className="text-xs text-slate-500 not-italic font-sans pt-1">— your future self, age {r.written_from_age}</p>
          )}
        </div>
      )}

      {r.alignment_narrative && (
        <p className="mt-1.5 text-sm text-slate-700 leading-relaxed">{r.alignment_narrative}</p>
      )}

      {((Array.isArray(r.aligned_goals) && r.aligned_goals.length > 0) ||
        (Array.isArray(r.neglected_goals) && r.neglected_goals.length > 0)) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
          {Array.isArray(r.aligned_goals) && r.aligned_goals.length > 0 && (
            <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-3.5">
              <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 mb-2">On track</div>
              <ul className="space-y-1.5 text-xs text-emerald-950">
                {r.aligned_goals.map((g: string, i: number) => (
                  <li key={i} className="flex gap-1.5"><span className="text-emerald-600">✓</span><span>{g}</span></li>
                ))}
              </ul>
            </div>
          )}
          {Array.isArray(r.neglected_goals) && r.neglected_goals.length > 0 && (
            <div className="bg-rose-50/70 border border-rose-200 rounded-xl p-3.5">
              <div className="text-[11px] font-bold uppercase tracking-wider text-rose-700 mb-2">Neglected</div>
              <ul className="space-y-1.5 text-xs text-rose-950">
                {r.neglected_goals.map((g: string, i: number) => (
                  <li key={i} className="flex gap-1.5"><span className="text-rose-500">✕</span><span>{g}</span></li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {Array.isArray(r.key_things_referenced) && r.key_things_referenced.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {r.key_things_referenced.map((k: string, i: number) => (
            <span key={i} className="text-[11px] bg-white/90 border border-emerald-100 text-slate-600 px-2 py-0.5 rounded-full">
              {k}
            </span>
          ))}
        </div>
      )}
    </>
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-3xl p-6 sm:p-7 shadow-forest border border-emerald-100/70 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-forest-700 mb-1">
              <span className="flex items-center space-x-1 bg-emerald-50/90 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200/70 shadow-forest-xs font-semibold">
                <Sparkle className="w-3 h-3 text-amber-500 fill-amber-400" />
                <span>AI Guidance</span>
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">AI Coach</h2>
            <p className="text-xs text-slate-500 mt-0.5 font-normal">
              Personal guidance grounded in your daily journals, past lessons, and active goals.
            </p>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            {/* Sub-view Switcher */}
            <div className="flex items-center space-x-1.5 bg-slate-100/80 p-1 rounded-full border border-emerald-100/70 backdrop-blur-md">
              <button
                onClick={() => setSubView('pipelines')}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  subView === 'pipelines' ? 'bg-emerald-700 text-white shadow-forest-xs' : 'text-slate-700 hover:text-slate-900'
                }`}
              >
                <ListChecks className="w-3.5 h-3.5" />
                <span>Guided Pipelines</span>
              </button>
              <button
                onClick={() => setSubView('chat')}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  subView === 'chat' ? 'bg-emerald-700 text-white shadow-forest-xs' : 'text-slate-700 hover:text-slate-900'
                }`}
              >
                <MessageCircle className="w-3.5 h-3.5" />
                <span>Coach Chat</span>
              </button>
            </div>

            {subView === 'pipelines' ? (
              <button
                onClick={handleRunCoach}
                disabled={loading}
                className="flex items-center justify-center space-x-1.5 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white px-5 py-2.5 rounded-full text-xs font-semibold shadow-forest-xs transition-all cursor-pointer"
              >
                <Sparkles className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>{loading ? 'Generating Guidance...' : 'Run AI Coach'}</span>
              </button>
            ) : (
              <button
                onClick={handleNewChat}
                className="flex items-center justify-center space-x-1.5 bg-emerald-700 hover:bg-emerald-800 text-white px-5 py-2.5 rounded-full text-xs font-semibold shadow-forest-xs transition-all cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Chat</span>
              </button>
            )}
          </div>
        </div>

        {subView === 'pipelines' && (
          <>
            {/* Pipeline Selector Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mt-5">
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
                    className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-gradient-to-br from-white via-emerald-50/70 to-teal-50/50 border-emerald-300 ring-1 ring-emerald-300 shadow-forest-xs'
                        : 'glass-card-interactive border-slate-200/80 hover:border-emerald-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2 mb-1">
                      <div className={`p-1.5 rounded-lg ${isSelected ? 'bg-emerald-700 text-white' : 'bg-slate-100 text-slate-500'}`}>
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <span className={`text-xs font-bold ${isSelected ? 'text-emerald-950' : 'text-slate-800'}`}>
                        {opt.label}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 leading-snug line-clamp-2 font-normal">{opt.desc}</p>
                  </button>
                );
              })}
            </div>

            {/* Goal selector if goal-alignment mode */}
            {mode === 'goal-alignment' && (
              <div className="mt-3.5 pt-3 border-t border-emerald-100/60 flex items-center space-x-2.5">
                <span className="text-xs font-semibold text-slate-700">Target Goal:</span>
                <select
                  value={selectedGoalId || ''}
                  onChange={(e) => setSelectedGoalId(Number(e.target.value))}
                  className="text-xs px-3 py-1.5 rounded-xl border border-emerald-100 bg-white/95 text-slate-800 shadow-xs font-medium"
                >
                  {goals.map((g) => (
                    <option key={g.id} value={g.id}>
                      [{g.horizon}] {g.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </>
        )}
      </div>

      {subView === 'pipelines' ? (
        <>
          {/* Error state */}
          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-900 p-3.5 rounded-2xl flex items-start space-x-2.5 text-xs shadow-forest-xs">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Notice</p>
                <p className="mt-0.5 font-normal">{error}</p>
              </div>
            </div>
          )}

          {/* Loading state animation */}
          {loading && (
            <div className="glass-panel rounded-3xl p-10 text-center space-y-3 shadow-forest border border-emerald-100/70">
              <div className="w-12 h-12 rounded-2xl bg-emerald-700 flex items-center justify-center mx-auto text-white shadow-forest-xs animate-bounce">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Synthesizing Coaching Guidance</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto font-normal">
                  Grounded in your goals, journals, and multi-day patterns (auto-routing across high-speed endpoints)...
                </p>
              </div>
            </div>
          )}

          {/* Coaching Output View */}
          {coachingResult && (
            <div className="space-y-6">
              {/* Main Mentor Directive Card */}
              <div className="glass-panel rounded-3xl p-6 sm:p-7 relative overflow-hidden shadow-forest border border-emerald-200/90">
                <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-800 mb-2">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-500 fill-amber-400" />
                  <span>Core Mentor Directive</span>
                </div>

                {(() => {
                  const directive =
                    coachingResult.mentor_rule ||
                    coachingResult.rule ||
                    coachingResult.core_insight ||
                    coachingResult.coaching ||
                    coachingResult.recommendation ||
                    (coachingResult.message || coachingResult.alignment_narrative
                      ? ''
                      : 'Focus on relentless execution of today\'s #1 priority.');
                  return directive ? (
                    <h3 className="text-2xl font-medium text-forest-950 font-serif italic leading-snug tracking-tight">
                      &ldquo;{directive}&rdquo;
                    </h3>
                  ) : null;
                })()}

                {renderStructuredBody(coachingResult)}

                {coachingResult.why_this_rule && (
                  <p className="text-xs text-slate-700 mt-3 bg-white/95 p-3.5 rounded-xl border border-emerald-100 shadow-forest-xs leading-relaxed">
                    <strong className="text-emerald-950 font-semibold">Why this matters: </strong>
                    {coachingResult.why_this_rule}
                  </p>
                )}

                {/* Next Immediate Action */}
                {(coachingResult.next_action || coachingResult.immediate_action) && (
                  <div className="mt-3 flex items-center space-x-2.5 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 text-emerald-950 p-3.5 rounded-xl text-xs font-medium shadow-forest-xs">
                    <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>
                      <strong className="font-semibold text-emerald-900">Next Action: </strong>
                      {coachingResult.next_action || coachingResult.immediate_action}
                    </span>
                  </div>
                )}

                {/* Meta & Evidence Badges */}
                <div className="mt-5 pt-3 border-t border-emerald-100/60 flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-500 font-normal">Source:</span>
                    <span className="font-mono font-semibold bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-md border border-emerald-200/70">
                      {coachingResult.source || 'agent_coach'}
                    </span>
                    {coachingResult.confidence && (
                      <span className="font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200 font-semibold">
                        {Math.round(coachingResult.confidence * 100)}% Confidence
                      </span>
                    )}
                  </div>

                  {coachingResult.tools_used && Array.isArray(coachingResult.tools_used) && (
                    <div className="flex items-center space-x-1 text-slate-500 font-normal">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
                      <span>Grounded via: {coachingResult.tools_used.join(', ')}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Raw Structured Output (collapsed by default) */}
              <div className="glass-panel rounded-3xl p-5 shadow-forest border border-emerald-100/70">
                <button
                  type="button"
                  onClick={() => setShowRawOutput(!showRawOutput)}
                  className="w-full flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-700 cursor-pointer"
                >
                  <span>Raw Structured Output</span>
                  <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${showRawOutput ? 'rotate-180' : ''}`} />
                </button>
                {showRawOutput && (
                  <pre className="bg-white/95 text-slate-800 p-3.5 rounded-xl text-xs font-mono overflow-x-auto border border-emerald-100 max-h-72 shadow-inner mt-3">
                    {JSON.stringify(coachingResult, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        /* Coach Chat */
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Sessions Sidebar */}
          <div className="lg:col-span-1 glass-panel rounded-3xl border border-emerald-100/70 shadow-forest p-4 flex flex-col max-h-[420px] lg:max-h-[640px]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2.5 px-1 flex-shrink-0">
              Recent Conversations
            </h3>
            <div className="flex-1 overflow-y-auto space-y-1 pr-0.5">
              {sessionsLoading ? (
                <p className="text-xs text-slate-400 text-center py-6">Loading...</p>
              ) : sessions.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6 italic px-2">
                  No conversations yet. Send a message to start one.
                </p>
              ) : (
                sessions.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => handleSelectSession(s.id)}
                    className={`group/sess flex items-center justify-between gap-1 px-3 py-2 rounded-xl text-xs cursor-pointer transition-all border ${
                      activeSessionId === s.id
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-950 font-semibold'
                        : 'border-transparent hover:bg-white text-slate-700'
                    }`}
                  >
                    <span className="truncate flex-1">{s.title || 'Untitled conversation'}</span>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteSession(s.id, e)}
                      title="Delete conversation"
                      className="opacity-0 group-hover/sess:opacity-100 text-slate-400 hover:text-rose-600 flex-shrink-0 p-0.5 cursor-pointer transition-opacity"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Chat Thread */}
          <div className="lg:col-span-3 glass-panel rounded-3xl border border-emerald-100/70 shadow-forest flex flex-col h-[520px] lg:h-[640px]">
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-2">
                  <MessageCircle className="w-8 h-8 text-emerald-300" />
                  <p className="text-xs font-medium text-slate-500 max-w-xs">
                    Ask about your goals, get unstuck on a decision, or talk through today. Your journals, goals, and memories ground the reply.
                  </p>
                </div>
              ) : (
                messages.map((m) => <ChatBubble key={m.id} message={m} />)
              )}

              {chatSending && (
                <div className="flex items-center space-x-2 text-xs text-slate-400 pl-1">
                  <span className="w-6 h-6 rounded-full bg-emerald-700 flex items-center justify-center text-white flex-shrink-0">
                    <Brain className="w-3 h-3 animate-pulse" />
                  </span>
                  <span className="italic">Coach is thinking...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {chatError && (
              <div className="mx-5 mb-2 bg-rose-50 border border-rose-200 text-rose-900 px-3 py-2 rounded-xl text-xs flex items-center space-x-2 flex-shrink-0">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{chatError}</span>
              </div>
            )}

            <div className="border-t border-emerald-100/60 p-3.5 flex items-end space-x-2 flex-shrink-0">
              <textarea
                rows={1}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleChatKeyDown}
                placeholder="Message your coach..."
                className="flex-1 text-sm px-3.5 py-2.5 rounded-2xl border border-emerald-100 focus:ring-2 focus:ring-emerald-600 bg-white/95 shadow-xs text-slate-900 placeholder-slate-400 resize-none max-h-32"
              />
              <button
                type="button"
                onClick={handleSendChat}
                disabled={chatSending || !chatInput.trim()}
                className="bg-emerald-700 hover:bg-emerald-800 disabled:opacity-40 text-white p-3 rounded-full shadow-forest-xs transition-all cursor-pointer flex-shrink-0"
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
