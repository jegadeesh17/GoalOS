import React, { useState, useEffect } from 'react';
import { Navbar, ActiveTab } from './components/Navbar';
import { LifeProgressBanner } from './components/LifeProgressBanner';
import { YearProductivityCalendar } from './components/YearProductivityCalendar';
import { JournalView } from './components/JournalView';
import { GoalsView } from './components/GoalsView';
import { AICoachView } from './components/AICoachView';
import { AnalyticsView } from './components/AnalyticsView';
import { MemoriesView } from './components/MemoriesView';
import { SettingsView } from './components/SettingsView';
import { LifeSummary, YearProductivityData, goalOSApi } from './api/client';
import { ShieldCheck, Database, Compass, Sparkle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('calendar');
  const [coachInitialMode, setCoachInitialMode] = useState<'morning' | 'evening' | 'weekly' | 'future-self' | 'goal-alignment'>('morning');
  const [lifeSummary, setLifeSummary] = useState<LifeSummary | null>(null);
  const [yearSummary, setYearSummary] = useState<YearProductivityData | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [journalTargetDate, setJournalTargetDate] = useState<string | undefined>(undefined);
  const [healthStatus, setHealthStatus] = useState<{ log_count?: number; memory_count?: number; openrouter_configured?: boolean } | null>(null);

  const fetchSummary = async () => {
    try {
      setLoadingSummary(true);
      const [summary, yearData, health] = await Promise.all([
        goalOSApi.getCalendarSummary(),
        goalOSApi.getYearProductivity().catch((err) => {
          console.warn('Failed to load year productivity summary:', err);
          return null;
        }),
        goalOSApi.getSettings().then((s) => ({
          openrouter_configured: s.openrouter_configured,
        })).catch(() => null),
      ]);
      setLifeSummary(summary);
      if (yearData) setYearSummary(yearData);
      if (health) setHealthStatus(health);
    } catch (err) {
      console.error('Failed to load initial summary:', err);
    } finally {
      setLoadingSummary(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleTriggerCoachFromJournal = (mode: 'morning' | 'evening') => {
    setCoachInitialMode(mode);
    setActiveTab('coach');
  };

  const handleNavigateToJournalWithDate = (dateStr: string) => {
    setJournalTargetDate(dateStr);
    setActiveTab('journal');
  };

  return (
    <div className="min-h-screen flex flex-col text-slate-900 selection:bg-emerald-100 selection:text-emerald-950 relative overflow-x-hidden bg-[#f7f9f7]">
      {/* Floating Sticky Header Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        lifeSummary={lifeSummary}
      />

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
        {/* Life Horizon Progress Banner on top of Calendar, Journal & Goals */}
        {(activeTab === 'calendar' || activeTab === 'journal' || activeTab === 'goals') && (
          <LifeProgressBanner
            summary={lifeSummary}
            yearSummary={yearSummary}
            loading={loadingSummary}
          />
        )}

        {/* Tab Routed Views */}
        {activeTab === 'calendar' && (
          <YearProductivityCalendar
            summary={lifeSummary}
            onNavigateToJournal={handleNavigateToJournalWithDate}
          />
        )}
        {activeTab === 'journal' && (
          <JournalView
            initialDate={journalTargetDate}
            onTriggerCoach={handleTriggerCoachFromJournal}
          />
        )}
        {activeTab === 'goals' && <GoalsView />}
        {activeTab === 'coach' && <AICoachView initialMode={coachInitialMode} />}
        {activeTab === 'analytics' && <AnalyticsView />}
        {activeTab === 'memories' && <MemoriesView />}
        {activeTab === 'settings' && <SettingsView onSettingsSaved={fetchSummary} />}
      </main>


      {/* Footer */}
      <footer className="mt-auto border-t border-emerald-100/70 glass-panel py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-1.5 font-bold text-slate-900">
              <Compass className="w-4 h-4 text-emerald-700" />
              <span>GoalOS v2.1</span>
            </span>
            <span className="text-slate-300">|</span>
            <span className="flex items-center space-x-1 text-slate-600 font-medium">
              <Database className="w-3.5 h-3.5 text-emerald-600/70" />
              <span>Local SQLite & ChromaDB Vector Storage</span>
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1.5 text-emerald-800 font-bold bg-emerald-50/80 px-3 py-1 rounded-full border border-emerald-200/80 shadow-forest-xs">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Local-First Grounded</span>
            </span>
            {healthStatus?.openrouter_configured ? (
              <span className="text-[11px] font-mono font-bold text-emerald-900 bg-gradient-to-r from-emerald-50 to-teal-50 px-3 py-1 rounded-full border border-emerald-200/80 shadow-forest-xs flex items-center space-x-1">
                <Sparkle className="w-2.5 h-2.5 text-amber-500 fill-amber-400" />
                <span>AI Coach Online</span>
              </span>
            ) : (
              <span className="text-[11px] font-mono text-slate-600 bg-slate-100/90 px-3 py-1 rounded-full border border-slate-200/60">
                Deterministic Mode
              </span>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
};
