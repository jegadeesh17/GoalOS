import React from 'react';
import { 
  Calendar, 
  BookOpen, 
  Target, 
  Sparkles, 
  BarChart3, 
  Brain, 
  Settings as SettingsIcon,
  Compass
} from 'lucide-react';

export type ActiveTab = 'calendar' | 'journal' | 'goals' | 'coach' | 'analytics' | 'memories' | 'settings';

interface NavbarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  lifeSummary?: {
    age_years: number;
    percentage_lived: number;
    weeks_remaining: number;
  } | null;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, lifeSummary }) => {
  const navItems = [
    { id: 'calendar', label: 'Life Calendar', icon: Calendar },
    { id: 'journal', label: 'Daily Journal', icon: BookOpen },
    { id: 'goals', label: 'Goals & Horizons', icon: Target },
    { id: 'coach', label: 'AI Coach', icon: Sparkles },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'memories', label: 'Memories', icon: Brain },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ] as const;

  const todayFormatted = new Intl.DateTimeFormat('en-US', { 
    weekday: 'short', 
    month: 'short', 
    day: 'numeric' 
  }).format(new Date());

  return (
    <header className="sticky top-3 z-50 px-4 sm:px-6 max-w-7xl mx-auto w-full">
      <div className="bg-white/90 backdrop-blur-2xl rounded-full px-5 py-3 shadow-[0_8px_30px_rgb(79,70,229,0.12)] border border-indigo-100/80 transition-all">
        <div className="flex items-center justify-between">
          {/* Logo & Brand */}
          <div 
            className="flex items-center space-x-2.5 cursor-pointer group" 
            onClick={() => setActiveTab('calendar')}
          >
            <div className="w-9 h-9 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/30 group-hover:scale-105 transition-all">
              <Compass className="w-5 h-5" />
            </div>
            <span className="font-black text-xl text-slate-900 tracking-tight">
              GoalOS
            </span>
          </div>

          {/* Floating Pill Navigation */}
          <nav className="hidden lg:flex items-center space-x-1.5 bg-slate-100/90 p-1.5 rounded-full border border-slate-200 shadow-inner">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-full text-xs font-bold transition-all duration-200 ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 scale-[1.03]'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-white'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Quick Date Status */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 text-xs font-semibold text-slate-700 bg-indigo-50/70 px-4 py-2 rounded-full border border-indigo-100 shadow-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 ring-4 ring-emerald-100 animate-pulse"></span>
              <span className="font-bold text-slate-900">{todayFormatted}</span>
              {lifeSummary && (
                <span className="text-slate-400 border-l border-slate-300 pl-2 font-medium">
                  <strong className="text-indigo-700 font-extrabold">{lifeSummary.percentage_lived}%</strong> lived
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="lg:hidden flex items-center space-x-1.5 pt-2 pb-1 overflow-x-auto border-t border-slate-100 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-700 hover:bg-white bg-slate-100/60'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
