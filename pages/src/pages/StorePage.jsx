import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Clock, 
  Search, 
  Sparkles, 
  Flame, 
  Layers, 
  Filter, 
  Smartphone, 
  Download, 
  CheckCircle2, 
  ExternalLink,
  RefreshCw,
  Zap
} from 'lucide-react';
import { PatchChangelogsSection } from '../components/PatchChangelogsSection';
import { AppCard } from '../components/AppCard';
import { formatTimeAgo } from '../utils/dateUtils';

export function StorePage() {
  const [manifest, setManifest] = useState(null);
  const [patchChangelogs, setPatchChangelogs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState('all');
  const [selectedArch, setSelectedArch] = useState('all');

  useEffect(() => {
    // Fetch manifest.json and patch_changelogs.json concurrently
    Promise.allSettled([
      fetch(`${import.meta.env.BASE_URL}manifest.json`).then(r => r.ok ? r.json() : null),
      fetch(`${import.meta.env.BASE_URL}patch_changelogs.json`).then(r => r.ok ? r.json() : null)
    ]).then(([manifestRes, changelogsRes]) => {
      const manifestData = manifestRes.status === 'fulfilled' ? manifestRes.value : null;
      const changelogsData = changelogsRes.status === 'fulfilled' ? changelogsRes.value : null;

      setManifest(manifestData);
      // Prefer embedded patch_changelogs in manifest if present, otherwise external file
      setPatchChangelogs(manifestData?.patch_changelogs || changelogsData || {});
      setLoading(false);
    }).catch(err => {
      console.error("Failed to load catalog data:", err);
      setLoading(false);
    });
  }, []);

  const entries = useMemo(() => {
    if (!manifest?.entries) return [];
    return Object.values(manifest.entries);
  }, [manifest]);

  // Group entries by app_name
  const groupedApps = useMemo(() => {
    return entries.reduce((acc, entry) => {
      if (!acc[entry.app_name]) {
        acc[entry.app_name] = [];
      }
      acc[entry.app_name].push(entry);
      return acc;
    }, {});
  }, [entries]);

  // Collect all affected apps from updated patch changelogs
  const updatedAppNames = useMemo(() => {
    const set = new Set();
    if (patchChangelogs) {
      Object.values(patchChangelogs).forEach(src => {
        (src.affected_apps || []).forEach(a => set.add(a.toLowerCase()));
      });
    }
    return set;
  }, [patchChangelogs]);

  // Determine unique sources and arches for filter chips
  const sources = useMemo(() => {
    const s = new Set();
    entries.forEach(e => {
      if (e.source) s.add(e.source.toLowerCase());
    });
    return Array.from(s);
  }, [entries]);

  const arches = useMemo(() => {
    const a = new Set();
    entries.forEach(e => {
      if (e.arch) a.add(e.arch.toLowerCase());
    });
    return Array.from(a);
  }, [entries]);

  // Filtered Apps
  const filteredAppNames = useMemo(() => {
    return Object.keys(groupedApps).filter(appName => {
      const appEntries = groupedApps[appName];
      const firstEntry = appEntries[0] || {};
      
      // Search query filter (matches app name or package)
      const matchesSearch = !searchQuery || 
        appName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (firstEntry.package || '').toLowerCase().includes(searchQuery.toLowerCase());

      // Source filter
      const matchesSource = selectedSource === 'all' || 
        (firstEntry.source || '').toLowerCase() === selectedSource.toLowerCase();

      // Arch filter
      const matchesArch = selectedArch === 'all' ||
        appEntries.some(e => (e.arch || '').toLowerCase() === selectedArch.toLowerCase());

      return matchesSearch && matchesSource && matchesArch;
    });
  }, [groupedApps, searchQuery, selectedSource, selectedArch]);

  // Split filtered apps into Recently Updated vs All Other Apps
  const { recentlyUpdatedApps, otherApps } = useMemo(() => {
    const recent = [];
    const others = [];

    filteredAppNames.forEach(appName => {
      if (updatedAppNames.has(appName.toLowerCase())) {
        recent.push(appName);
      } else {
        others.push(appName);
      }
    });

    return { recentlyUpdatedApps: recent, otherApps: others };
  }, [filteredAppNames, updatedAppNames]);

  const handleFilterByApp = (appName) => {
    setSearchQuery(appName);
    // Smooth scroll down to apps section
    const el = document.getElementById('apps-catalog-section');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const handleFilterBySource = (sourceName) => {
    setSelectedSource(sourceName.toLowerCase());
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 yr-fade-up">
          <div className="w-9 h-9 rounded-full border-2 border-accent/20 border-t-accent animate-spin" />
          <p className="text-muted-foreground text-xs font-medium tracking-wide">Loading catalog...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-10 max-w-[1400px] mx-auto w-full yr-fade-up space-y-10">
      
      {/* 1. Header & Minimal Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border/40">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
              App Store
            </h2>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-[11px] font-bold tracking-wider uppercase border border-emerald-500/20">
              Active
            </span>
          </div>
          <p className="text-muted-foreground text-sm max-w-xl">
            Custom patched, ad-free Android apps built automatically from community ReVanced toolchains.
          </p>
        </div>

        {/* Sync Info Badges */}
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-2 text-muted-foreground bg-muted/40 px-3.5 py-1.5 rounded-xl border border-border/50">
            <Layers size={13} className="text-accent" />
            <span className="font-semibold text-foreground">{Object.keys(groupedApps).length} Apps</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground bg-muted/40 px-3.5 py-1.5 rounded-xl border border-border/50">
            <Clock size={13} className="text-accent" />
            <span>Updated {formatTimeAgo(manifest?.updated_at)}</span>
          </div>
        </div>
      </div>

      {/* 2. Top Section: What's New in Patches (Only if updated patch changelogs exist) */}
      <PatchChangelogsSection 
        patchChangelogs={patchChangelogs}
        onFilterByApp={handleFilterByApp}
        onFilterBySource={handleFilterBySource}
      />

      {/* 3. Search & Filter Bar */}
      <div id="apps-catalog-section" className="space-y-3 pt-2">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          
          {/* Minimal Search Bar */}
          <div className="relative flex-1 max-w-sm">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60" />
            <input
              type="text"
              placeholder="Search apps or package..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 bg-card/60 border border-border/60 rounded-xl text-xs placeholder:text-muted-foreground/50 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
            />
            {searchQuery && (
              <button 
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[11px] text-muted-foreground hover:text-foreground"
              >
                ✕
              </button>
            )}
          </div>

          {/* Architecture Filter Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            <button
              onClick={() => setSelectedArch('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-colors ${
                selectedArch === 'all' 
                  ? 'bg-foreground text-background shadow-2xs' 
                  : 'bg-muted/40 hover:bg-muted text-muted-foreground'
              }`}
            >
              All Arch
            </button>
            {arches.map(arch => (
              <button
                key={arch}
                onClick={() => setSelectedArch(arch)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${
                  selectedArch === arch 
                    ? 'bg-foreground text-background shadow-2xs' 
                    : 'bg-muted/40 hover:bg-muted text-muted-foreground'
                }`}
              >
                {arch}
              </button>
            ))}
          </div>
        </div>

        {/* Source Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          <span className="text-muted-foreground/60 font-semibold uppercase tracking-wider text-[10px] mr-1">
            Source:
          </span>
          <button
            onClick={() => setSelectedSource('all')}
            className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
              selectedSource === 'all' 
                ? 'bg-accent/15 text-accent font-semibold border border-accent/30' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
            }`}
          >
            All
          </button>
          {sources.map(src => (
            <button
              key={src}
              onClick={() => setSelectedSource(src)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium capitalize transition-colors ${
                selectedSource === src 
                  ? 'bg-accent/15 text-accent font-semibold border border-accent/30' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
              }`}
            >
              {src}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Second Section: Recently Updated Apps (if any) */}
      {recentlyUpdatedApps.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-base font-bold text-foreground">
            <Flame size={17} className="text-accent" />
            <h3>Recently Updated</h3>
            <span className="px-2 py-0.5 rounded-full bg-accent/10 text-accent text-[11px] font-semibold">
              {recentlyUpdatedApps.length}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {recentlyUpdatedApps.map(appName => (
              <AppCard
                key={appName}
                appName={appName}
                appEntries={groupedApps[appName]}
                isRecentlyUpdated={true}
                manifestUpdatedAt={manifest?.updated_at}
              />
            ))}
          </div>
        </section>
      )}

      {/* 5. Third Section: All Other Apps Catalog */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 text-base font-bold text-foreground">
          <Smartphone size={17} className="text-muted-foreground" />
          <h3>
            {recentlyUpdatedApps.length > 0 ? "All Other Apps" : "All Apps"}
          </h3>
          <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-[11px] font-semibold">
            {otherApps.length}
          </span>
        </div>

        {otherApps.length === 0 && recentlyUpdatedApps.length === 0 ? (
          <div className="text-center p-12 bg-muted/10 border border-border/50 rounded-2xl">
            <Box className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
            <h4 className="text-base font-medium mb-1 text-foreground">No matching apps found</h4>
            <p className="text-muted-foreground text-xs">Try adjusting your search query or filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {otherApps.map(appName => (
              <AppCard
                key={appName}
                appName={appName}
                appEntries={groupedApps[appName]}
                isRecentlyUpdated={false}
                manifestUpdatedAt={manifest?.updated_at}
              />
            ))}
          </div>
        )}
      </section>

    </div>
  );
}
