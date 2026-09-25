import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DailyLog, TaskItem, TimeBlockItem, goalOSApi, Goal, YearDayBlock } from '../api/client';
import { cacheLog, flushPendingWrites, queueWrite, readCachedLog } from '../offline/journalStash';
import { formatDate, localDateStr, parseLocalDate, shiftDate, weekStartOf } from '../lib/date';
import { DayDot, tierRank } from './DayDot';
import {
  CheckCircle2,
  Circle,
  Plus,
  Trash2,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Clock,
  Dumbbell,
  ListChecks,
  FileDown,
  CalendarDays,
  Sun,
  Moon
} from 'lucide-react';

interface JournalViewProps {
  onTriggerCoach?: (mode: 'morning' | 'evening') => void;
  initialDate?: string;
}

type SaveState = 'idle' | 'dirty' | 'saving' | 'saved' | 'offline';

const AUTOSAVE_DELAY_MS = 1200;
const WEEKDAY_LABELS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
const timeFormat = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' });

const fieldBase =
  'w-full rounded-xl border border-emerald-100 bg-white text-slate-900 placeholder:text-slate-500 transition-colors';

const parseTasks = (raw: string | null | undefined): TaskItem[] => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return raw.split('\n').filter(Boolean).map((text, idx) => ({
      id: `${Date.now()}-${idx}`,
      text: text.replace(/^\d+[\.\)]\s*/, '').replace(/\(tick\)|\(x\)/gi, '').trim(),
      priority: 1,
      completed: text.toLowerCase().includes('tick') || text.includes('✓'),
    }));
  }
};

const parseTimeBlocks = (raw: string | null | undefined): TimeBlockItem[] => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return raw.split('\n').filter(Boolean).map((line, idx) => {
      const parts = line.trim().split(/\s+/);
      const activity = parts.slice(1).join(' ');
      return {
        id: `${Date.now()}-${idx}`,
        time: parts[0] || '',
        activity,
        hours: 1,
        is_work: !activity.toLowerCase().includes('chill') && !activity.toLowerCase().includes('freshup'),
      };
    });
  }
};

const snapshotOf = (log: DailyLog, tasks: TaskItem[], blocks: TimeBlockItem[]) => JSON.stringify([log, tasks, blocks]);

const buildPayload = (date: string, log: DailyLog, tasks: TaskItem[], blocks: TimeBlockItem[]) => {
  const workHours = blocks.filter((b) => b.is_work).reduce((sum, b) => sum + (Number(b.hours) || 0), 0);
  return {
    ...log,
    date,
    planned_tasks: JSON.stringify(tasks),
    time_blocks: JSON.stringify(blocks),
    deep_work_hours: workHours > 0 ? workHours : log.deep_work_hours || 0,
    task_completion_rate: tasks.length > 0 ? tasks.filter((t) => t.completed).length / tasks.length : 0,
  };
};

const weekDates = (start: string) => Array.from({ length: 7 }, (_, i) => shiftDate(start, i));

/** Stand-in for a day the year grid didn't return (e.g. offline). */
const blankDay = (date: string): YearDayBlock => {
  const today = localDateStr();
  const d = parseLocalDate(date);
  return {
    date,
    day_of_year: 0,
    day_of_week: (d.getDay() + 6) % 7,
    month: d.getMonth() + 1,
    day: d.getDate(),
    status: date === today ? 'today' : date < today ? 'past' : 'future',
    has_log: false,
    is_productive: false,
  };
};

export const JournalView: React.FC<JournalViewProps> = ({ onTriggerCoach, initialDate }) => {
  const [currentDate, setCurrentDate] = useState<string>(initialDate || localDateStr());
  const [log, setLog] = useState<DailyLog | null>(null);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [timeBlocks, setTimeBlocks] = useState<TimeBlockItem[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [saveState, setSaveState] = useState<SaveState>('idle');
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const [weekDays, setWeekDays] = useState<Map<string, YearDayBlock>>(new Map());
  const [inkDate, setInkDate] = useState<string | null>(null);

  // New item inputs
  const [newTaskText, setNewTaskText] = useState('');
  const [newTaskGoalId, setNewTaskGoalId] = useState<number | undefined>(undefined);
  const [newBlockTime, setNewBlockTime] = useState('');
  const [newBlockActivity, setNewBlockActivity] = useState('');
  const [newBlockHours, setNewBlockHours] = useState<string>('');
  const [newBlockIsWork, setNewBlockIsWork] = useState<boolean>(true);

  // Autosave bookkeeping lives in refs so a save never races a re-render.
  const lastSavedRef = useRef('');
  const latestRef = useRef<{ date: string; log: DailyLog; tasks: TaskItem[]; timeBlocks: TimeBlockItem[]; snapshot: string } | null>(null);
  const currentDateRef = useRef(currentDate);
  currentDateRef.current = currentDate;
  const weekDaysRef = useRef(weekDays);
  weekDaysRef.current = weekDays;
  const dateInputRef = useRef<HTMLInputElement>(null);

  const weekStart = weekStartOf(currentDate);

  const refreshWeek = useCallback(async (start: string): Promise<Map<string, YearDayBlock>> => {
    const dates = weekDates(start);
    const years = [...new Set(dates.map((d) => Number(d.slice(0, 4))))];
    const results = await Promise.all(years.map((y) => goalOSApi.getYearProductivity(y).catch(() => null)));
    const map = new Map<string, YearDayBlock>();
    results.forEach((r) => r?.days.forEach((d) => dates.includes(d.date) && map.set(d.date, d)));
    if (weekStartOf(currentDateRef.current) === start) setWeekDays(map);
    return map;
  }, []);

  useEffect(() => {
    refreshWeek(weekStart);
  }, [weekStart, refreshWeek]);

  const persist = useCallback(
    async (force = false): Promise<void> => {
      const latest = latestRef.current;
      if (!latest || (!force && latest.snapshot === lastSavedRef.current)) return;
      const payload = buildPayload(latest.date, latest.log, latest.tasks, latest.timeBlocks);
      lastSavedRef.current = latest.snapshot; // claimed now, so overlapping triggers don't double-send
      setSaveState('saving');
      try {
        const updated = await goalOSApi.upsertJournal(payload);
        cacheLog(updated);
        setSavedAt(new Date());
        setNotice(null);
        setSaveState(latestRef.current?.snapshot === latest.snapshot ? 'saved' : 'dirty');

        // If this save changed how the day reads on the calendar, ink its dot.
        const weekLoaded = weekDaysRef.current.size > 0;
        const before = weekDaysRef.current.get(latest.date);
        const after = (await refreshWeek(weekStartOf(latest.date))).get(latest.date);
        if (weekLoaded && tierRank(after) > tierRank(before)) {
          setInkDate(latest.date);
          window.setTimeout(() => setInkDate(null), 1000);
        }
      } catch (err) {
        // Never drop the edit: stash it locally and replay it on reconnect.
        console.error('Failed to save journal:', err);
        await queueWrite(payload);
        setSaveState('offline');
        setNotice('You’re offline. This entry is kept in your browser and syncs when you reconnect.');
      }
    },
    [refreshWeek],
  );

  const goToDate = useCallback(
    (dateStr: string) => {
      if (!dateStr || dateStr === currentDateRef.current) return;
      void persist();
      setLoading(true);
      setCurrentDate(dateStr);
    },
    [persist],
  );

  useEffect(() => {
    if (initialDate) goToDate(initialDate);
  }, [initialDate, goToDate]);

  useEffect(() => {
    let cancelled = false;
    const loadData = async () => {
      setLoading(true);
      try {
        const [logData, goalsData] = await Promise.all([
          goalOSApi.getJournalByDate(currentDate),
          goalOSApi.getGoals({ status: 'active' }),
        ]);
        if (cancelled) return;
        const parsedTasks = parseTasks(logData.planned_tasks);
        const parsedBlocks = parseTimeBlocks(logData.time_blocks);
        lastSavedRef.current = snapshotOf(logData, parsedTasks, parsedBlocks);
        setLog(logData);
        setTasks(parsedTasks);
        setTimeBlocks(parsedBlocks);
        setGoals(goalsData);
        setSaveState('idle');
        setNotice(null);
        cacheLog(logData);
      } catch (err) {
        console.error('Failed to load journal log:', err);
        // Fall back to the local stash so the day is still readable offline.
        const cached = await readCachedLog(currentDate);
        if (cancelled) return;
        if (cached) {
          const parsedTasks = parseTasks(cached.planned_tasks);
          const parsedBlocks = parseTimeBlocks(cached.time_blocks);
          lastSavedRef.current = snapshotOf(cached, parsedTasks, parsedBlocks);
          setLog(cached);
          setTasks(parsedTasks);
          setTimeBlocks(parsedBlocks);
          setNotice('You’re offline. Showing the copy of this day saved in your browser.');
        } else {
          setLog(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadData();
    return () => {
      cancelled = true;
    };
  }, [currentDate]);

  // Autosave: a quiet beat after the last edit.
  useEffect(() => {
    if (loading || !log) return;
    const snapshot = snapshotOf(log, tasks, timeBlocks);
    latestRef.current = { date: currentDate, log, tasks, timeBlocks, snapshot };
    if (snapshot === lastSavedRef.current) return;
    setSaveState('dirty');
    const timer = window.setTimeout(() => void persist(), AUTOSAVE_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [log, tasks, timeBlocks, loading, currentDate, persist]);

  // Leaving the Journal (tab switch) flushes anything still pending.
  useEffect(() => () => void persist(), [persist]);

  // Ctrl/Cmd+S saves immediately.
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        void persist();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [persist]);

  // Replay anything queued while offline, on mount and whenever the browser reconnects.
  useEffect(() => {
    const sync = async () => {
      const synced = await flushPendingWrites(goalOSApi.upsertJournal);
      if (synced > 0) {
        setSaveState((s) => (s === 'offline' ? 'saved' : s));
        setSavedAt(new Date());
        setNotice(`Back online. Synced ${synced} journal ${synced === 1 ? 'entry' : 'entries'} saved in your browser.`);
        window.setTimeout(() => setNotice(null), 4000);
      }
    };
    sync();
    window.addEventListener('online', sync);
    return () => window.removeEventListener('online', sync);
  }, []);

  const openDatePicker = () => {
    const input = dateInputRef.current as (HTMLInputElement & { showPicker?: () => void }) | null;
    if (!input) return;
    try {
      if (input.showPicker) input.showPicker();
      else input.focus();
    } catch {
      input.focus();
    }
  };

  // Task Handlers
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
    setTasks(tasks.map((t, i) => (i === index ? { ...t, completed: !t.completed } : t)));
  };

  const removeTask = (index: number) => {
    setTasks(tasks.filter((_, i) => i !== index));
  };

  // Time Block Handlers
  const handleAddTimeBlock = () => {
    if (!newBlockActivity.trim()) return;
    const newBlock: TimeBlockItem = {
      id: Date.now().toString(),
      time: newBlockTime.trim(),
      activity: newBlockActivity.trim(),
      hours: parseFloat(newBlockHours) || 1.0,
      is_work: newBlockIsWork,
    };
    setTimeBlocks([...timeBlocks, newBlock]);
    setNewBlockTime('');
    setNewBlockActivity('');
    setNewBlockHours('');
  };

  const removeTimeBlock = (index: number) => {
    setTimeBlocks(timeBlocks.filter((_, i) => i !== index));
  };

  const toggleBlockType = (index: number) => {
    setTimeBlocks(timeBlocks.map((b, i) => (i === index ? { ...b, is_work: !b.is_work } : b)));
  };

  const totalWorkHours = timeBlocks.filter((b) => b.is_work).reduce((sum, b) => sum + (Number(b.hours) || 0), 0);
  const totalChillHours = timeBlocks.filter((b) => !b.is_work).reduce((sum, b) => sum + (Number(b.hours) || 0), 0);
  const doneCount = tasks.filter((t) => t.completed).length;

  const isToday = currentDate === localDateStr();

  const handleExportDigest = async () => {
    try {
      setExportStatus('Preparing digest…');
      const markdown = await goalOSApi.getWeeklyReportMarkdown(weekStart);
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `goalos_weekly_digest_${weekStart}.md`;
      a.click();
      URL.revokeObjectURL(url);
      setExportStatus(null);
    } catch (err) {
      console.error('Weekly digest export failed:', err);
      setExportStatus('Digest failed, try again');
      window.setTimeout(() => setExportStatus(null), 3000);
    }
  };

  const openCoach = async (mode: 'morning' | 'evening') => {
    await persist();
    onTriggerCoach?.(mode);
  };

  const saveLabel =
    saveState === 'saving'
      ? 'Saving…'
      : saveState === 'dirty'
      ? 'Unsaved changes'
      : saveState === 'saved'
      ? `Saved ${savedAt ? timeFormat.format(savedAt) : ''}`.trim()
      : saveState === 'offline'
      ? 'Saved in this browser'
      : 'Saves as you write';

  return (
    <div className="space-y-6">
      {/* Header: the day as a title, this week as dots */}
      <header className="px-1 sm:px-2 flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5">
        <div className="flex items-start gap-1">
          <button
            type="button"
            onClick={() => goToDate(shiftDate(currentDate, -1))}
            className="mt-1.5 p-1.5 rounded-full text-emerald-800/70 hover:text-emerald-950 hover:bg-emerald-50 transition-colors cursor-pointer"
            aria-label="Previous day"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
              <h1 className="font-serif font-medium text-[1.75rem] sm:text-[2.1rem] leading-tight tracking-[-0.015em] text-forest-950">
                {formatDate(currentDate, { weekday: 'long', month: 'long', day: 'numeric' })}
              </h1>
              {isToday && (
                <span className="text-[11px] font-semibold text-amber-900 bg-amber-100 px-2 py-0.5 rounded-full">Today</span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1 text-xs text-slate-500">
              <span className="relative">
                <button
                  type="button"
                  onClick={openDatePicker}
                  className="inline-flex items-center gap-1 font-medium text-emerald-800 hover:text-emerald-950 cursor-pointer"
                >
                  <CalendarDays className="w-3.5 h-3.5" />
                  {currentDate.slice(0, 4)} · Pick a date
                </button>
                <input
                  ref={dateInputRef}
                  type="date"
                  value={currentDate}
                  onChange={(e) => goToDate(e.target.value)}
                  tabIndex={-1}
                  aria-hidden="true"
                  className="sr-only"
                />
              </span>
              <span aria-hidden="true">·</span>
              <span aria-live="polite">{saveLabel}</span>
              {(saveState === 'dirty' || saveState === 'offline') && (
                <button
                  type="button"
                  onClick={() => void persist(saveState === 'offline')}
                  className="font-semibold text-emerald-800 hover:text-emerald-950 cursor-pointer"
                >
                  {saveState === 'offline' ? 'Retry' : 'Save now'}
                </button>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={() => goToDate(shiftDate(currentDate, 1))}
            className="mt-1.5 p-1.5 rounded-full text-emerald-800/70 hover:text-emerald-950 hover:bg-emerald-50 transition-colors cursor-pointer"
            aria-label="Next day"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-col items-start lg:items-end gap-3 pl-9 lg:pl-0">
          <div className="flex items-end gap-2.5" role="group" aria-label="This week">
            {weekDates(weekStart).map((date, i) => {
              const selected = date === currentDate;
              return (
                <div key={date} className="flex flex-col items-center gap-1.5">
                  <span className={`text-[10px] font-semibold ${selected ? 'text-emerald-800' : 'text-slate-500'}`} aria-hidden="true">
                    {WEEKDAY_LABELS[i]}
                  </span>
                  <DayDot
                    day={weekDays.get(date) ?? blankDay(date)}
                    size="md"
                    selected={selected}
                    inking={inkDate === date}
                    aria-current={selected ? 'date' : undefined}
                    onClick={() => goToDate(date)}
                  />
                </div>
              );
            })}
          </div>

          <div className="flex items-center gap-4 text-xs font-semibold">
            <button
              type="button"
              onClick={handleExportDigest}
              title="Download a 7-day retrospective for this week"
              className="inline-flex items-center gap-1.5 text-emerald-800 hover:text-emerald-950 cursor-pointer"
            >
              <FileDown className="w-3.5 h-3.5" />
              {exportStatus || 'Weekly digest'}
            </button>
            {onTriggerCoach && (
              <button
                type="button"
                onClick={() => openCoach('morning')}
                className="inline-flex items-center gap-1.5 text-emerald-800 hover:text-emerald-950 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                Morning coach
              </button>
            )}
          </div>
        </div>
      </header>

      {notice && (
        <div role="status" className="animate-fade-up bg-amber-50/90 border border-amber-200 text-amber-950 text-xs font-medium px-4 py-2.5 rounded-2xl">
          {notice}
        </div>
      )}

      {loading ? (
        <div className="glass-panel rounded-3xl p-8 space-y-4 motion-safe:animate-pulse" aria-hidden="true">
          <div className="h-10 bg-slate-100/80 rounded-xl w-2/3" />
          <div className="h-48 bg-slate-50/80 rounded-2xl" />
          <div className="h-28 bg-slate-50/80 rounded-2xl" />
        </div>
      ) : !log ? (
        <div className="glass-panel rounded-3xl p-10 text-center">
          <p className="voice text-lg">This day couldn’t be loaded.</p>
          <p className="text-sm text-slate-600 mt-1">Check that GoalOS is running, then pick the day again.</p>
        </div>
      ) : (
        <div className="glass-panel rounded-3xl p-6 sm:p-8 space-y-8 shadow-forest">
          {/* Morning */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="md:col-span-2">
              <label htmlFor="journal-gratitude" className="flex items-center gap-1.5 text-xs font-semibold text-forest-800 mb-1.5">
                <Sun className="w-3.5 h-3.5 text-amber-500" />
                Morning gratitude
              </label>
              <input
                id="journal-gratitude"
                type="text"
                placeholder="What are you grateful for today?"
                value={log.gratitude || ''}
                onChange={(e) => setLog({ ...log, gratitude: e.target.value })}
                className={`${fieldBase} voice text-[17px] px-4 py-2.5 placeholder:italic`}
              />
            </div>

            <div>
              <label htmlFor="journal-awake" className="flex items-center justify-between text-xs font-semibold text-forest-800 mb-1.5">
                <span>Awake &amp; sleep</span>
                {log.sleep_hours ? <span className="font-medium text-emerald-800">{log.sleep_hours}h sleep</span> : null}
              </label>
              <div className="flex items-center gap-2">
                <input
                  id="journal-awake"
                  type="text"
                  placeholder="e.g. 9:00 AM – 2:00 AM"
                  value={log.awake_range || ''}
                  onChange={(e) => setLog({ ...log, awake_range: e.target.value })}
                  className={`${fieldBase} !w-auto flex-1 min-w-0 text-sm px-3.5 py-2.5`}
                />
                <input
                  type="number"
                  min="0"
                  max="24"
                  step="0.5"
                  aria-label="Hours of sleep"
                  placeholder="7h"
                  value={log.sleep_hours || ''}
                  onChange={(e) => setLog({ ...log, sleep_hours: parseFloat(e.target.value) || 0 })}
                  className={`${fieldBase} !w-16 flex-shrink-0 text-sm px-2.5 py-2.5 text-center font-semibold tabular-nums`}
                />
              </div>
            </div>
          </div>

          {/* Plan: time blocks and tasks side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pt-6 border-t border-emerald-100/70">
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Clock className="w-4 h-4 text-emerald-700" />
                  Time blocks
                </h2>
                <div className="flex items-center gap-2 text-xs font-semibold">
                  {totalWorkHours > 0 && (
                    <span className="bg-emerald-50 text-emerald-800 px-2.5 py-0.5 rounded-full">{totalWorkHours}h work</span>
                  )}
                  {totalChillHours > 0 && (
                    <span className="bg-amber-50 text-amber-900 px-2.5 py-0.5 rounded-full">{totalChillHours}h rest</span>
                  )}
                </div>
              </div>

              {timeBlocks.length === 0 ? (
                <p className="text-sm text-slate-500 py-1">
                  Nothing planned yet. Add a block like <span className="font-medium text-slate-700">10–12 · Applications</span>.
                </p>
              ) : (
                <ul className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
                  {timeBlocks.map((block, idx) => (
                    <li
                      key={block.id || idx}
                      className="flex items-center justify-between gap-2 px-3 py-2 rounded-xl border border-emerald-100/80 bg-white text-sm"
                    >
                      <div className="flex items-center gap-2.5 flex-1 min-w-0">
                        {block.time && (
                          <span className="text-xs font-semibold text-emerald-900 bg-emerald-50 px-2 py-0.5 rounded-lg whitespace-nowrap tabular-nums">
                            {block.time}
                          </span>
                        )}
                        <span className="font-medium text-slate-800 truncate">{block.activity}</span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {block.hours ? <span className="text-xs text-slate-500 tabular-nums">{block.hours}h</span> : null}
                        <button
                          type="button"
                          onClick={() => toggleBlockType(idx)}
                          className={`px-2 py-0.5 rounded-lg text-[11px] font-semibold transition-colors cursor-pointer ${
                            block.is_work ? 'bg-emerald-100 text-emerald-900' : 'bg-amber-100 text-amber-900'
                          }`}
                          aria-label={`${block.is_work ? 'Work' : 'Rest'} block. Switch to ${block.is_work ? 'rest' : 'work'}`}
                        >
                          {block.is_work ? 'Work' : 'Rest'}
                        </button>
                        <button
                          type="button"
                          onClick={() => removeTimeBlock(idx)}
                          className="text-slate-400 hover:text-rose-600 transition-colors p-1 cursor-pointer"
                          aria-label={`Delete ${block.activity}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              <div className="pt-1 flex flex-wrap sm:flex-nowrap items-center gap-2">
                <input
                  type="text"
                  aria-label="Time"
                  placeholder="9–10"
                  value={newBlockTime}
                  onChange={(e) => setNewBlockTime(e.target.value)}
                  className={`${fieldBase} !w-20 text-xs px-3 py-2 tabular-nums`}
                />
                <input
                  type="text"
                  aria-label="Activity"
                  placeholder="What will you do?"
                  value={newBlockActivity}
                  onChange={(e) => setNewBlockActivity(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddTimeBlock()}
                  className={`${fieldBase} !w-auto flex-1 min-w-[8rem] text-xs px-3 py-2`}
                />
                <input
                  type="number"
                  min="0.25"
                  max="12"
                  step="0.25"
                  aria-label="Hours"
                  placeholder="Hrs"
                  value={newBlockHours}
                  onChange={(e) => setNewBlockHours(e.target.value)}
                  className={`${fieldBase} !w-16 text-xs px-2 py-2 text-center tabular-nums`}
                />
                <button
                  type="button"
                  onClick={() => setNewBlockIsWork(!newBlockIsWork)}
                  className={`px-2.5 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                    newBlockIsWork ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-900'
                  }`}
                  aria-label={`New block type: ${newBlockIsWork ? 'work' : 'rest'}. Switch`}
                >
                  {newBlockIsWork ? 'Work' : 'Rest'}
                </button>
                <button
                  type="button"
                  onClick={handleAddTimeBlock}
                  disabled={!newBlockActivity.trim()}
                  className="bg-emerald-700 hover:bg-emerald-800 disabled:opacity-40 text-white px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer disabled:cursor-default"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add
                </button>
              </div>
            </section>

            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <ListChecks className="w-4 h-4 text-emerald-700" />
                  Tasks
                </h2>
                {tasks.length > 0 && (
                  <span className="text-xs font-semibold text-emerald-900 bg-emerald-50 px-2.5 py-0.5 rounded-full tabular-nums">
                    {doneCount} of {tasks.length} done
                  </span>
                )}
              </div>

              {tasks.length === 0 ? (
                <p className="text-sm text-slate-500 py-1">No tasks yet. Add the few that would make today count.</p>
              ) : (
                <ul className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
                  {tasks.map((task, idx) => {
                    const linkedGoal = goals.find((g) => g.id === task.goal_id);
                    return (
                      <li
                        key={task.id || idx}
                        className={`flex items-center justify-between gap-2 px-3 py-2 rounded-xl border transition-colors ${
                          task.completed ? 'bg-slate-50/80 border-slate-200' : 'bg-white border-emerald-100/80'
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => toggleTask(idx)}
                          className="flex items-center gap-2.5 flex-1 min-w-0 text-left cursor-pointer"
                          aria-pressed={task.completed}
                          aria-label={`${task.text}${task.completed ? ', done' : ''}`}
                        >
                          {task.completed ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                          ) : (
                            <Circle className="w-4 h-4 text-slate-300 flex-shrink-0" />
                          )}
                          <span className={`text-sm truncate ${task.completed ? 'line-through text-slate-500' : 'font-medium text-slate-800'}`}>
                            {task.text}
                          </span>
                          {linkedGoal && (
                            <span className="text-[11px] font-medium bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-md flex-shrink-0">
                              {linkedGoal.title}
                            </span>
                          )}
                        </button>

                        <button
                          type="button"
                          onClick={() => removeTask(idx)}
                          className="text-slate-400 hover:text-rose-600 transition-colors p-1 cursor-pointer"
                          aria-label={`Delete ${task.text}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}

              <div className="pt-1 flex flex-col sm:flex-row items-center gap-2">
                <input
                  type="text"
                  aria-label="New task"
                  placeholder="Add a task…"
                  value={newTaskText}
                  onChange={(e) => setNewTaskText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddTask()}
                  className={`${fieldBase} flex-1 text-xs px-3.5 py-2`}
                />
                <select
                  aria-label="Link to goal"
                  value={newTaskGoalId || ''}
                  onChange={(e) => setNewTaskGoalId(e.target.value ? Number(e.target.value) : undefined)}
                  className={`${fieldBase} sm:!w-auto text-xs px-3 py-2 font-medium text-slate-800`}
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
                  disabled={!newTaskText.trim()}
                  className="w-full sm:w-auto bg-emerald-700 hover:bg-emerald-800 disabled:opacity-40 text-white px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 transition-colors cursor-pointer disabled:cursor-default"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add task
                </button>
              </div>
            </section>
          </div>

          {/* Evening */}
          <div className="pt-6 border-t border-emerald-100/70 space-y-5">
            <div>
              <label htmlFor="journal-reflection" className="flex items-center gap-1.5 text-xs font-semibold text-forest-800 mb-1.5">
                <Moon className="w-3.5 h-3.5 text-teal-700" />
                Evening reflection
              </label>
              <textarea
                id="journal-reflection"
                rows={5}
                placeholder="How did today go? What pulled you off course, and what did you notice?"
                value={log.journal_entry || ''}
                onChange={(e) => setLog({ ...log, journal_entry: e.target.value })}
                className={`${fieldBase} voice text-[17px] px-4 py-3 resize-y placeholder:italic`}
              />
            </div>

            <div>
              <label htmlFor="journal-rule" className="block text-xs font-semibold text-forest-800 mb-1.5">
                One rule for tomorrow
              </label>
              <input
                id="journal-rule"
                type="text"
                placeholder="A rule or reminder to carry into tomorrow"
                value={log.takeaway || ''}
                onChange={(e) => setLog({ ...log, takeaway: e.target.value })}
                className={`${fieldBase} voice italic text-[17px] px-4 py-2.5`}
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
              <label className="flex items-center gap-2.5 cursor-pointer px-3 py-2 rounded-xl border border-emerald-100 bg-white hover:border-emerald-200 transition-colors">
                <input
                  type="checkbox"
                  checked={!!log.workout_completed}
                  onChange={(e) => setLog({ ...log, workout_completed: e.target.checked })}
                  className="w-4 h-4 rounded accent-emerald-700"
                />
                <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                  <Dumbbell className="w-3.5 h-3.5 text-emerald-700" />
                  Workout done
                </span>
              </label>

              {onTriggerCoach && (
                <button
                  type="button"
                  onClick={() => openCoach('evening')}
                  className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 flex items-center gap-1.5 cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  Run evening review
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
