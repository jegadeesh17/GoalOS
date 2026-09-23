import React, { useState, useEffect, useMemo } from 'react';
import { 
  YearProductivityData, 
  YearDayBlock, 
  LifeSummary, 
  YearGridRow, 
  goalOSApi 
} from '../api/client';
import { DayDetailDrawer } from './DayDetailDrawer';
import { 
  Calendar as CalendarIcon, 
  Flame, 
  Info, 
  ChevronLeft, 
  ChevronRight, 
  Target, 
  Hourglass 
} from 'lucide-react';

interface YearProductivityCalendarProps {
  summary: LifeSummary | null;
  onNavigateToJournal: (dateStr: string) => void;
}

export const YearProductivityCalendar: React.FC<YearProductivityCalendarProps> = ({
  summary,
  onNavigateToJournal,
}) => {
  const currentSystemYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState<number>(currentSystemYear);
  const [calendarData, setCalendarData] = useState<YearProductivityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [hoveredDay, setHoveredDay] = useState<YearDayBlock | null>(null);
  const [activeDayDate, setActiveDayDate] = useState<string | null>(null);


  // Lifespan perspective toggle (Preserve 70-Year Memento Mori)
  const [viewPerspective, setViewPerspective] = useState<'yearProductivity' | 'lifespanHorizon'>('yearProductivity');
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
    if (viewPerspective === 'lifespanHorizon' && lifeGrid.length === 0) {
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

  const weekDayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

  if (loading && !calendarData) {
    return (
      <div className="glass-panel rounded-3xl p-8 text-center animate-pulse space-y-4">
        <div className="h-6 bg-slate-100 rounded-full w-1/4 mx-auto"></div>
        <div className="h-80 bg-slate-50/70 rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Perspective Toggle & Main Calendar Container */}
      <div className="glass-panel rounded-3xl shadow-forest p-6 sm:p-7 transition-all border border-emerald-100/70 relative overflow-hidden">
        {/* Header Controls */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-5 border-b border-emerald-100/70">
          <div>
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-700 to-teal-600 flex items-center justify-center text-white shadow-forest-xs">
                <CalendarIcon className="w-4 h-4" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                {viewPerspective === 'yearProductivity'
                  ? `${selectedYear} Daily Productivity Calendar`
                  : '70-Year Lifespan (Memento Mori)'}
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 font-normal">
              {viewPerspective === 'yearProductivity'
                ? 'Every circle represents a day. Filled circles track your productive execution across the year.'
                : '3,640 discrete week blocks (52 weeks × 70 years) mapping your lifetime horizon.'}
            </p>
          </div>

          {/* Perspective & Year Switcher Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Year Selector (when in Year Productivity mode) */}
            {viewPerspective === 'yearProductivity' && (
              <div className="flex items-center bg-slate-100/80 p-1 rounded-full border border-emerald-100/70">
                <button
                  onClick={() => setSelectedYear((y) => y - 1)}
                  className="p-1 rounded-full hover:bg-white text-slate-600 hover:text-slate-900 transition-all cursor-pointer"
                  title="Previous Year"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-2.5 text-xs font-bold font-mono text-slate-900">{selectedYear}</span>
                <button
                  onClick={() => setSelectedYear((y) => y + 1)}
                  className="p-1 rounded-full hover:bg-white text-slate-600 hover:text-slate-900 transition-all cursor-pointer"
                  title="Next Year"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* View Mode Perspective Toggle */}
            <div className="flex items-center bg-slate-100/80 p-1 rounded-full border border-emerald-100/70">
              <button
                onClick={() => setViewPerspective('yearProductivity')}
                className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  viewPerspective === 'yearProductivity'
                    ? 'bg-emerald-700 text-white shadow-forest-xs'
                    : 'text-slate-700 hover:text-slate-900'
                }`}
              >
                <Flame className="w-3.5 h-3.5" />
                <span>{selectedYear} Productivity</span>
              </button>

              <button
                onClick={() => setViewPerspective('lifespanHorizon')}
                className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  viewPerspective === 'lifespanHorizon'
                    ? 'bg-emerald-700 text-white shadow-forest-xs'
                    : 'text-slate-700 hover:text-slate-900'
                }`}
              >
                <Hourglass className="w-3.5 h-3.5" />
                <span>70-Year Horizon</span>
              </button>
            </div>
          </div>
        </div>

        {/* ----------------- VIEW 1: Current Year Productivity Calendar (12-Month Grouped Grid) ----------------- */}
        {viewPerspective === 'yearProductivity' && calendarData && (
          <div className="mt-5 space-y-6">
            {/* Filter Pills & Interactive Legend */}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-gradient-to-r from-white via-emerald-50/30 to-teal-50/20 p-3.5 rounded-2xl border border-emerald-100/80 text-xs shadow-forest-xs">
              {/* Legend */}
              <div className="flex flex-wrap items-center gap-3 sm:gap-5">
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-gradient-to-tr from-emerald-700 to-teal-500 shadow-sm ring-1 ring-emerald-400/50"></span>
                  <span className="text-slate-700 font-medium">High Productivity (≥70)</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 shadow-sm"></span>
                  <span className="text-slate-700 font-medium">Productive</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-50 border border-emerald-300"></span>
                  <span className="text-slate-600 font-medium">Light Execution</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-100 border border-slate-300"></span>
                  <span className="text-slate-500 font-medium">Unlogged Past</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-3 h-3 rounded-full bg-amber-400 ring-3 ring-amber-200/90 animate-star-pulse"></span>
                  <span className="text-amber-950 font-bold">Today</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-white border border-dashed border-emerald-200"></span>
                  <span className="text-slate-400 font-normal">Future</span>
                </div>
              </div>

              {/* Hover / Selection Inspector Snippet */}
              <div className="flex items-center space-x-2 text-slate-700 font-medium bg-white/95 px-3 py-1.5 rounded-full border border-emerald-100 shadow-forest-xs min-h-[32px]">
                <Info className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
                {hoveredDay ? (
                  <span className="truncate">
                    <strong>{hoveredDay.date}</strong> &mdash;{' '}
                    {hoveredDay.is_productive ? (
                      <span className="text-emerald-700 font-bold">Productive Day ✓</span>
                    ) : hoveredDay.status === 'today' ? (
                      <span className="text-amber-700 font-bold">Today</span>
                    ) : hoveredDay.status === 'future' ? (
                      <span className="text-slate-400">Future</span>
                    ) : hoveredDay.has_log ? (
                      <span className="text-slate-600">Logged (Light Execution)</span>
                    ) : (
                      <span className="text-slate-400 italic">No log</span>
                    )}
                    {hoveredDay.productivity_score !== null && hoveredDay.productivity_score !== undefined && (
                      <span className="ml-1 text-slate-500 font-mono">({Math.round(hoveredDay.productivity_score)} pts)</span>
                    )}
                    {hoveredDay.deep_work_hours ? (
                      <span className="ml-1 text-emerald-800 font-mono">&middot; {hoveredDay.deep_work_hours}h deep work</span>
                    ) : null}
                  </span>
                ) : (
                  <span className="text-slate-400 italic">Hover or click any circle to inspect details</span>
                )}
              </div>
            </div>

            {/* 12-Month Grouped Grid (Decision 1: Option A) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {calendarData.months.map((month) => {
                const monthDays = calendarData.days.filter((d) => d.month === month.month);
                const firstDayWeekday = monthDays.length > 0 ? monthDays[0].day_of_week : 0; // 0 = Mon, 6 = Sun

                return (
                  <div
                    key={month.month}
                    className="glass-panel rounded-2xl p-4 border border-emerald-100/70 hover:border-emerald-200 transition-all flex flex-col justify-between"
                  >
                    {/* Month Header */}
                    <div className="flex items-center justify-between pb-2.5 mb-2 border-b border-emerald-50">
                      <div className="flex items-baseline space-x-1.5">
                        <span className="font-bold text-sm text-slate-900">{month.name}</span>
                        <span className="text-[11px] font-mono text-slate-400">({month.total_days}d)</span>
                      </div>

                      {/* Month Productive Badge */}
                      <span
                        className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                          month.productive_days > 0
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : 'bg-slate-50 text-slate-500 border-slate-200'
                        }`}
                      >
                        {month.productive_days} productive
                      </span>
                    </div>

                    {/* Weekday Header Row */}
                    <div className="grid grid-cols-7 gap-1 text-center mb-1 text-[10px] font-semibold text-slate-400 font-mono">
                      {weekDayLabels.map((lbl, idx) => (
                        <div key={idx}>{lbl}</div>
                      ))}
                    </div>

                    {/* Day Circles Grid */}
                    <div className="grid grid-cols-7 gap-1.5 items-center justify-items-center">
                      {/* Leading empty slots for weekday alignment */}
                      {Array.from({ length: firstDayWeekday }).map((_, i) => (
                        <div key={`empty-${i}`} className="w-5 h-5 opacity-0" />
                      ))}

                      {/* Month Days */}
                      {monthDays.map((day) => {
                        const isHighProductivity =
                          day.is_productive &&
                          day.productivity_score !== null &&
                          day.productivity_score !== undefined &&
                          day.productivity_score >= 70;

                        let circleStyle =
                          'bg-white/80 border border-dashed border-emerald-100/90 text-slate-300 hover:scale-130';

                        if (day.status === 'today') {
                          circleStyle =
                            'bg-amber-400 ring-3 ring-amber-300 animate-star-pulse scale-110 z-10 shadow-glow-amber';
                        } else if (isHighProductivity) {
                          circleStyle =
                            'bg-gradient-to-tr from-emerald-700 to-teal-500 ring-1 ring-emerald-300 shadow-forest-xs hover:scale-140 z-10';
                        } else if (day.is_productive) {
                          circleStyle =
                            'bg-emerald-600 hover:bg-emerald-500 shadow-forest-xs hover:scale-140 z-10';
                        } else if (day.status === 'past') {
                          if (day.has_log) {
                            circleStyle =
                              'bg-emerald-50 border border-emerald-300/80 hover:bg-emerald-100 hover:scale-130';
                          } else {
                            circleStyle =
                              'bg-slate-100 border border-slate-200 hover:border-slate-400 hover:scale-125';
                          }
                        }

                        const isSelected = activeDayDate === day.date;

                        return (
                          <button
                            key={day.date}
                            onClick={() => setActiveDayDate(day.date)}
                            onMouseEnter={() => setHoveredDay(day)}
                            onMouseLeave={() => setHoveredDay(null)}
                            className={`w-5 h-5 rounded-full transition-all duration-150 cursor-pointer relative flex items-center justify-center text-[9px] font-mono select-none ${circleStyle} ${
                              isSelected ? 'ring-2 ring-emerald-700 ring-offset-1 scale-125 z-20' : ''
                            }`}
                            aria-label={`${day.date}: ${day.is_productive ? 'Productive' : day.status}`}
                          >
                            <span className="sr-only">{day.day}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Quick Helper CTA */}
            <div className="flex items-center justify-between pt-4 border-t border-emerald-100/60 text-xs text-slate-500">
              <span className="flex items-center space-x-1.5">
                <Target className="w-3.5 h-3.5 text-emerald-700" />
                <span>
                  <strong>Tip:</strong> Click any day circle to inspect its morning intentions, completed tasks, evening reflections, and deep work hours.
                </span>
              </span>
              <span className="font-mono text-slate-400">
                {calendarData.total_days} Discrete Days &middot; {calendarData.productive_days_count} Productive Days
              </span>
            </div>
          </div>
        )}

        {/* ----------------- VIEW 2: 70-Year Lifespan Memento Mori Grid (Secondary Perspective) ----------------- */}
        {viewPerspective === 'lifespanHorizon' && (
          <div className="mt-5 space-y-4">
            {loadingLifeGrid ? (
              <div className="py-12 text-center animate-pulse space-y-3">
                <div className="h-5 bg-slate-100 rounded-full w-1/4 mx-auto"></div>
                <div className="h-48 bg-slate-50 rounded-2xl"></div>
              </div>
            ) : (
              <div className="overflow-x-auto pb-2">
                <div className="min-w-[700px]">
                  <div className="grid grid-cols-[48px_repeat(52,1fr)] gap-1 mb-1 text-xs text-slate-400 font-mono text-center">
                    <div className="font-semibold text-slate-500">AGE</div>
                    {Array.from({ length: 52 }, (_, i) => i + 1).map((wk) => (
                      <div
                        key={wk}
                        className={wk % 10 === 0 || wk === 1 || wk === 52 ? 'text-emerald-700 font-semibold' : 'opacity-30'}
                      >
                        {wk % 10 === 0 ? wk : ''}
                      </div>
                    ))}
                  </div>

                  <div className="space-y-1">
                    {lifeGrid.map((row) => {
                      const isDecadeMarker = row.age % 10 === 0;
                      const currentAge = summary ? Math.floor(summary.age_years) : 22;
                      const isCurrentAge = row.age === currentAge;

                      return (
                        <div
                          key={row.age}
                          className={`grid grid-cols-[48px_repeat(52,1fr)] gap-1 items-center p-0.5 rounded-xl transition-all ${
                            isCurrentAge
                              ? 'bg-amber-50/70 ring-1 ring-amber-300 shadow-forest-xs'
                              : isDecadeMarker
                              ? 'bg-emerald-50/40 border border-emerald-100/50'
                              : ''
                          }`}
                        >
                          <div
                            className={`text-xs font-mono text-right pr-2 ${
                              isCurrentAge
                                ? 'text-amber-800 font-bold'
                                : isDecadeMarker
                                ? 'text-emerald-800 font-bold'
                                : 'text-slate-400 font-normal'
                            }`}
                          >
                            {row.age}
                          </div>

                          {row.weeks.map((week) => {
                            let nodeStyle =
                              'bg-white/90 border border-slate-200/90 hover:border-emerald-500 hover:scale-150 hover:z-20';
                            if (week.status === 'past') {
                              nodeStyle =
                                'bg-gradient-to-tr from-slate-300 to-emerald-200/90 hover:from-slate-400 hover:to-emerald-400 hover:scale-150 hover:z-20';
                            } else if (week.status === 'current') {
                              nodeStyle =
                                'bg-gradient-to-r from-amber-400 to-emerald-400 ring-4 ring-amber-300/80 animate-star-pulse scale-125 z-30 shadow-glow-amber';
                            }

                            return (
                              <button
                                key={week.global_week}
                                className={`aspect-square rounded-full transition-all duration-150 relative cursor-pointer ${nodeStyle}`}
                                aria-label={`Age ${week.year}, Week ${week.week_of_year}`}
                              />
                            );
                          })}
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
