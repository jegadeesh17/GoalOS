import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  YearProductivityData,
  YearDayBlock,
  LifeSummary,
  YearGridRow,
  goalOSApi
} from '../api/client';
import { DayDetailDrawer } from './DayDetailDrawer';
import { LifeProgressBanner } from './LifeProgressBanner';
import { DayDot, TIER_FILL, describeDay } from './DayDot';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface YearProductivityCalendarProps {
  summary: LifeSummary | null;
  yearSummary: YearProductivityData | null;
  loadingSummary: boolean;
  onNavigateToJournal: (dateStr: string) => void;
}

const WEEKDAY_LABELS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
const ARROW_STEPS: Record<string, number> = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: 7, ArrowUp: -7 };

const LEGEND = [
  { label: 'Strong day', fill: TIER_FILL.strong },
  { label: 'Productive', fill: TIER_FILL.productive },
  { label: 'Logged', fill: TIER_FILL.logged },
  { label: 'Not logged', fill: TIER_FILL.unlogged },
  { label: 'Today', fill: 'bg-amber-400 day-today' },
];

export const YearProductivityCalendar: React.FC<YearProductivityCalendarProps> = ({
  summary,
  yearSummary,
  loadingSummary,
  onNavigateToJournal,
}) => {
  const currentSystemYear = new Date().getFullYear();
  const currentSystemMonth = new Date().getMonth() + 1;
  const [selectedYear, setSelectedYear] = useState<number>(currentSystemYear);
  const [calendarData, setCalendarData] = useState<YearProductivityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewDay, setPreviewDay] = useState<YearDayBlock | null>(null);
  const [activeDayDate, setActiveDayDate] = useState<string | null>(null);
  const [focusDate, setFocusDate] = useState<string | null>(null);
  const dotRefs = useRef(new Map<string, HTMLButtonElement>());

  // Lifespan perspective toggle (Preserve 70-Year Memento Mori)
  const [viewPerspective, setViewPerspective] = useState<'year' | 'lifespan'>('year');
  const [lifeGrid, setLifeGrid] = useState<YearGridRow[]>([]);
  const [loadingLifeGrid, setLoadingLifeGrid] = useState(false);

  // Fetch Year Productivity Data
  useEffect(() => {
    let isMounted = true;
    const fetchYearData = async () => {
      try {
        setLoading(true);
        const data = await goalOSApi.getYearProductivity(selectedYear);
        if (isMounted) {
          setCalendarData(data);
          setFocusDate(null);
        }
      } catch (err) {
        console.error('Failed to load year productivity data:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchYearData();
    return () => {
      isMounted = false;
    };
  }, [selectedYear]);

  // Fetch Lifespan grid on-demand if user toggles perspective
  useEffect(() => {
    if (viewPerspective === 'lifespan' && lifeGrid.length === 0) {
      const fetchLifespan = async () => {
        try {
          setLoadingLifeGrid(true);
          const data = await goalOSApi.getCalendarGrid();
          setLifeGrid(data);
        } catch (err) {
          console.error('Failed to load lifespan grid:', err);
        } finally {
          setLoadingLifeGrid(false);
        }
      };
      fetchLifespan();
    }
  }, [viewPerspective, lifeGrid.length]);

  const activeDaySummary = useMemo(() => {
    if (!activeDayDate || !calendarData) return null;
    return calendarData.days.find((d) => d.date === activeDayDate) || null;
  }, [activeDayDate, calendarData]);

  // Roving tab stop: one day in the tab order, arrow keys move between days.
  const tabDate = useMemo(() => {
    if (!calendarData || calendarData.days.length === 0) return null;
    return (
      focusDate ??
      activeDayDate ??
      calendarData.days.find((d) => d.status === 'today')?.date ??
      calendarData.days[0].date
    );
  }, [calendarData, focusDate, activeDayDate]);

  const handleGridKeyDown = (e: React.KeyboardEvent) => {
    const step = ARROW_STEPS[e.key];
    if (!step || !calendarData || !tabDate) return;
    const index = calendarData.days.findIndex((d) => d.date === tabDate);
    const next = calendarData.days[index + step];
    if (!next) return;
    e.preventDefault();
    setFocusDate(next.date);
    dotRefs.current.get(next.date)?.focus();
  };

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-3">
      {viewPerspective === 'year' ? (
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setSelectedYear((y) => y - 1)}
            className="p-1.5 rounded-full text-emerald-800/70 hover:text-emerald-950 hover:bg-emerald-50 transition-colors cursor-pointer"
            aria-label="Previous year"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight tabular-nums px-1">{selectedYear}</h2>
          <button
            type="button"
            onClick={() => setSelectedYear((y) => y + 1)}
            className="p-1.5 rounded-full text-emerald-800/70 hover:text-emerald-950 hover:bg-emerald-50 transition-colors cursor-pointer"
            aria-label="Next year"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Seventy years, week by week</h2>
      )}

      <div className="flex items-center bg-slate-100/80 p-1 rounded-full" role="group" aria-label="Calendar perspective">
        {([
          ['year', 'This year'],
          ['lifespan', '70 years'],
        ] as const).map(([value, label]) => (
          <button
            key={value}
            type="button"
            onClick={() => setViewPerspective(value)}
            aria-pressed={viewPerspective === value}
            className={`px-3.5 py-1 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
              viewPerspective === value ? 'bg-white text-emerald-900 shadow-forest-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <LifeProgressBanner
        summary={summary}
        yearSummary={yearSummary}
        loading={loadingSummary}
        perspective={viewPerspective}
      />

      <div className="glass-panel rounded-3xl shadow-forest p-5 sm:p-7">
        {header}

        {/* ----------------- Year of days: twelve borderless month groups ----------------- */}
        {viewPerspective === 'year' && loading && !calendarData && (
          <div className="mt-6 h-80 rounded-2xl bg-slate-50/70 motion-safe:animate-pulse" aria-hidden="true" />
        )}

        {viewPerspective === 'year' && calendarData && (
          <>
            <div className="mt-5 pb-4 border-b border-emerald-100/70 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 text-xs">
              <ul className="flex flex-wrap items-center gap-x-5 gap-y-2 text-slate-600">
                {LEGEND.map((item) => (
                  <li key={item.label} className="flex items-center gap-2">
                    <span className={`relative w-2.5 h-2.5 rounded-full ${item.fill}`} aria-hidden="true" />
                    <span>{item.label}</span>
                  </li>
                ))}
              </ul>

              <p className="text-slate-500 min-h-[1.25rem] lg:text-right" aria-live="polite">
                {previewDay ? (
                  <span className="text-slate-800">{describeDay(previewDay)}</span>
                ) : (
                  <>
                    <span className="[@media(hover:none)]:hidden">Point at a day to preview it; click to open it.</span>
                    <span className="hidden [@media(hover:none)]:inline">Tap a day to open it.</span>
                  </>
                )}
              </p>
            </div>

            <div
              className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-10 gap-y-8"
              role="group"
              aria-label={`Days of ${selectedYear}. Use the arrow keys to move between days.`}
              onKeyDown={handleGridKeyDown}
            >
              {calendarData.months.map((month) => {
                const monthDays = calendarData.days.filter((d) => d.month === month.month);
                const firstDayWeekday = monthDays.length > 0 ? monthDays[0].day_of_week : 0; // 0 = Mon, 6 = Sun
                const isCurrentMonth = selectedYear === currentSystemYear && month.month === currentSystemMonth;

                return (
                  <section key={month.month} aria-label={month.name}>
                    <div className="flex items-baseline justify-between mb-2.5">
                      <h3 className={`text-sm font-semibold ${isCurrentMonth ? 'text-emerald-800' : 'text-slate-800'}`}>
                        {month.name}
                      </h3>
                      {month.productive_days > 0 && (
                        <span className="text-xs font-medium text-emerald-700 tabular-nums">
                          {month.productive_days} productive
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-7 gap-1.5 justify-items-center mb-1.5 text-[10px] font-medium text-slate-500" aria-hidden="true">
                      {WEEKDAY_LABELS.map((lbl, idx) => (
                        <span key={idx}>{lbl}</span>
                      ))}
                    </div>

                    <div className="grid grid-cols-7 gap-1.5 justify-items-center">
                      {Array.from({ length: firstDayWeekday }).map((_, i) => (
                        <span key={`empty-${i}`} className="w-6 h-6 sm:w-5 sm:h-5" aria-hidden="true" />
                      ))}

                      {monthDays.map((day) => (
                        <DayDot
                          key={day.date}
                          ref={(el) => {
                            if (el) dotRefs.current.set(day.date, el);
                            else dotRefs.current.delete(day.date);
                          }}
                          day={day}
                          selected={activeDayDate === day.date}
                          tabIndex={day.date === tabDate ? 0 : -1}
                          onClick={() => setActiveDayDate(day.date)}
                          onMouseEnter={() => setPreviewDay(day)}
                          onMouseLeave={() => setPreviewDay(null)}
                          onFocus={() => {
                            setFocusDate(day.date);
                            setPreviewDay(day);
                          }}
                          onBlur={() => setPreviewDay(null)}
                        />
                      ))}
                    </div>
                  </section>
                );
              })}
            </div>
          </>
        )}

        {/* ----------------- 70-Year Lifespan Memento Mori Grid (Secondary Perspective) ----------------- */}
        {viewPerspective === 'lifespan' && (
          <div className="mt-5">
            <p className="text-xs text-slate-500 pb-4 border-b border-emerald-100/70">
              Each row is a year of your life, each dot a week.
            </p>
            {loadingLifeGrid ? (
              <div className="mt-6 h-48 rounded-2xl bg-slate-50 motion-safe:animate-pulse" aria-hidden="true" />
            ) : (
              <div className="mt-5 overflow-x-auto pb-2">
                <div
                  className="min-w-[700px]"
                  role="img"
                  aria-label={
                    summary
                      ? `Week ${summary.weeks_lived} of ${summary.total_weeks} in a ${summary.target_age}-year horizon.`
                      : 'Lifespan in weeks.'
                  }
                >
                  <div className="grid grid-cols-[48px_repeat(52,1fr)] gap-1 mb-1.5 text-[10px] font-medium text-slate-500 text-center">
                    <div className="text-right pr-2">Age</div>
                    {Array.from({ length: 52 }, (_, i) => i + 1).map((wk) => (
                      <div key={wk}>{wk === 1 || wk % 10 === 0 ? `wk ${wk}` : ''}</div>
                    ))}
                  </div>

                  <div className="space-y-1">
                    {lifeGrid.map((row) => {
                      const isDecadeMarker = row.age % 10 === 0;
                      const currentAge = summary ? Math.floor(summary.age_years) : null;
                      const isCurrentAge = row.age === currentAge;

                      return (
                        <div
                          key={row.age}
                          className={`grid grid-cols-[48px_repeat(52,1fr)] gap-1 items-center py-0.5 rounded-lg ${
                            isCurrentAge ? 'bg-amber-50/80' : ''
                          }`}
                        >
                          <div
                            className={`text-[11px] text-right pr-2 tabular-nums ${
                              isCurrentAge
                                ? 'text-amber-900 font-semibold'
                                : isDecadeMarker
                                ? 'text-emerald-800 font-semibold'
                                : 'text-slate-500'
                            }`}
                          >
                            {row.age}
                          </div>

                          {row.weeks.map((week) => (
                            <span
                              key={week.global_week}
                              className={`relative aspect-square rounded-full ${
                                week.status === 'past'
                                  ? 'bg-emerald-200/90'
                                  : week.status === 'current'
                                  ? 'bg-amber-400 day-today'
                                  : 'border border-slate-200'
                              }`}
                            />
                          ))}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Structured Day Inspector Drawer (When any circle is clicked) */}
      <DayDetailDrawer
        dateStr={activeDayDate}
        daySummary={activeDaySummary}
        onClose={() => setActiveDayDate(null)}
        onOpenInJournal={(dateStr) => {
          onNavigateToJournal(dateStr);
        }}
      />
    </div>
  );
};
