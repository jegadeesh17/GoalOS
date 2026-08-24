import React, { useState, useEffect, useMemo } from 'react';
import { Memory, goalOSApi } from '../api/client';
import { 
  Search, 
  Plus, 
  Trash2, 
  Sparkles,
  Brain,
  Table as TableIcon,
  LayoutGrid,
  Calendar,
  Layers,
  Lightbulb,
  BookOpen,
  Award,
  Fingerprint
} from 'lucide-react';

export const MemoriesView: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
  const [loading, setLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [newMemoryText, setNewMemoryText] = useState('');
  const [newMemoryType, setNewMemoryType] = useState('insight');
  const [newMemoryImportance, setNewMemoryImportance] = useState(0.8);

  const loadMemories = async () => {
    try {
      setLoading(true);
      const list = await goalOSApi.listMemories(100);
      setMemories(list);
    } catch (err) {
      console.error('Failed to load memories:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      setIsSearching(true);
      const results = await goalOSApi.searchMemories(searchQuery.trim(), 20);
      setSearchResults(results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleCreateMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemoryText.trim()) return;
    try {
      await goalOSApi.createMemory({
        text: newMemoryText.trim(),
        memory_type: newMemoryType,
        importance: newMemoryImportance,
        source_date: new Date().toISOString().split('T')[0],
      });
      setNewMemoryText('');
      loadMemories();
    } catch (err) {
      console.error('Failed to store memory:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this memory?')) return;
    try {
      await goalOSApi.deleteMemory(id);
      loadMemories();
      if (searchResults) {
        setSearchResults(searchResults.filter((r) => r.id !== id));
      }
    } catch (err) {
      console.error('Failed to delete memory:', err);
    }
  };

  const displayedList = useMemo(() => {
    const rawList = searchResults !== null ? searchResults : memories;
    if (selectedType === 'all') return rawList;
    return rawList.filter((m) => (m.memory_type || '').toLowerCase() === selectedType.toLowerCase());
  }, [searchResults, memories, selectedType]);

  const getTypeBadge = (type: string) => {
    const t = (type || 'insight').toLowerCase();
    switch (t) {
      case 'principle':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200/70 px-2.5 py-0.5 rounded-full shadow-xs">
            <Award className="w-3 h-3 text-amber-600" />
            <span className="capitalize">Principle</span>
          </span>
        );
      case 'lesson':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/70 px-2.5 py-0.5 rounded-full shadow-xs">
            <BookOpen className="w-3 h-3 text-emerald-600" />
            <span className="capitalize">Lesson</span>
          </span>
        );
      case 'identity':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-semibold bg-purple-50 text-purple-800 border border-purple-200/70 px-2.5 py-0.5 rounded-full shadow-xs">
            <Fingerprint className="w-3 h-3 text-purple-600" />
            <span className="capitalize">Identity</span>
          </span>
        );
      case 'insight':
      default:
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-semibold bg-indigo-50 text-indigo-800 border border-indigo-200/70 px-2.5 py-0.5 rounded-full shadow-xs">
            <Lightbulb className="w-3 h-3 text-indigo-600" />
            <span className="capitalize">Insight</span>
          </span>
        );
    }
  };


  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-3xl p-6 sm:p-7 shadow-celestial border border-white/80">
        <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-indigo-700 mb-1">
          <span className="flex items-center space-x-1 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-100 shadow-sm font-semibold">
            <Brain className="w-3.5 h-3.5 text-indigo-600" />
            <span>Memory & Cognitive Base</span>
          </span>
        </div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Memories & Insights</h2>
        <p className="text-xs text-slate-500 mt-0.5 font-normal">
          Search and retrieve past lessons, mental models, operating principles, and breakthroughs.
        </p>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mt-4 flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search past insights, mental models, lessons, and breakthroughs..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                if (!e.target.value.trim()) setSearchResults(null);
              }}
              className="w-full text-xs pl-10 pr-3.5 py-2.5 rounded-full border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-full text-xs font-semibold shadow-sm flex items-center space-x-1.5 transition-all cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isSearching ? 'Searching...' : 'Search'}</span>
          </button>
        </form>
      </div>

      {/* Main Layout: Record Insight Form + Table View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Add Memory Form */}
        <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-3.5 shadow-celestial border border-white/80 h-fit">
          <h3 className="font-bold text-sm text-slate-900 flex items-center space-x-2">
            <Plus className="w-4 h-4 text-indigo-600" />
            <span>Record New Insight</span>
          </h3>

          <form onSubmit={handleCreateMemory} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Insight / Principle / Lesson *
              </label>
              <textarea
                rows={4}
                required
                placeholder="Write an operating principle, rule of thumb, or key realization..."
                value={newMemoryText}
                onChange={(e) => setNewMemoryText(e.target.value)}
                className="w-full text-sm p-3 rounded-xl border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm resize-none font-sans"
              />
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Type
                </label>
                <select
                  value={newMemoryType}
                  onChange={(e) => setNewMemoryType(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-indigo-100 bg-white/90 text-slate-800 shadow-sm font-medium"
                >
                  <option value="insight">Insight</option>
                  <option value="principle">Principle</option>
                  <option value="lesson">Lesson</option>
                  <option value="identity">Identity</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Importance ({newMemoryImportance})
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={newMemoryImportance}
                  onChange={(e) => setNewMemoryImportance(parseFloat(e.target.value))}
                  className="w-full accent-indigo-600 mt-1.5 cursor-pointer"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded-full text-xs font-semibold shadow-sm transition-all cursor-pointer"
            >
              Save Memory
            </button>
          </form>
        </div>

        {/* Right: Table / List */}
        <div className="lg:col-span-2 space-y-3.5">
          {/* Controls Bar */}
          <div className="glass-panel rounded-2xl px-4 py-3 border border-white/80 shadow-celestial flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-sm text-slate-900">
                {searchResults ? `Search Results (${displayedList.length})` : `Saved Memories (${displayedList.length})`}
              </span>
              {searchResults && (
                <button
                  onClick={() => {
                    setSearchResults(null);
                    setSearchQuery('');
                  }}
                  className="text-xs text-indigo-600 hover:underline font-semibold ml-2 cursor-pointer"
                >
                  Clear Search
                </button>
              )}
            </div>

            {/* Type Filters & View Mode Toggles */}
            <div className="flex items-center space-x-2 flex-wrap gap-y-1">
              <div className="flex items-center bg-slate-100/90 rounded-lg p-0.5 text-xs">
                {(['all', 'insight', 'principle', 'lesson', 'identity'] as const).map((type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedType(type)}
                    className={`px-2.5 py-1 rounded-md capitalize font-medium transition-all cursor-pointer ${
                      selectedType === type
                        ? 'bg-white text-indigo-900 shadow-xs font-semibold'
                        : 'text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>

              {/* View Toggle */}
              <div className="flex items-center bg-slate-100/90 rounded-lg p-0.5">
                <button
                  onClick={() => setViewMode('table')}
                  title="Table View"
                  className={`p-1.5 rounded-md transition-all cursor-pointer ${
                    viewMode === 'table' ? 'bg-white text-indigo-600 shadow-xs' : 'text-slate-400 hover:text-slate-700'
                  }`}
                >
                  <TableIcon className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setViewMode('cards')}
                  title="Card View"
                  className={`p-1.5 rounded-md transition-all cursor-pointer ${
                    viewMode === 'cards' ? 'bg-white text-indigo-600 shadow-xs' : 'text-slate-400 hover:text-slate-700'
                  }`}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* Data Container */}
          {loading ? (
            <div className="glass-panel rounded-3xl p-8 animate-pulse text-center text-xs text-slate-400">
              Loading memories...
            </div>
          ) : displayedList.length === 0 ? (
            <div className="glass-panel rounded-3xl border border-dashed border-indigo-200 p-8 text-center text-xs text-slate-400">
              <Layers className="w-8 h-8 text-indigo-300 mx-auto mb-2 opacity-60" />
              <p className="font-medium text-slate-600">No memories found</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {searchResults ? 'Try a different search term or clear the filter.' : 'Record a new insight to get started.'}
              </p>
            </div>
          ) : viewMode === 'table' ? (
            /* Table View */
            <div className="glass-panel rounded-3xl shadow-celestial border border-white/80 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/90 border-b border-indigo-100/70 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                      <th className="py-3 px-4 w-12 text-center">#</th>
                      <th className="py-3 px-4">Memory / Insight</th>
                      <th className="py-3 px-3 w-28">Type</th>
                      <th className="py-3 px-3 w-28">Date</th>
                      <th className="py-3 px-3 w-28">Importance</th>
                      {searchResults && <th className="py-3 px-3 w-24">Match</th>}
                      <th className="py-3 px-3 w-14 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {displayedList.map((mem, idx) => (
                      <tr 
                        key={mem.id || idx}
                        className="hover:bg-indigo-50/40 transition-colors group"
                      >
                        {/* Index */}
                        <td className="py-3 px-4 text-center font-mono text-[11px] text-slate-400">
                          {idx + 1}
                        </td>

                        {/* Memory Text */}
                        <td className="py-3 px-4">
                          <p className="font-medium text-slate-800 leading-relaxed break-words line-clamp-3 group-hover:line-clamp-none transition-all">
                            {mem.text}
                          </p>
                        </td>

                        {/* Type */}
                        <td className="py-3 px-3 whitespace-nowrap">
                          {getTypeBadge(mem.memory_type)}
                        </td>

                        {/* Date */}
                        <td className="py-3 px-3 whitespace-nowrap text-slate-500 font-mono text-[11px]">
                          {mem.source_date ? (
                            <span className="flex items-center space-x-1">
                              <Calendar className="w-3 h-3 text-slate-400" />
                              <span>{mem.source_date}</span>
                            </span>
                          ) : (
                            <span className="text-slate-300">-</span>
                          )}
                        </td>

                        {/* Importance */}
                        <td className="py-3 px-3 whitespace-nowrap">
                          <div className="space-y-1">
                            <div className="flex items-center justify-between text-[10px] font-semibold text-slate-600">
                              <span>{(mem.importance ?? 0.8).toFixed(1)}</span>
                            </div>
                            <div className="w-20 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-gradient-to-r from-indigo-500 to-purple-600 h-full rounded-full"
                                style={{ width: `${Math.min(100, Math.max(0, (mem.importance ?? 0.8) * 100))}%` }}
                              />
                            </div>
                          </div>
                        </td>

                        {/* Match Score (if search active) */}
                        {searchResults && (
                          <td className="py-3 px-3 whitespace-nowrap">
                            {mem.score !== undefined ? (
                              <span className="inline-block text-[11px] font-mono font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-md border border-indigo-200">
                                {(mem.score * 100).toFixed(0)}%
                              </span>
                            ) : (
                              <span className="text-slate-300">-</span>
                            )}
                          </td>
                        )}

                        {/* Delete Action */}
                        <td className="py-3 px-3 text-center">
                          {mem.id ? (
                            <button
                              type="button"
                              onClick={() => handleDelete(mem.id)}
                              title="Delete Memory"
                              className="p-1.5 text-slate-300 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            /* Cards View */
            <div className="space-y-3">
              {displayedList.map((mem, idx) => (
                <div
                  key={mem.id || idx}
                  className="glass-card-interactive rounded-3xl p-4 space-y-2 border border-white/80 shadow-celestial"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-medium text-slate-900 leading-relaxed">{mem.text}</p>
                    {mem.id && (
                      <button
                        type="button"
                        onClick={() => handleDelete(mem.id)}
                        className="text-slate-300 hover:text-rose-500 transition-colors p-1 cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-indigo-50 font-normal">
                    <div className="flex items-center space-x-2">
                      {getTypeBadge(mem.memory_type)}
                      {mem.source_date && <span>Date: {mem.source_date}</span>}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span>Importance: {mem.importance}</span>
                      {mem.score !== undefined && (
                        <span className="text-[11px] font-mono font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-md border border-indigo-200">
                          Match: {(mem.score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

