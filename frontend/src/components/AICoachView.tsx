import React, { useState, useEffect, useRef } from 'react';
import { goalOSApi, CoachSession, CoachMessage } from '../api/client';
import { PageHeader } from './PageHeader';
import {
  Sparkles,
  Compass,
  Target,
  CheckCircle,
  AlertCircle,
  Brain,
  Lightbulb,
  ShieldCheck,
  ListChecks,
  MessageCircle,
  Plus,
  Trash2,
  Send,
  ChevronDown
} from 'lucide-react';

interface AICoachViewProps {
  initialMode?: 'future-self' | 'goal-alignment';
}

type SubView = 'pipelines' | 'chat';

// "Saved months: 2026-08 ..." -> ["Saved months", "2026-08 ..."]; no lead when the first colon sits too far in.
const splitLead = (point: string): [string | null, string] => {
  const i = point.indexOf(': ');
  return i > 0 && i <= 60 && !point.slice(0, i).includes('. ') ? [point.slice(0, i), point.slice(i + 2)] : [null, point];
};

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
        <div className="voice bg-white rounded-2xl rounded-bl-md px-4 py-3 text-[15px] border border-emerald-100/80 shadow-forest-xs whitespace-pre-wrap">
          {message.content}
        </div>
        {(message.agent_name || toolNames.length > 0) && (
          <div className="flex items-center flex-wrap gap-x-2.5 gap-y-1 px-1 text-[11px] text-slate-500 font-medium">
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

export const AICoachView: React.FC<AICoachViewProps> = ({ initialMode = 'goal-alignment' }) => {
  const [subView, setSubView] = useState<SubView>('pipelines');

  // --- Guided Pipelines state ---
  const [mode, setMode] = useState<'future-self' | 'goal-alignment'>(initialMode);
  const [loading, setLoading] = useState(false);
  const [coachingResult, setCoachingResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRawOutput, setShowRawOutput] = useState(false);

  const handleRunCoach = async () => {
    try {
      setLoading(true);
      setError(null);
      setCoachingResult(null);
      setShowRawOutput(false);

      let result: any = null;
      if (mode === 'future-self') {
        result = await goalOSApi.futureSelfCoach();
      } else if (mode === 'goal-alignment') {
        result = await goalOSApi.progressCoach();
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
    { id: 'goal-alignment', label: 'Goal Alignment', icon: Target, desc: 'Monthly & yearly pacing against your active goals' },
    { id: 'future-self', label: 'Future Self', icon: Compass, desc: '5-year & 10-year horizon pacing' },
  ] as const;
  const selectedMode = modeOptions.find((o) => o.id === mode) ?? modeOptions[0];

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
          {r.written_from_age != null && (
            <p className="text-xs text-slate-600 not-italic font-sans pt-1">— your future self, age {r.written_from_age}</p>
          )}
        </div>
      )}

      {r.pacing_status && (
        <div className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded-full border border-emerald-200">
          {r.pacing_status}
        </div>
      )}

      {Array.isArray(r.progress_points) && r.progress_points.length > 1 ? (
        <ul className="mt-2 divide-y divide-emerald-100/70">
          {r.progress_points.map((point: string, i: number) => {
            const [lead, rest] = splitLead(point);
            return (
              <li key={i} className="py-2 first:pt-0 last:pb-0 text-sm text-slate-700 leading-relaxed">
                {lead && <span className="font-semibold text-slate-900">{lead}: </span>}
                {rest}
              </li>
            );
          })}
        </ul>
      ) : (
        r.progress_narrative && <p className="mt-2 text-sm text-slate-700 leading-relaxed">{r.progress_narrative}</p>
      )}

      {r.monthly_goal_evaluated && (
        <p className="mt-1.5 text-xs text-slate-600">
          <strong className="text-slate-800 font-semibold">Evaluated against: </strong>
          {r.monthly_goal_evaluated}
        </p>
      )}

      {(r.five_year_pacing || r.ten_year_pacing) && (
        <div className="mt-3 space-y-1.5">
          {r.five_year_pacing && (
            <p className="text-xs text-slate-700 leading-relaxed">
              <strong className="text-slate-900 font-semibold">5-year pacing: </strong>
              {r.five_year_pacing}
            </p>
          )}
          {r.ten_year_pacing && (
            <p className="text-xs text-slate-700 leading-relaxed">
              <strong className="text-slate-900 font-semibold">10-year pacing: </strong>
              {r.ten_year_pacing}
            </p>
          )}
        </div>
      )}

      {(r.critical_bottleneck || r.recognized_pattern_analysis) && (
        <div className="bg-rose-50/70 border border-rose-200 rounded-xl p-3.5 mt-3 space-y-1.5">
          {r.critical_bottleneck && <p className="text-xs font-semibold text-rose-900">{r.critical_bottleneck}</p>}
          {r.recognized_pattern_analysis && <p className="text-xs text-rose-800 leading-relaxed">{r.recognized_pattern_analysis}</p>}
        </div>
      )}

      {r.actionable_pattern_breaking_protocol && (
        <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-3.5 mt-3">
          <div className="text-xs font-semibold text-emerald-800 mb-1">Pattern-breaking protocol</div>
          <p className="text-xs text-emerald-950 leading-relaxed">{r.actionable_pattern_breaking_protocol}</p>
        </div>
      )}

      {r.key_wins_aligned && (
        <p className="mt-2 text-xs text-slate-600">
          <strong className="text-slate-800 font-semibold">Wins: </strong>
          {r.key_wins_aligned}
        </p>
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
      <PageHeader
        title="AI Coach"
        subtitle="Guidance grounded in your journals, saved lessons and active goals."
        actions={
          <>
            <div className="flex items-center gap-1 bg-slate-100/80 p-1 rounded-full" role="group" aria-label="Coach mode">
              <button
                type="button"
                onClick={() => setSubView('pipelines')}
                aria-pressed={subView === 'pipelines'}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
                  subView === 'pipelines' ? 'bg-white text-emerald-900 shadow-forest-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <ListChecks className="w-3.5 h-3.5" />
                Sessions
              </button>
              <button
                type="button"
                onClick={() => setSubView('chat')}
                aria-pressed={subView === 'chat'}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
                  subView === 'chat' ? 'bg-white text-emerald-900 shadow-forest-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <MessageCircle className="w-3.5 h-3.5" />
                Chat
              </button>
            </div>
            {subView === 'chat' && (
              <button
                type="button"
                onClick={handleNewChat}
                className="flex items-center justify-center gap-1.5 bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2 rounded-full text-xs font-semibold shadow-forest-xs transition-colors cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                New chat
              </button>
            )}
          </>
        }
      />

      {subView === 'pipelines' ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup" aria-label="Coaching session">
            {modeOptions.map((opt) => {
              const Icon = opt.icon;
              const isSelected = mode === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  onClick={() => {
                    setMode(opt.id);
                    setCoachingResult(null);
                    setError(null);
                  }}
                  className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
                    isSelected ? 'bg-white border-emerald-300 ring-1 ring-emerald-300 shadow-forest-xs' : 'glass-card-interactive'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`p-1.5 rounded-lg ${isSelected ? 'bg-emerald-700 text-white' : 'bg-emerald-50 text-emerald-800'}`}>
                      <Icon className="w-3.5 h-3.5" />
                    </span>
                    <span className={`text-xs font-bold ${isSelected ? 'text-emerald-950' : 'text-slate-800'}`}>{opt.label}</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-snug line-clamp-2">{opt.desc}</p>
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap items-center justify-end gap-3 px-1">
            <button
              type="button"
              onClick={handleRunCoach}
              disabled={loading}
              className="flex items-center justify-center gap-1.5 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white px-5 py-2.5 rounded-full text-xs font-semibold shadow-forest-xs transition-colors cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {loading ? 'Thinking…' : `Run ${selectedMode.label.toLowerCase()}`}
            </button>
          </div>

          {error && (
            <div role="alert" className="bg-rose-50 border border-rose-200 text-rose-900 p-3.5 rounded-2xl flex items-start gap-2.5 text-xs">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">The coach couldn’t answer</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="glass-panel rounded-3xl p-10 text-center space-y-3 shadow-forest" role="status">
              <div className="w-12 h-12 rounded-2xl bg-emerald-700 flex items-center justify-center mx-auto text-white shadow-forest-xs motion-safe:animate-pulse">
                <Brain className="w-6 h-6" />
              </div>
              <p className="voice text-lg">Reading your recent days…</p>
              <p className="text-xs text-slate-600 max-w-md mx-auto">
                Drawing on your goals, journals and patterns. This usually takes a few seconds.
              </p>
            </div>
          )}

          {!loading && !coachingResult && !error && (
            <div className="glass-panel rounded-3xl px-6 py-12 text-center shadow-forest">
              <p className="voice text-xl">{selectedMode.desc}.</p>
              <p className="text-xs text-slate-600 mt-2">Run it when you’re ready; it reads your latest journal entries first.</p>
            </div>
          )}

          {/* Coaching Output View */}
          {coachingResult && (
            <div className="space-y-6">
              {/* Main Mentor Directive Card */}
              <div className="glass-panel rounded-3xl p-6 sm:p-7 relative overflow-hidden shadow-forest border border-emerald-200/90">
                <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-800 mb-2">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-500 fill-amber-400" />
                  <span>Your coach says</span>
                </div>

                {(() => {
                  const directive =
                    coachingResult.mentor_rule ||
                    coachingResult.rule ||
                    coachingResult.core_insight ||
                    coachingResult.coaching ||
                    coachingResult.recommendation ||
                    coachingResult.actionable_coaching_advice ||
                    (coachingResult.message || coachingResult.progress_narrative
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
                  className="w-full flex items-center justify-between text-xs font-semibold text-slate-700 cursor-pointer"
                >
                  <span>Raw output</span>
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
            <h2 className="text-sm font-semibold text-slate-600 mb-2.5 px-1 flex-shrink-0">
              Conversations
            </h2>
            <div className="flex-1 overflow-y-auto space-y-1 pr-0.5">
              {sessionsLoading ? (
                <p className="text-xs text-slate-500 text-center py-6">Loading…</p>
              ) : sessions.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6 px-2">
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
                      aria-label={`Delete conversation ${s.title || ''}`.trim()}
                      className="opacity-0 group-hover/sess:opacity-100 focus-visible:opacity-100 [@media(hover:none)]:opacity-100 text-slate-400 hover:text-rose-600 flex-shrink-0 p-0.5 cursor-pointer transition-opacity"
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
                  <p className="voice text-base max-w-xs">
                    Ask about your goals, get unstuck on a decision, or talk through today. Your journals, goals, and memories ground the reply.
                  </p>
                </div>
              ) : (
                messages.map((m) => <ChatBubble key={m.id} message={m} />)
              )}

              {chatSending && (
                <div className="flex items-center space-x-2 text-xs text-slate-500 pl-1" role="status">
                  <span className="w-6 h-6 rounded-full bg-emerald-700 flex items-center justify-center text-white flex-shrink-0">
                    <Brain className="w-3 h-3 animate-pulse" />
                  </span>
                  <span className="italic">Coach is thinking…</span>
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
                className="flex-1 text-sm px-3.5 py-2.5 rounded-2xl border border-emerald-100 focus:ring-2 focus:ring-emerald-600 bg-white/95 text-slate-900 placeholder:text-slate-500 resize-none max-h-32"
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
