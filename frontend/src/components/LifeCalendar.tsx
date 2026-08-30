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
        <div className="h-5 bg-slate-100 rounded-full w-1/4 mx-auto mb-4"></div>
        <div className="h-64 bg-slate-50/60 rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-3xl shadow-forest p-6 sm:p-7 transition-all border border-emerald-100/70 relative overflow-hidden">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-emerald-100/60">
        <div>
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-emerald-700 to-teal-600 flex items-center justify-center text-white shadow-forest-xs">
              <Calendar className="w-4 h-4" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">70-Year Life Calendar (Memento Mori)</h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 font-normal">
            3,640 discrete week blocks (52 weeks &times; 70 years) mapping your lifetime horizon.
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center space-x-1.5 bg-slate-100/80 p-1 rounded-full border border-emerald-100/70 backdrop-blur-md">
          <button
            onClick={() => setViewMode('full')}
            className={`px-3.5 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
              viewMode === 'full'
                ? 'bg-emerald-700 text-white shadow-forest-xs'
                : 'text-slate-700 hover:text-slate-900'
            }`}
          >
            Full Lifespan (70 Years)
          </button>
          <button
            onClick={() => setViewMode('currentDecade')}
            className={`px-3.5 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
              viewMode === 'currentDecade'
                ? 'bg-emerald-700 text-white shadow-forest-xs'
                : 'text-slate-700 hover:text-slate-900'
            }`}
          >
            Current Decade (Age {currentDecadeStart}-{currentDecadeStart + 9})
          </button>
        </div>
      </div>

      {/* Interactive Legend & Inspector (Clean & Non-redundant) */}
      <div className="my-4 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-white via-emerald-50/30 to-teal-50/20 p-3.5 rounded-2xl border border-emerald-100/80 text-xs shadow-forest-xs">
        {/* Legend */}
        <div className="flex items-center space-x-5">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-gradient-to-tr from-slate-400 to-emerald-300 shadow-sm"></span>
            <span className="text-slate-700 font-medium">Weeks Lived</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-amber-400 ring-4 ring-amber-200/80 animate-star-pulse"></span>
            <span className="text-amber-950 font-bold">Current Week</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-white border border-emerald-200 shadow-sm"></span>
            <span className="text-slate-600 font-medium">Remaining Weeks</span>
          </div>
        </div>

        {/* Hover Inspector */}
        <div className="text-slate-700 font-medium flex items-center space-x-2 bg-white/95 px-3 py-1 rounded-full border border-emerald-100 shadow-forest-xs">
          <Info className="w-3.5 h-3.5 text-emerald-700" />
          {hoveredWeek ? (
            <span>
              <strong>Age {hoveredWeek.year}</strong>, Week {hoveredWeek.week_of_year} (Global #{hoveredWeek.global_week}) &mdash;{' '}
              <span className={hoveredWeek.status === 'current' ? 'text-amber-700 font-bold' : 'text-emerald-700 font-semibold'}>
                {hoveredWeek.status.toUpperCase()}
              </span>
            </span>
          ) : (
            <span className="text-slate-400 italic">Hover over any week block to inspect</span>
          )}
        </div>
      </div>

      {/* 3,640 Week Grid */}
      <div className="overflow-x-auto pb-2">
        <div className="min-w-[700px]">
          {/* Week column hints */}
          <div className="grid grid-cols-[48px_repeat(52,1fr)] gap-1 mb-1 text-xs text-slate-400 font-mono text-center">
            <div className="font-semibold text-slate-500">AGE</div>
            {Array.from({ length: 52 }, (_, i) => i + 1).map((wk) => (
              <div key={wk} className={wk % 10 === 0 || wk === 1 || wk === 52 ? 'text-emerald-700 font-semibold' : 'opacity-30'}>
                {wk % 10 === 0 ? wk : ''}
              </div>
            ))}
          </div>

          {/* Grid Rows */}
          <div className="space-y-1">
            {displayedGrid.map((row) => {
              const isDecadeMarker = row.age % 10 === 0;
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
                  {/* Age Label */}
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

                  {/* 52 Week Nodes */}
                  {row.weeks.map((week) => {
                    let nodeStyle = 'bg-white/90 border border-slate-200/90 hover:border-emerald-500 hover:scale-150 hover:z-20 hover:shadow-forest-xs';
                    if (week.status === 'past') {
                      nodeStyle = 'bg-gradient-to-tr from-slate-300 to-emerald-200/90 hover:from-slate-400 hover:to-emerald-400 hover:scale-150 hover:z-20 hover:shadow-forest-xs';
                    } else if (week.status === 'current') {
                      nodeStyle = 'bg-gradient-to-r from-amber-400 to-emerald-400 ring-4 ring-amber-300/80 animate-star-pulse scale-125 z-30 shadow-glow-amber';
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
