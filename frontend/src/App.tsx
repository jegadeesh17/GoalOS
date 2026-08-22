import React, { useState, useEffect } from 'react';
import { Navbar, ActiveTab } from './components/Navbar';
import { LifeProgressBanner } from './components/LifeProgressBanner';
import { LifeCalendar } from './components/LifeCalendar';
import { JournalView } from './components/JournalView';
import { GoalsView } from './components/GoalsView';
import { AICoachView } from './components/AICoachView';
import { AnalyticsView } from './components/AnalyticsView';
import { MemoriesView } from './components/MemoriesView';
import { SettingsView } from './components/SettingsView';
import { LifeSummary, goalOSApi } from './api/client';
import { ShieldCheck, Database, Compass, Sparkle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('calendar');
  const [coachInitialMode, setCoachInitialMode] = useState<'morning' | 'evening' | 'weekly' | 'future-self' | 'goal-alignment'>('morning');
  const [lifeSummary, setLifeSummary] = useState<LifeSummary | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [healthStatus, setHealthStatus] = useState<{ log_count?: number; memory_count?: number; openrouter_configured?: boolean } | null>(null);

  const fetchSummary = async () => {
    try {
      setLoadingSummary(true);
      const [summary, health] = await Promise.all([
        goalOSApi.getCalendarSummary(),
        goalOSApi.getSettings().then((s) => ({
          openrouter_configured: s.openrouter_configured,
        })).catch(() => null),
      ]);
      setLifeSummary(summary);
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

  return (
    <div className="min-h-screen flex flex-col text-slate-900 selection:bg-indigo-100 selection:text-indigo-950 relative overflow-x-hidden">
      {/* Luminous Ambient Aurora Orbs in Background */}
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-gradient-to-br from-indigo-200/40 via-purple-200/30 to-transparent rounded-full blur-3xl pointer-events-none -z-10 animate-float"></div>
      <div className="fixed top-1/3 right-10 w-96 h-96 bg-gradient-to-br from-amber-100/50 via-rose-100/30 to-transparent rounded-full blur-3xl pointer-events-none -z-10 animate-float" style={{ animationDelay: '-2s' }}></div>
      <div className="fixed bottom-10 left-10 w-96 h-96 bg-gradient-to-tr from-cyan-100/40 via-indigo-100/30 to-transparent rounded-full blur-3xl pointer-events-none -z-10"></div>

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
          <LifeProgressBanner summary={lifeSummary} loading={loadingSummary} />
        )}

        {/* Tab Routed Views */}
        {activeTab === 'calendar' && <LifeCalendar summary={lifeSummary} />}
        {activeTab === 'journal' && <JournalView onTriggerCoach={handleTriggerCoachFromJournal} />}
        {activeTab === 'goals' && <GoalsView />}
        {activeTab === 'coach' && <AICoachView initialMode={coachInitialMode} />}
        {activeTab === 'analytics' && <AnalyticsView />}
        {activeTab === 'memories' && <MemoriesView />}
        {activeTab === 'settings' && <SettingsView onSettingsSaved={fetchSummary} />}
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-indigo-100/60 glass-panel py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-1.5 font-bold text-slate-800">
              <Compass className="w-4 h-4 text-indigo-600" />
              <span>GoalOS v2.1</span>
            </span>
            <span className="text-slate-300">|</span>
            <span className="flex items-center space-x-1 text-slate-500 font-medium">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span>Local SQLite & ChromaDB Vector Storage</span>
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1.5 text-emerald-700 font-bold bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 shadow-sm">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>Local-First Grounded</span>
            </span>
            {healthStatus?.openrouter_configured ? (
              <span className="text-[11px] font-mono font-bold text-indigo-800 bg-gradient-to-r from-indigo-50 to-purple-50 px-3 py-1 rounded-full border border-indigo-200 shadow-sm flex items-center space-x-1">
                <Sparkle className="w-2.5 h-2.5 text-amber-500 fill-amber-400" />
                <span>AI Coach Online</span>
              </span>
            ) : (
              <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
                Deterministic Mode
              </span>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
};
