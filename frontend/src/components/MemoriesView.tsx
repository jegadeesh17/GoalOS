import React, { useState, useEffect, useMemo } from 'react';
import { Memory, goalOSApi } from '../api/client';
import { PageHeader } from './PageHeader';
import { localDateStr, relativeDay, formatDate } from '../lib/date';
import {
  Search,
  Plus,
  Trash2,
  Table as TableIcon,
  LayoutGrid,
  Layers,
  Lightbulb,
  BookOpen,
  Award,
  Fingerprint
} from 'lucide-react';

const TYPE_STYLES: Record<string, { label: string; icon: typeof Lightbulb; tone: string }> = {
  principle: { label: 'Principle', icon: Award, tone: 'bg-amber-50 text-amber-900' },
  lesson: { label: 'Lesson', icon: BookOpen, tone: 'bg-emerald-50 text-emerald-900' },
  identity: { label: 'Identity', icon: Fingerprint, tone: 'bg-teal-50 text-teal-900' },
  insight: { label: 'Insight', icon: Lightbulb, tone: 'bg-emerald-50/70 text-forest-900' },
};

const TypeBadge: React.FC<{ type: string }> = ({ type }) => {
  const style = TYPE_STYLES[(type || 'insight').toLowerCase()] ?? TYPE_STYLES.insight;
  const Icon = style.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${style.tone}`}>
      <Icon className="w-3 h-3" />
      {style.label}
    </span>
  );
};

export const MemoriesView: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('cards');
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
        source_date: localDateStr(),
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

  const clearSearch = () => {
    setSearchResults(null);
    setSearchQuery('');
  };

  const displayedList = useMemo(() => {
    const rawList = searchResults !== null ? searchResults : memories;
    if (selectedType === 'all') return rawList;
    return rawList.filter((m) => (m.memory_type || '').toLowerCase() === selectedType.toLowerCase());
  }, [searchResults, memories, selectedType]);

  const deleteButton = (mem: Memory) =>
    mem.id ? (
      <button
        type="button"
        onClick={() => handleDelete(mem.id)}
        aria-label="Delete memory"
        className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition-colors cursor-pointer"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    ) : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Memories"
        subtitle="Lessons, principles and insights from your journals. The coach draws on these when it guides you."
      />

      <form onSubmit={handleSearch} className="flex gap-2" role="search">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="search"
            aria-label="Search memories"
            placeholder="Search your lessons, principles and breakthroughs…"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              if (!e.target.value.trim()) setSearchResults(null);
            }}
            className="w-full text-sm pl-11 pr-4 py-2.5 rounded-full border border-emerald-100 bg-white text-slate-900 placeholder:text-slate-500 shadow-forest-xs"
          />
        </div>
        <button
          type="submit"
          disabled={isSearching}
          className="bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white px-5 py-2.5 rounded-full text-xs font-semibold shadow-forest-xs transition-colors cursor-pointer"
        >
          {isSearching ? 'Searching…' : 'Search'}
        </button>
      </form>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Record a new memory */}
        <div className="glass-panel rounded-3xl p-6 sm:p-7 space-y-3.5 shadow-forest h-fit">
          <h2 className="font-bold text-sm text-slate-900 flex items-center gap-2">
            <Plus className="w-4 h-4 text-emerald-700" />
            Record something you learned
          </h2>

          <form onSubmit={handleCreateMemory} className="space-y-3">
            <div>
              <label htmlFor="memory-text" className="block text-xs font-semibold text-slate-700 mb-1">
                In your words
              </label>
              <textarea
                id="memory-text"
                rows={4}
                required
                placeholder="A principle, a rule of thumb, or something you realized…"
                value={newMemoryText}
                onChange={(e) => setNewMemoryText(e.target.value)}
                className="voice w-full text-base p-3 rounded-xl border border-emerald-100 bg-white resize-none placeholder:text-slate-500 placeholder:italic"
              />
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label htmlFor="memory-type" className="block text-xs font-semibold text-slate-700 mb-1">
                  Type
                </label>
                <select
                  id="memory-type"
                  value={newMemoryType}
                  onChange={(e) => setNewMemoryType(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-emerald-100 bg-white text-slate-800 font-medium"
                >
                  <option value="insight">Insight</option>
                  <option value="principle">Principle</option>
                  <option value="lesson">Lesson</option>
                  <option value="identity">Identity</option>
                </select>
              </div>

              <div>
                <label htmlFor="memory-importance" className="block text-xs font-semibold text-slate-700 mb-1">
                  Importance ({newMemoryImportance})
                </label>
                <input
                  id="memory-importance"
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={newMemoryImportance}
                  onChange={(e) => setNewMemoryImportance(parseFloat(e.target.value))}
                  className="w-full accent-emerald-700 mt-1.5 cursor-pointer"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-emerald-700 hover:bg-emerald-800 text-white py-2.5 rounded-full text-xs font-semibold shadow-forest-xs transition-colors cursor-pointer"
            >
              Save memory
            </button>
          </form>
        </div>

        {/* Saved memories */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 px-1">
            <div className="flex items-center gap-3">
              <h2 className="font-bold text-sm text-slate-900">
                {searchResults ? 'Search results' : 'Saved memories'}{' '}
                <span className="font-medium text-slate-500 tabular-nums">· {displayedList.length}</span>
              </h2>
              {searchResults && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="text-xs text-emerald-800 hover:text-emerald-950 font-semibold cursor-pointer"
                >
                  Clear search
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center bg-slate-100/90 rounded-full p-0.5 text-xs" role="group" aria-label="Filter by type">
                {(['all', 'insight', 'principle', 'lesson', 'identity'] as const).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setSelectedType(type)}
                    aria-pressed={selectedType === type}
                    className={`px-2.5 py-1 rounded-full capitalize transition-colors cursor-pointer ${
                      selectedType === type ? 'bg-white text-emerald-950 font-semibold shadow-forest-xs' : 'text-slate-600 font-medium hover:text-slate-900'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>

              <div className="flex items-center bg-slate-100/90 rounded-full p-0.5" role="group" aria-label="Layout">
                <button
                  type="button"
                  onClick={() => setViewMode('cards')}
                  aria-label="Card view"
                  aria-pressed={viewMode === 'cards'}
                  className={`p-1.5 rounded-full transition-colors cursor-pointer ${
                    viewMode === 'cards' ? 'bg-white text-emerald-800 shadow-forest-xs' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('table')}
                  aria-label="Table view"
                  aria-pressed={viewMode === 'table'}
                  className={`p-1.5 rounded-full transition-colors cursor-pointer ${
                    viewMode === 'table' ? 'bg-white text-emerald-800 shadow-forest-xs' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <TableIcon className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 motion-safe:animate-pulse" aria-hidden="true">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="h-36 bg-white/60 rounded-3xl" />
              ))}
            </div>
          ) : displayedList.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-emerald-200 p-10 text-center">
              <Layers className="w-8 h-8 text-emerald-300 mx-auto mb-2" />
              <p className="voice text-lg">Nothing here yet.</p>
              <p className="text-xs text-slate-600 mt-1">
                {searchResults ? 'Try other words, or clear the search.' : 'Record something you learned to start your memory bank.'}
              </p>
            </div>
          ) : viewMode === 'cards' ? (
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {displayedList.map((mem, idx) => (
                <li key={mem.id || idx} className="glass-panel rounded-3xl p-5 flex flex-col gap-4 shadow-forest group">
                  <blockquote className="voice text-[16.5px] flex-1">{mem.text}</blockquote>
                  <div className="flex items-center justify-between gap-2 text-xs text-slate-500">
                    <div className="flex flex-wrap items-center gap-2">
                      <TypeBadge type={mem.memory_type} />
                      {mem.source_date && (
                        <time dateTime={mem.source_date} title={formatDate(mem.source_date, { month: 'long', day: 'numeric', year: 'numeric' })}>
                          {relativeDay(mem.source_date)}
                        </time>
                      )}
                      {mem.score !== undefined && (
                        <span className="font-semibold text-emerald-800 tabular-nums">{(mem.score * 100).toFixed(0)}% match</span>
                      )}
                    </div>
                    <span className="opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 [@media(hover:none)]:opacity-100 transition-opacity">
                      {deleteButton(mem)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="glass-panel rounded-3xl shadow-forest overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/90 border-b border-emerald-100 text-xs font-semibold text-slate-600">
                      <th className="py-3 px-4">Memory</th>
                      <th className="py-3 px-3 w-28">Type</th>
                      <th className="py-3 px-3 w-28">Date</th>
                      <th className="py-3 px-3 w-24">Importance</th>
                      {searchResults && <th className="py-3 px-3 w-20">Match</th>}
                      <th className="py-3 px-3 w-12"><span className="sr-only">Actions</span></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {displayedList.map((mem, idx) => (
                      <tr key={mem.id || idx} className="hover:bg-emerald-50/40 transition-colors align-top">
                        <td className="py-3 px-4">
                          <p className="text-slate-800 leading-relaxed break-words">{mem.text}</p>
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          <TypeBadge type={mem.memory_type} />
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap text-xs text-slate-600 tabular-nums">
                          {mem.source_date || '–'}
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap text-xs text-slate-600 tabular-nums">
                          {(mem.importance ?? 0.8).toFixed(1)}
                        </td>
                        {searchResults && (
                          <td className="py-3 px-3 whitespace-nowrap text-xs font-semibold text-emerald-800 tabular-nums">
                            {mem.score !== undefined ? `${(mem.score * 100).toFixed(0)}%` : '–'}
                          </td>
                        )}
                        <td className="py-2 px-3 text-center">{deleteButton(mem)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
