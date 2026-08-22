import React, { useState, useEffect } from 'react';
import { UserSettings, goalOSApi } from '../api/client';
import { 
  Save, 
  Download, 
  AlertOctagon, 
  User, 
  Lock,
  Settings as SettingsIcon
} from 'lucide-react';

interface SettingsViewProps {
  onSettingsSaved?: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onSettingsSaved }) => {
  const [settings, setSettings] = useState<UserSettings>({
    name: 'Jegadeesh',
    birth_date: '2002-06-17',
    target_age: 70,
    life_vision: '',
    five_year_vision: '',
    one_year_vision: '',
    remote_ai_consent: false,
  });
  const [loading, setLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [resetConfirm, setResetConfirm] = useState('');
  const [resetStatus, setResetStatus] = useState<string | null>(null);

  useEffect(() => {
    goalOSApi.getSettings().then((data) => {
      setSettings(data);
      setLoading(false);
    }).catch((err) => {
      console.error('Failed to load settings:', err);
      setLoading(false);
    });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaveStatus('Saving settings to SQLite...');
      const updated = await goalOSApi.updateSettings(settings);
      setSettings(updated);
      setSaveStatus('Settings Saved Successfully!');
      setTimeout(() => setSaveStatus(null), 3000);
      if (onSettingsSaved) onSettingsSaved();
    } catch (err) {
      console.error('Failed to update settings:', err);
      setSaveStatus('Error saving settings');
    }
  };

  const handleExport = async () => {
    try {
      const data = await goalOSApi.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `goalos_export_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      alert('Failed to export data');
    }
  };

  const handleReset = async () => {
    if (resetConfirm !== 'RESET') {
      alert("Type 'RESET' exactly to confirm factory reset.");
      return;
    }
    if (!confirm('Are you sure? A timestamped backup of your SQLite database will be created before resetting.')) {
      return;
    }
    try {
      const res = await goalOSApi.factoryReset();
      setResetStatus(`Reset completed! Backup created at: ${res.backup_created}`);
      setResetConfirm('');
      if (onSettingsSaved) onSettingsSaved();
    } catch (err: any) {
      console.error('Reset failed:', err);
      alert('Reset failed: ' + (err?.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="glass-panel rounded-3xl p-8 animate-pulse">
        <div className="h-6 bg-slate-100 rounded-full w-1/4 mb-4"></div>
        <div className="h-64 bg-slate-50/60 rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="glass-panel rounded-3xl p-6 sm:p-7 shadow-celestial border border-white/80">
        <div className="flex items-center space-x-2 text-xs font-extrabold uppercase tracking-wider text-indigo-700 mb-1">
          <span className="flex items-center space-x-1 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100 shadow-sm font-extrabold">
            <SettingsIcon className="w-3.5 h-3.5 text-indigo-600" />
            <span>Profile & System Configuration</span>
          </span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">Settings & Privacy</h2>
        <p className="text-xs text-slate-500 mt-1 font-medium">
          Configure your life horizons, birth date, AI privacy guardrails, and data exports.
        </p>
      </div>

      {saveStatus && (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 text-emerald-950 text-xs font-bold px-4 py-3 rounded-2xl flex items-center justify-between shadow-sm animate-fadeIn">
          <span>{saveStatus}</span>
        </div>
      )}

      {/* Main Settings Form */}
      <form onSubmit={handleSave} className="space-y-6">
        {/* Identity & Life Horizons */}
        <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-5 shadow-celestial border border-white/80">
          <h3 className="font-extrabold text-base text-slate-900 flex items-center space-x-2">
            <User className="w-4 h-4 text-indigo-600" />
            <span>Profile & Life Horizon Parameters</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-extrabold text-slate-700 uppercase tracking-wider mb-1.5">
                Your Name
              </label>
              <input
                type="text"
                value={settings.name || ''}
                onChange={(e) => setSettings({ ...settings, name: e.target.value })}
                className="w-full text-sm px-4 py-3 rounded-2xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm font-semibold"
              />
            </div>

            <div>
              <label className="block text-xs font-extrabold text-slate-700 uppercase tracking-wider mb-1.5">
                Birth Date *
              </label>
              <input
                type="date"
                required
                value={settings.birth_date || '2002-06-17'}
                onChange={(e) => setSettings({ ...settings, birth_date: e.target.value })}
                className="w-full text-sm px-4 py-3 rounded-2xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm font-semibold cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-xs font-extrabold text-slate-700 uppercase tracking-wider mb-1.5">
                Target Lifespan Horizon (Years)
              </label>
              <input
                type="number"
                min="50"
                max="120"
                value={settings.target_age || 70}
                onChange={(e) => setSettings({ ...settings, target_age: parseInt(e.target.value) || 70 })}
                className="w-full text-sm px-4 py-3 rounded-2xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm font-semibold"
              />
            </div>
          </div>

          <div className="space-y-4 pt-2">
            <div>
              <label className="block text-xs font-extrabold text-slate-700 uppercase tracking-wider mb-1.5">
                10-Year Vision & Long-Term Identity
              </label>
              <textarea
                rows={2}
                placeholder="What is your ultimate 10-year horizon vision?"
                value={settings.life_vision || ''}
                onChange={(e) => setSettings({ ...settings, life_vision: e.target.value })}
                className="w-full text-sm p-4 rounded-2xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm resize-none font-sans font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-extrabold text-slate-700 uppercase tracking-wider mb-1.5">
                5-Year Strategic Goals
              </label>
              <textarea
                rows={2}
                placeholder="Where must you be 5 years from now to align with your life vision?"
                value={settings.five_year_vision || ''}
                onChange={(e) => setSettings({ ...settings, five_year_vision: e.target.value })}
                className="w-full text-sm p-4 rounded-2xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm resize-none font-sans font-medium"
              />
            </div>
          </div>
        </div>

        {/* Privacy & Remote AI Consent */}
        <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-4 shadow-celestial border border-white/80">
          <h3 className="font-extrabold text-base text-slate-900 flex items-center space-x-2">
            <Lock className="w-4 h-4 text-indigo-600" />
            <span>Privacy & AI Connectivity</span>
          </h3>

          <div className="bg-gradient-to-r from-white via-indigo-50/30 to-purple-50/20 p-5 rounded-2xl border border-indigo-100 flex items-start justify-between gap-4 shadow-sm">
            <div className="space-y-1">
              <span className="text-xs font-extrabold text-slate-900 block">Allow Remote AI Coaching (OpenRouter)</span>
              <p className="text-xs text-slate-500 font-medium leading-relaxed">
                When enabled and an OpenRouter API key is configured in <code className="bg-white px-1.5 py-0.5 rounded border border-indigo-100 text-[11px] font-bold text-indigo-700">.env</code>, AI coaching queries use remote LLMs. When disabled, GoalOS operates strictly on deterministic local rules.
              </p>
            </div>

            <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
              <input
                type="checkbox"
                checked={!!settings.remote_ai_consent}
                onChange={(e) => setSettings({ ...settings, remote_ai_consent: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-12 h-6.5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5.5 after:w-5.5 after:transition-all peer-checked:bg-indigo-600 shadow-inner"></div>
            </label>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-full text-xs font-black shadow-md shadow-indigo-600/30 transition-all"
          >
            <Save className="w-4 h-4" />
            <span>Save Settings</span>
          </button>
        </div>
      </form>

      {/* Data Export & Factory Reset Section */}
      <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-6 shadow-celestial border border-white/80">
        <h3 className="font-extrabold text-base text-slate-900 flex items-center space-x-2">
          <Download className="w-4 h-4 text-indigo-600" />
          <span>Data Portability & Database Management</span>
        </h3>

        {/* Export Card */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-5 rounded-2xl border border-indigo-100 bg-white/80 gap-3 shadow-sm">
          <div>
            <h4 className="text-xs font-extrabold text-slate-900">Export JSON Data</h4>
            <p className="text-xs text-slate-500 mt-0.5 font-medium">
              Download all goals, daily logs, memories, and scores in a portable JSON file.
            </p>
          </div>
          <button
            type="button"
            onClick={handleExport}
            className="flex items-center justify-center space-x-1.5 bg-gradient-to-r from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 text-indigo-900 border border-indigo-200 px-5 py-2.5 rounded-full text-xs font-bold transition-all shadow-sm flex-shrink-0"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
        </div>

        {/* Factory Reset Danger Zone */}
        <div className="p-5 rounded-2xl border border-rose-200 bg-rose-50/40 space-y-3 shadow-sm">
          <div className="flex items-center space-x-2 text-rose-700 font-extrabold text-xs">
            <AlertOctagon className="w-4 h-4" />
            <span>Factory Reset (Auto-Backup)</span>
          </div>
          <p className="text-xs text-slate-600 font-medium">
            Creates an automatic timestamped backup in your database directory, then clears all logs and memories.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-2 pt-1">
            <input
              type="text"
              placeholder="Type RESET to confirm"
              value={resetConfirm}
              onChange={(e) => setResetConfirm(e.target.value)}
              className="text-xs px-4 py-2.5 rounded-2xl border border-rose-200 bg-white focus:ring-2 focus:ring-rose-500 w-full sm:w-48 font-mono shadow-sm"
            />
            <button
              type="button"
              disabled={resetConfirm !== 'RESET'}
              onClick={handleReset}
              className="w-full sm:w-auto bg-rose-600 hover:bg-rose-700 disabled:opacity-40 text-white px-5 py-2.5 rounded-full text-xs font-black transition-all shadow-sm"
            >
              Execute Reset
            </button>
          </div>

          {resetStatus && (
            <p className="text-xs text-emerald-700 font-bold pt-1">{resetStatus}</p>
          )}
        </div>
      </div>
    </div>
  );
};
