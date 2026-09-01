import React from 'react';
import { Search, Filter, Cpu, X, Sparkles } from 'lucide-react';

export function FilterBar({
  searchQuery,
  setSearchQuery,
  selectedSource,
  setSelectedSource,
  selectedArch,
  setSelectedArch,
  sources,
  arches,
  totalResults
}) {
  const getSourceLabel = (src) => {
    if (!src || src === 'all') return 'All Sources';
    const map = {
      morphe: 'Morphe',
      piko: 'Piko',
      'piko-dev': 'Piko (Dev)',
      paresh: 'Paresh',
      durgesh: 'Durgesh',
      rookie: 'Rookie',
      rushiranpise: 'Rushi',
      browzomje: 'Browzomje',
      dh6k: 'dh6k'
    };
    return map[src.toLowerCase()] || src.charAt(0).toUpperCase() + src.slice(1);
  };

  const getArchLabel = (arch) => {
    if (!arch || arch === 'all') return 'All Arch';
    return arch.toUpperCase();
  };

  return (
    <div className="bg-card/70 backdrop-blur-md rounded-2xl border border-border/70 p-3 sm:p-4 shadow-2xs space-y-3">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
        
        {/* Search Input */}
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60" />
          <input
            type="text"
            placeholder="Search apps (e.g. YouTube, Instagram, X)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-2 bg-background/90 border border-border/60 rounded-xl text-xs sm:text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
              aria-label="Clear search"
            >
              <X size={13} />
            </button>
          )}
        </div>

        {/* Filter Controls Row (Compact side-by-side dropdowns) */}
        <div className="grid grid-cols-2 sm:flex sm:items-center gap-2">
          
          {/* Source Dropdown */}
          <div className="relative">
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full sm:w-auto appearance-none pl-8 pr-7 py-2 bg-background/90 border border-border/60 hover:border-accent/40 rounded-xl text-xs font-semibold text-foreground focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent cursor-pointer transition-all shadow-2xs"
            >
              <option value="all">All Sources</option>
              {sources.map(src => (
                <option key={src} value={src}>
                  {getSourceLabel(src)}
                </option>
              ))}
            </select>
            <Filter size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-accent pointer-events-none" />
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none text-[10px]">
              ▼
            </div>
          </div>

          {/* Arch Dropdown */}
          <div className="relative">
            <select
              value={selectedArch}
              onChange={(e) => setSelectedArch(e.target.value)}
              className="w-full sm:w-auto appearance-none pl-8 pr-7 py-2 bg-background/90 border border-border/60 hover:border-accent/40 rounded-xl text-xs font-semibold text-foreground focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent cursor-pointer transition-all shadow-2xs uppercase"
            >
              <option value="all">All Arch</option>
              {arches.map(arch => (
                <option key={arch} value={arch}>
                  {getArchLabel(arch)}
                </option>
              ))}
            </select>
            <Cpu size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-accent pointer-events-none" />
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none text-[10px]">
              ▼
            </div>
          </div>

        </div>

      </div>

      {/* Active Filter Indicators (if any filter is applied) */}
      {(searchQuery || selectedSource !== 'all' || selectedArch !== 'all') && (
        <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px] text-muted-foreground">
          <span>Filters:</span>
          {searchQuery && (
            <span className="px-2 py-0.5 rounded-md bg-accent/10 text-accent font-medium flex items-center gap-1">
              "{searchQuery}"
              <button onClick={() => setSearchQuery('')} className="hover:text-foreground">✕</button>
            </span>
          )}
          {selectedSource !== 'all' && (
            <span className="px-2 py-0.5 rounded-md bg-accent/10 text-accent font-medium flex items-center gap-1">
              Source: {getSourceLabel(selectedSource)}
              <button onClick={() => setSelectedSource('all')} className="hover:text-foreground">✕</button>
            </span>
          )}
          {selectedArch !== 'all' && (
            <span className="px-2 py-0.5 rounded-md bg-accent/10 text-accent font-medium flex items-center gap-1">
              Arch: {getArchLabel(selectedArch)}
              <button onClick={() => setSelectedArch('all')} className="hover:text-foreground">✕</button>
            </span>
          )}
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedSource('all');
              setSelectedArch('all');
            }}
            className="text-xs text-muted-foreground hover:text-accent underline ml-auto"
          >
            Reset filters
          </button>
        </div>
      )}
    </div>
  );
}
