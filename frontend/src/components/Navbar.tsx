import React, { useEffect, useRef } from 'react';
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
}

const NAV_ITEMS = [
  { id: 'calendar', label: 'Calendar', icon: Calendar },
  { id: 'journal', label: 'Journal', icon: BookOpen },
  { id: 'goals', label: 'Goals', icon: Target },
  { id: 'coach', label: 'AI Coach', icon: Sparkles },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'memories', label: 'Memories', icon: Brain },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
] as const;

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const mobileRefs = useRef(new Map<string, HTMLButtonElement>());

  // Keep the active tab visible in the scrolling phone row.
  useEffect(() => {
    mobileRefs.current.get(activeTab)?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }, [activeTab]);

  const todayFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric'
  }).format(new Date());

  return (
    <header className="sticky top-3 z-40 px-4 sm:px-6 max-w-7xl mx-auto w-full">
      <div className="bg-white/95 rounded-3xl lg:rounded-full px-4 sm:px-5 py-2 shadow-forest border border-emerald-100/80">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center flex-1 min-w-0">
            <button
              type="button"
              className="flex items-center gap-2.5 cursor-pointer group rounded-xl"
              onClick={() => setActiveTab('calendar')}
              aria-label="GoalOS, go to calendar"
            >
              <span className="w-8 h-8 rounded-xl bg-emerald-700 flex items-center justify-center text-white shadow-forest-xs motion-safe:group-hover:scale-105 transition-transform flex-shrink-0">
                <Compass className="w-4 h-4" />
              </span>
              <span className="font-bold text-lg text-slate-900 tracking-tight">GoalOS</span>
            </button>
          </div>

          <nav aria-label="Primary" className="hidden lg:flex items-center gap-1 bg-slate-100/70 p-1 rounded-full flex-shrink-0">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveTab(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors duration-150 cursor-pointer ${
                    isActive
                      ? 'bg-emerald-700 text-white shadow-forest-xs'
                      : 'text-slate-700 hover:text-emerald-950 hover:bg-white'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          <div className="hidden sm:flex items-center justify-end flex-1 min-w-0">
            <p className="flex items-center gap-2 text-xs font-semibold text-slate-700 whitespace-nowrap">
              <span className="w-2 h-2 rounded-full bg-amber-400" aria-hidden="true" />
              {todayFormatted}
            </p>
          </div>
        </div>

        <nav aria-label="Primary" className="lg:hidden flex items-center gap-1 pt-2 pb-1 mt-2 border-t border-emerald-50 overflow-x-auto scroll-fade-x">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                ref={(el) => {
                  if (el) mobileRefs.current.set(item.id, el);
                  else mobileRefs.current.delete(item.id);
                }}
                type="button"
                onClick={() => setActiveTab(item.id)}
                aria-current={isActive ? 'page' : undefined}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition-colors cursor-pointer ${
                  isActive
                    ? 'bg-emerald-700 text-white font-semibold shadow-forest-xs'
                    : 'text-slate-700 font-medium hover:bg-slate-100'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
          <span className="w-6 shrink-0" aria-hidden="true" />
        </nav>
      </div>
    </header>
  );
};
