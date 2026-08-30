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

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'calendar', label: 'Calendar', icon: Calendar },
    { id: 'journal', label: 'Journal', icon: BookOpen },
    { id: 'goals', label: 'Goals', icon: Target },
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
      <div className="bg-white/88 backdrop-blur-2xl rounded-full px-5 py-2 shadow-forest border border-emerald-100/80 transition-all">
        <div className="flex items-center justify-between gap-4">
          {/* Left Cluster: Brand Logo (flex-1) */}
          <div className="flex items-center flex-1 min-w-0">
            <div 
              className="flex items-center space-x-2.5 cursor-pointer group" 
              onClick={() => setActiveTab('calendar')}
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-700 to-teal-600 flex items-center justify-center text-white shadow-forest-xs group-hover:scale-105 transition-all flex-shrink-0">
                <Compass className="w-4 h-4" />
              </div>
              <span className="font-bold text-lg text-slate-900 tracking-tight">
                GoalOS
              </span>
            </div>
          </div>

          {/* Center Cluster: Symmetrically Centered Navigation */}
          <nav className="hidden lg:flex items-center space-x-1 bg-slate-100/70 p-1 rounded-full border border-emerald-100/60 shadow-inner flex-shrink-0">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-150 cursor-pointer ${
                    isActive
                      ? 'bg-emerald-700 text-white shadow-forest-xs'
                      : 'text-slate-700 hover:text-emerald-950 hover:bg-white/90'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Cluster: Date Indicator (flex-1 justify-end) */}
          <div className="hidden sm:flex items-center justify-end flex-1 min-w-0">
            <div className="flex items-center space-x-2 text-xs font-medium text-slate-700 bg-emerald-50/80 px-3.5 py-1.5 rounded-full border border-emerald-100/90 shadow-forest-xs whitespace-nowrap">
              <span className="w-2 h-2 rounded-full bg-emerald-600 ring-4 ring-emerald-200/70 animate-pulse flex-shrink-0"></span>
              <span className="font-semibold text-slate-800">{todayFormatted}</span>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="lg:hidden flex items-center space-x-1 pt-2 pb-1 overflow-x-auto border-t border-emerald-50 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? 'bg-emerald-700 text-white font-semibold shadow-forest-xs'
                    : 'text-slate-700 hover:bg-white bg-slate-100/70'
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
