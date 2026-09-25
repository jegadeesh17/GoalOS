import React, { useState, useEffect, useCallback } from 'react';
import { Navbar, ActiveTab } from './components/Navbar';
import { YearProductivityCalendar } from './components/YearProductivityCalendar';
import { JournalView } from './components/JournalView';
import { GoalsView } from './components/GoalsView';
import { AICoachView } from './components/AICoachView';
import { AnalyticsView } from './components/AnalyticsView';
import { MemoriesView } from './components/MemoriesView';
import { SettingsView } from './components/SettingsView';
import { LifeSummary, YearProductivityData, goalOSApi } from './api/client';
import { ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('calendar');
  const [coachInitialMode, setCoachInitialMode] = useState<'morning' | 'evening' | 'weekly' | 'future-self' | 'goal-alignment'>('morning');
  const [lifeSummary, setLifeSummary] = useState<LifeSummary | null>(null);
  const [yearSummary, setYearSummary] = useState<YearProductivityData | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [journalTargetDate, setJournalTargetDate] = useState<string | undefined>(undefined);
  const [aiConnected, setAiConnected] = useState(false);

  // Only the first load shows a skeleton; later refreshes update the numbers in place.
  const fetchSummary = useCallback(async () => {
    try {
      const [summary, yearData, settings] = await Promise.all([
        goalOSApi.getCalendarSummary(),
        goalOSApi.getYearProductivity().catch((err) => {
          console.warn('Failed to load year productivity summary:', err);
          return null;
        }),
        goalOSApi.getSettings().catch(() => null),
      ]);
      setLifeSummary(summary);
      if (yearData) setYearSummary(yearData);
      if (settings) setAiConnected(!!settings.openrouter_configured);
    } catch (err) {
      console.error('Failed to load initial summary:', err);
    } finally {
      setLoadingSummary(false);
    }
  }, []);

  // Refresh whenever the calendar comes back into view, so journal edits show up in the horizon line.
  useEffect(() => {
    if (activeTab === 'calendar') fetchSummary();
  }, [activeTab, fetchSummary]);

  const handleTriggerCoachFromJournal = (mode: 'morning' | 'evening') => {
    setCoachInitialMode(mode);
    setActiveTab('coach');
  };

  const handleNavigateToJournalWithDate = (dateStr: string) => {
    setJournalTargetDate(dateStr);
    setActiveTab('journal');
  };

  return (
    <div className="min-h-screen flex flex-col text-slate-900 relative overflow-x-hidden">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8 sm:pt-10 pb-10 space-y-6">
        {activeTab === 'calendar' && (
          <YearProductivityCalendar
            summary={lifeSummary}
            yearSummary={yearSummary}
            loadingSummary={loadingSummary}
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

      <footer className="mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <span className="inline-flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
            Stored privately on this device
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${aiConnected ? 'bg-emerald-500' : 'bg-slate-300'}`} aria-hidden="true" />
            {aiConnected ? 'AI coach connected' : 'Coaching from local rules'}
          </span>
        </div>
      </footer>
    </div>
  );
};
