import React from 'react';
import { Search, X, ChevronDown } from 'lucide-react';

export function FilterBar({
  searchQuery,
  setSearchQuery,
  selectedSource,
  setSelectedSource,
  sources,
  totalResults
}) {
  const getSourceLabel = (src) => {
    if (!src || src === 'all') return 'All sources';
    const map = {
      morphe: 'Morphe',
      'piko-newx': 'Piko NewX',
      paresh: 'Paresh',
      rookie: 'Rookie',
      rushiranpise: 'Rushi',
      hushgram: 'HushGram',
      hushpinterest: 'HushPinterest',
      hushtelegram: 'HushTelegram',
      hushthreads: 'HushThreads',
      jasonwu: 'Jasonwu (Gboard)',
      kveld9: 'kveld9',
      hoodles: 'Hoodles',
      heval99: 'Heval99 (Brave)',
      venus: 'Venus (Discord)',
      noam: 'Noam (Chess.com)',
    };
    return map[src.toLowerCase()] || src.charAt(0).toUpperCase() + src.slice(1);
  };

  const hasFilters = searchQuery || selectedSource !== 'all';

  const selectClass =
    'w-full sm:w-auto appearance-none h-10 pl-3 pr-8 bg-background border border-border rounded-lg text-[13px] font-medium focus:outline-none focus:border-foreground cursor-pointer transition-colors';

  return (
    <div className="bg-card rounded-xl border border-border p-3 space-y-3">
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            placeholder="Search apps…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-10 pl-9 pr-9 bg-background border border-border rounded-lg text-sm placeholder:text-muted-foreground focus:outline-none focus:border-foreground transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="Clear search"
            >
              <X size={14} />
            </button>
          )}
        </div>

        <div className="relative">
          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className={selectClass}
            aria-label="Filter by patch source"
          >
            <option value="all">All sources</option>
            {sources.map(src => (
              <option key={src} value={src}>
                {getSourceLabel(src)}
              </option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {totalResults} {totalResults === 1 ? 'app' : 'apps'}
          {hasFilters && ' matching filters'}
        </span>
        {hasFilters && (
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedSource('all');
            }}
            className="font-medium text-foreground underline underline-offset-2 hover:opacity-70 transition-opacity"
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
