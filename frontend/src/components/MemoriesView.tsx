import React, { useState, useEffect } from 'react';
import { Memory, goalOSApi } from '../api/client';
import { 
  Search, 
  Plus, 
  Trash2, 
  Sparkles,
  Brain
} from 'lucide-react';

export const MemoriesView: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [newMemoryText, setNewMemoryText] = useState('');
  const [newMemoryType, setNewMemoryType] = useState('insight');
  const [newMemoryImportance, setNewMemoryImportance] = useState(0.8);

  const loadMemories = async () => {
    try {
      setLoading(true);
      const list = await goalOSApi.listMemories(50);
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
      const results = await goalOSApi.searchMemories(searchQuery.trim(), 10);
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
              className="w-full text-xs pl-10 pr-3.5 py-2.5 rounded-full border border-indigo-100 focus:ring-2 focus:ring-indigo-500 bg-white/90 shadow-sm"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-full text-xs font-semibold shadow-sm flex items-center space-x-1.5 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isSearching ? 'Searching...' : 'Search'}</span>
          </button>
        </form>
      </div>

      {/* Main Grid: Store Memory Form + List / Search Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Add Memory Form */}
        <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-3.5 shadow-celestial border border-white/80">
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
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded-full text-xs font-semibold shadow-sm transition-all"
            >
              Save Memory
            </button>
          </form>
        </div>

        {/* Right: Search Results or All Memories */}
        <div className="lg:col-span-2 space-y-3.5">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-slate-900">
              {searchResults ? `Search Results (${searchResults.length})` : `Saved Memories (${memories.length})`}
            </h3>
            {searchResults && (
              <button
                onClick={() => {
                  setSearchResults(null);
                  setSearchQuery('');
                }}
                className="text-xs text-indigo-600 hover:underline font-semibold"
              >
                Clear Search
              </button>
            )}
          </div>

          <div className="space-y-3">
            {loading ? (
              <div className="glass-panel rounded-3xl p-6 animate-pulse text-center text-xs text-slate-400">
                Loading memories...
              </div>
            ) : searchResults ? (
              searchResults.length === 0 ? (
                <div className="glass-panel rounded-3xl border border-dashed border-indigo-200 p-6 text-center text-xs text-slate-400 font-normal">
                  No memories matched this query.
                </div>
              ) : (
                searchResults.map((res, idx) => (
                  <div
                    key={res.id || idx}
                    className="glass-card-interactive rounded-3xl p-4 space-y-2 border border-white/80 shadow-celestial"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-medium text-slate-900 leading-relaxed">{res.text}</p>
                      {res.score !== undefined && (
                        <span className="text-xs font-mono font-bold bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 px-2 py-0.5 rounded-md border border-indigo-200 flex-shrink-0">
                          Match: {(res.score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>

                    <div className="flex items-center space-x-3 text-xs text-slate-500 pt-1.5 border-t border-indigo-50 font-normal">
                      <span className="capitalize font-medium text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md">{res.memory_type}</span>
                      {res.source_date && <span>Date: {res.source_date}</span>}
                      {res.importance !== undefined && <span>Importance: {res.importance}</span>}
                    </div>
                  </div>
                ))
              )
            ) : memories.length === 0 ? (
              <div className="glass-panel rounded-3xl border border-dashed border-indigo-200 p-6 text-center text-xs text-slate-400 font-normal">
                No memories recorded yet.
              </div>
            ) : (
              memories.map((mem) => (
                <div
                  key={mem.id}
                  className="glass-card-interactive rounded-3xl p-4 space-y-2 border border-white/80 shadow-celestial"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-medium text-slate-900 leading-relaxed">{mem.text}</p>
                    <button
                      type="button"
                      onClick={() => handleDelete(mem.id)}
                      className="text-slate-300 hover:text-rose-500 transition-colors p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="flex items-center space-x-3 text-xs text-slate-500 pt-1.5 border-t border-indigo-50 font-normal">
                    <span className="text-xs font-medium bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-md border border-indigo-100">
                      {mem.memory_type}
                    </span>
                    {mem.source_date && <span>Date: {mem.source_date}</span>}
                    <span>Importance: {mem.importance}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
