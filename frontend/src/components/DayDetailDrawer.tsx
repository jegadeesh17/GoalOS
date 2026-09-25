import React, { useEffect, useRef, useState } from 'react';
import { DailyLog, YearDayBlock, TaskItem, goalOSApi } from '../api/client';
import { daysInYear, formatDate } from '../lib/date';
import {
  X,
  Calendar,
  CheckCircle2,
  Circle,
  Clock,
  Sun,
  Moon,
  Trophy,
  Lightbulb,
  ArrowRight,
  Flame,
} from 'lucide-react';

interface DayDetailDrawerProps {
  dateStr: string | null;
  daySummary: YearDayBlock | null;
  onClose: () => void;
  onOpenInJournal: (dateStr: string) => void;
}

const FOCUSABLE = 'button, [href], input, textarea, select, [tabindex]:not([tabindex="-1"])';

const parseTasks = (raw: string | null | undefined): TaskItem[] => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return raw
      .split('\n')
      .filter(Boolean)
      .map((text, idx) => ({
        id: `${idx}`,
        text: text.replace(/^\d+[\.\)]\s*/, '').replace(/\(tick\)|\(x\)/gi, '').trim(),
        priority: 1,
        completed: text.toLowerCase().includes('tick') || text.includes('✓'),
      }));
  }
};

const SectionTitle: React.FC<{ icon: React.ReactNode; children: React.ReactNode; badge?: string }> = ({ icon, children, badge }) => (
  <div className="flex items-center justify-between mb-3">
    <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-800">
      {icon}
      {children}
    </h3>
    {badge && <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full">{badge}</span>}
  </div>
);

export const DayDetailDrawer: React.FC<DayDetailDrawerProps> = ({
  dateStr,
  daySummary,
  onClose,
  onOpenInJournal,
}) => {
  const [log, setLog] = useState<DailyLog | null>(null);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!dateStr) return;

    let isMounted = true;
    setLog(null);
    const fetchDayData = async () => {
      try {
        setLoading(true);
        const data = await goalOSApi.getJournalByDate(dateStr);
        if (isMounted) setLog(data);
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

  // Dialog behaviour: focus the close button, trap Tab inside, Escape closes,
  // lock page scroll, and hand focus back to the day that opened it.
  useEffect(() => {
    if (!dateStr) return;
    const opener = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCloseRef.current();
        return;
      }
      if (e.key !== 'Tab' || !panelRef.current) return;
      const focusables = panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE);
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = previousOverflow;
      if (opener?.isConnected) opener.focus();
    };
  }, [dateStr]);

  if (!dateStr) return null;

  const year = Number(dateStr.slice(0, 4));
  const tasks = parseTasks(log?.planned_tasks);
  const doneCount = tasks.filter((t) => t.completed).length;

  const isToday = daySummary?.status === 'today';
  const isFuture = daySummary?.status === 'future';
  const isProductive = daySummary?.is_productive;
  const hasContent = Boolean(daySummary?.has_log || log?.top_priority || log?.journal_entry);

  const hasMorning = Boolean(
    log?.top_priority || log?.supporting_task_1 || log?.supporting_task_2 || log?.intention || log?.gratitude,
  );
  const hasEvening = Boolean(log?.one_win || log?.one_lesson || log?.takeaway || log?.journal_entry);

  const tasksValue =
    daySummary?.tasks_total_count && daySummary.tasks_total_count > 0
      ? `${daySummary.tasks_completed_count}/${daySummary.tasks_total_count}`
      : tasks.length > 0
      ? `${doneCount}/${tasks.length}`
      : '–';

  const metrics = [
    { label: 'Deep work', value: log?.deep_work_hours ? `${log.deep_work_hours}h` : '–' },
    { label: 'Tasks', value: tasksValue },
    { label: 'Sleep', value: log?.sleep_hours ? `${log.sleep_hours}h` : '–' },
    { label: 'Energy', value: log?.energy_level ? `${log.energy_level}/5` : '–' },
  ];

  const status = isProductive
    ? { label: 'Productive day', icon: <Flame className="w-3.5 h-3.5 text-emerald-700 fill-emerald-600" />, tone: 'bg-emerald-50 text-emerald-900' }
    : isToday
    ? { label: 'Today, in progress', icon: <Sun className="w-3.5 h-3.5 text-amber-600" />, tone: 'bg-amber-50 text-amber-900' }
    : isFuture
    ? { label: 'Still ahead', icon: <Clock className="w-3.5 h-3.5 text-slate-500" />, tone: 'bg-slate-100 text-slate-700' }
    : daySummary?.has_log
    ? { label: 'Logged', icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />, tone: 'bg-emerald-50 text-emerald-900' }
    : { label: 'Not logged', icon: <Circle className="w-3.5 h-3.5 text-slate-400" />, tone: 'bg-slate-100 text-slate-700' };

  const openInJournal = () => {
    onOpenInJournal(dateStr);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end !mt-0">
      <div className="absolute inset-0 bg-forest-950/25 animate-veil-in" onClick={onClose} aria-hidden="true" />

      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="day-drawer-title"
        className="relative w-full max-w-lg h-full bg-white shadow-forest-lg border-l border-emerald-100 flex flex-col animate-drawer-in"
      >
        <header className="px-6 pt-6 pb-5 border-b border-emerald-100/70">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium text-slate-500">
                {year} · Day {daySummary?.day_of_year ?? '–'} of {daysInYear(year)}
              </p>
              <h2 id="day-drawer-title" className="font-serif font-medium text-[1.75rem] leading-tight tracking-[-0.015em] text-forest-950 mt-1">
                {formatDate(dateStr, { weekday: 'long', month: 'long', day: 'numeric' })}
              </h2>
            </div>
            <button
              ref={closeRef}
              type="button"
              onClick={onClose}
              className="p-2 -mr-2 rounded-full text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2 mt-3 text-xs font-semibold">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${status.tone}`}>
              {status.icon}
              {status.label}
            </span>
            {daySummary?.productivity_score !== null && daySummary?.productivity_score !== undefined && (
              <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 tabular-nums">
                Score {Math.round(daySummary.productivity_score)}
              </span>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto overscroll-contain px-6 py-6">
          {loading ? (
            <div className="space-y-4 motion-safe:animate-pulse" aria-hidden="true">
              <div className="h-16 bg-slate-100 rounded-2xl" />
              <div className="h-28 bg-slate-100 rounded-2xl" />
              <div className="h-24 bg-slate-100 rounded-2xl" />
            </div>
          ) : !hasContent ? (
            <div className="text-center py-14 px-4">
              <Calendar className="w-9 h-9 text-emerald-600/40 mx-auto mb-3" />
              <p className="voice text-lg">
                {isFuture ? 'This day is still ahead.' : 'Nothing written for this day yet.'}
              </p>
              <button
                type="button"
                onClick={openInJournal}
                className="mt-5 inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-full shadow-forest-xs transition-colors cursor-pointer"
              >
                {isFuture ? 'Plan this day' : 'Write this day'}
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="space-y-8">
              <dl className="grid grid-cols-4 rounded-2xl border border-emerald-100 divide-x divide-emerald-100">
                {metrics.map((m) => (
                  <div key={m.label} className="px-3 py-2.5">
                    <dt className="text-[11px] font-medium text-slate-500">{m.label}</dt>
                    <dd className="text-base font-semibold text-slate-900 tabular-nums mt-0.5">{m.value}</dd>
                  </div>
                ))}
              </dl>

              {hasMorning && (
                <section>
                  <SectionTitle icon={<Sun className="w-4 h-4 text-amber-500" />} badge={log?.morning_completed ? 'Routine done' : undefined}>
                    Morning
                  </SectionTitle>
                  <div className="space-y-3">
                    {log?.top_priority && (
                      <div>
                        <p className="text-xs text-slate-500">First priority</p>
                        <p className="text-sm font-semibold text-slate-900 mt-0.5">{log.top_priority}</p>
                      </div>
                    )}
                    {(log?.supporting_task_1 || log?.supporting_task_2) && (
                      <ul className="space-y-1 text-sm text-slate-700">
                        {[log.supporting_task_1, log.supporting_task_2].filter(Boolean).map((t) => (
                          <li key={t} className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
                            {t}
                          </li>
                        ))}
                      </ul>
                    )}
                    {log?.intention && <p className="voice italic text-[15px]">“{log.intention}”</p>}
                    {log?.gratitude && (
                      <div>
                        <p className="text-xs text-slate-500">Grateful for</p>
                        <p className="voice text-[15px] mt-0.5">{log.gratitude}</p>
                      </div>
                    )}
                  </div>
                </section>
              )}

              {tasks.length > 0 && (
                <section>
                  <SectionTitle icon={<CheckCircle2 className="w-4 h-4 text-emerald-700" />}>
                    Tasks <span className="font-normal text-slate-500 tabular-nums">· {doneCount} of {tasks.length} done</span>
                  </SectionTitle>
                  <ul className="space-y-2">
                    {tasks.map((task, idx) => (
                      <li key={task.id || idx} className="flex items-start gap-2.5 text-sm">
                        {task.completed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" aria-label="Done" />
                        ) : (
                          <Circle className="w-4 h-4 text-slate-300 mt-0.5 shrink-0" aria-label="Not done" />
                        )}
                        <span className={`leading-snug ${task.completed ? 'text-slate-500 line-through' : 'text-slate-800'}`}>
                          {task.text}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {hasEvening && (
                <section>
                  <SectionTitle icon={<Moon className="w-4 h-4 text-teal-700" />} badge={log?.evening_completed ? 'Reflection done' : undefined}>
                    Evening
                  </SectionTitle>
                  <div className="space-y-4">
                    {log?.one_win && (
                      <div>
                        <p className="flex items-center gap-1.5 text-xs text-slate-500">
                          <Trophy className="w-3.5 h-3.5 text-amber-500" /> Win
                        </p>
                        <p className="voice text-base mt-0.5">{log.one_win}</p>
                      </div>
                    )}
                    {log?.one_lesson && (
                      <div>
                        <p className="flex items-center gap-1.5 text-xs text-slate-500">
                          <Lightbulb className="w-3.5 h-3.5 text-teal-600" /> Lesson
                        </p>
                        <p className="voice text-base mt-0.5">{log.one_lesson}</p>
                      </div>
                    )}
                    {log?.takeaway && (
                      <div>
                        <p className="text-xs text-slate-500">Rule for tomorrow</p>
                        <p className="voice italic text-base mt-0.5">{log.takeaway}</p>
                      </div>
                    )}
                    {log?.journal_entry && (
                      <div>
                        <p className="text-xs text-slate-500">Notes</p>
                        <p className="voice text-[15px] mt-1 whitespace-pre-wrap">{log.journal_entry}</p>
                      </div>
                    )}
                  </div>
                </section>
              )}
            </div>
          )}
        </div>

        <footer className="px-6 py-4 border-t border-emerald-100/70 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-full transition-colors cursor-pointer"
          >
            Close
          </button>
          <button
            type="button"
            onClick={openInJournal}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-full shadow-forest-xs transition-colors cursor-pointer"
          >
            Open in Journal
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </footer>
      </div>
    </div>
  );
};
