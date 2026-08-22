import React, { useState, useEffect, useMemo } from 'react';
import { YearGridRow, WeekBlock, goalOSApi, LifeSummary } from '../api/client';
import { Info, Calendar } from 'lucide-react';

interface LifeCalendarProps {
  summary: LifeSummary | null;
}

export const LifeCalendar: React.FC<LifeCalendarProps> = ({ summary }) => {
  const [grid, setGrid] = useState<YearGridRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredWeek, setHoveredWeek] = useState<WeekBlock | null>(null);
  const [viewMode, setViewMode] = useState<'full' | 'currentDecade'>('full');

  useEffect(() => {
    const fetchGrid = async () => {
      try {
        setLoading(true);
        const data = await goalOSApi.getCalendarGrid();
        setGrid(data);
      } catch (err) {
        console.error('Failed to load life calendar grid:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchGrid();
  }, []);

  const currentAge = summary ? Math.floor(summary.age_years) : 22;
  const currentDecadeStart = Math.floor(currentAge / 10) * 10;

  const displayedGrid = useMemo(() => {
    if (viewMode === 'currentDecade') {
      return grid.filter((row) => row.age >= currentDecadeStart && row.age < currentDecadeStart + 10);
    }
    return grid;
  }, [grid, viewMode, currentDecadeStart]);

  if (loading) {
    return (
      <div className="glass-panel rounded-3xl p-8 text-center animate-pulse">
        <div className="h-6 bg-slate-100 rounded-full w-1/4 mx-auto mb-4"></div>
        <div className="h-64 bg-slate-50/60 rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-3xl shadow-celestial p-6 sm:p-7 transition-all border border-white/80 relative overflow-hidden">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-5 border-b border-indigo-100/60">
        <div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-sm">
              <Calendar className="w-4 h-4" />
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">70-Year Life Calendar (Memento Mori)</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            3,640 discrete week blocks (52 weeks &times; 70 years) mapping your complete life trajectory.
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center space-x-2 bg-slate-100/80 p-1 rounded-full border border-slate-200/60 backdrop-blur-md">
          <button
            onClick={() => setViewMode('full')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
              viewMode === 'full'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Full Lifespan (70 Years)
          </button>
          <button
            onClick={() => setViewMode('currentDecade')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
              viewMode === 'currentDecade'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Current Decade (Age {currentDecadeStart}-{currentDecadeStart + 9})
          </button>
        </div>
      </div>

      {/* Interactive Legend & Inspector */}
      <div className="my-5 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-white via-indigo-50/30 to-purple-50/20 p-4 rounded-2xl border border-indigo-100/70 text-xs shadow-sm">
        {/* Legend */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-gradient-to-tr from-slate-400 to-indigo-300 shadow-sm"></span>
            <span className="text-slate-700 font-semibold">Weeks Lived ({summary?.weeks_lived})</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3.5 h-3.5 rounded-full bg-amber-400 ring-4 ring-amber-200/80 animate-star-pulse"></span>
            <span className="text-amber-900 font-extrabold">Current Week</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-white border border-indigo-200 shadow-sm"></span>
            <span className="text-slate-600 font-semibold">Remaining Weeks ({summary?.weeks_remaining})</span>
          </div>
        </div>

        {/* Hover Inspector */}
        <div className="text-slate-700 font-medium flex items-center space-x-2 bg-white/90 px-3.5 py-1.5 rounded-full border border-indigo-100 shadow-sm">
          <Info className="w-3.5 h-3.5 text-indigo-600" />
          {hoveredWeek ? (
            <span>
              <strong>Age {hoveredWeek.year}</strong>, Week {hoveredWeek.week_of_year} (Global Week #{hoveredWeek.global_week}) &mdash;{' '}
              <span className={hoveredWeek.status === 'current' ? 'text-amber-600 font-black' : 'text-indigo-600 font-bold'}>
                {hoveredWeek.status.toUpperCase()}
              </span>
            </span>
          ) : (
            <span className="text-slate-400 italic">Hover over any week block to inspect</span>
          )}
        </div>
      </div>

      {/* 3,640 Week Grid */}
      <div className="overflow-x-auto pb-3">
        <div className="min-w-[700px]">
          {/* Week column hints */}
          <div className="grid grid-cols-[52px_repeat(52,1fr)] gap-1 mb-1.5 text-[10px] text-slate-400 font-mono text-center">
            <div className="font-bold text-slate-500">AGE</div>
            {Array.from({ length: 52 }, (_, i) => i + 1).map((wk) => (
              <div key={wk} className={wk % 10 === 0 || wk === 1 || wk === 52 ? 'text-indigo-600 font-bold' : 'opacity-30'}>
                {wk % 10 === 0 ? wk : ''}
              </div>
            ))}
          </div>

          {/* Grid Rows */}
          <div className="space-y-1.5">
            {displayedGrid.map((row) => {
              const isDecadeMarker = row.age % 10 === 0;
              const isCurrentAge = row.age === currentAge;

              return (
                <div
                  key={row.age}
                  className={`grid grid-cols-[52px_repeat(52,1fr)] gap-1 items-center p-1 rounded-xl transition-all ${
                    isCurrentAge
                      ? 'bg-amber-50/70 ring-1 ring-amber-300 shadow-sm'
                      : isDecadeMarker
                      ? 'bg-indigo-50/40 border border-indigo-100/50'
                      : ''
                  }`}
                >
                  {/* Age Label */}
                  <div
                    className={`text-[11px] font-mono font-bold text-right pr-2.5 ${
                      isCurrentAge
                        ? 'text-amber-800 font-extrabold'
                        : isDecadeMarker
                        ? 'text-indigo-700 font-extrabold'
                        : 'text-slate-400'
                    }`}
                  >
                    {row.age}
                  </div>

                  {/* 52 Week Nodes */}
                  {row.weeks.map((week) => {
                    let nodeStyle = 'bg-white/80 border border-slate-200/90 hover:border-indigo-500 hover:scale-150 hover:z-20 hover:shadow-sm';
                    if (week.status === 'past') {
                      nodeStyle = 'bg-gradient-to-tr from-slate-300 to-indigo-200 hover:from-slate-400 hover:to-indigo-400 hover:scale-150 hover:z-20 hover:shadow-sm';
                    } else if (week.status === 'current') {
                      nodeStyle = 'bg-gradient-to-r from-amber-400 to-rose-400 ring-4 ring-amber-300/80 animate-star-pulse scale-125 z-30 shadow-glow-amber';
                    }

                    return (
                      <button
                        key={week.global_week}
                        onMouseEnter={() => setHoveredWeek(week)}
                        onMouseLeave={() => setHoveredWeek(null)}
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
    </div>
  );
};
