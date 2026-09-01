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
  RefreshCw
} from 'lucide-react';
import { PatchChangelogsSection } from '../components/PatchChangelogsSection';
import { AppCard } from '../components/AppCard';

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
      <div className="w-full h-full flex items-center justify-center bg-background/50 backdrop-blur-sm">
        <div className="flex flex-col items-center gap-4 yr-fade-up">
          <div className="w-10 h-10 rounded-full border-2 border-accent/20 border-t-accent animate-spin" />
          <p className="text-muted-foreground text-sm font-medium tracking-wide">Syncing app library and patch notes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-12 max-w-[1500px] mx-auto w-full yr-fade-up space-y-12">
      
      {/* 1. Header & Quick Stats */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 pb-6 border-b border-border/40">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-4xl font-extrabold tracking-tight text-foreground">
              Morphe App Store
            </h2>
            <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold tracking-wide">
              PIPELINE ONLINE
            </span>
          </div>
          <p className="text-muted-foreground text-[15px] max-w-2xl leading-relaxed">
            Download verified, ad-free, and patched Android apps directly compiled from upstream ReVanced and Morphe repositories.
          </p>
        </div>

        {/* Sync Info Badges */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2.5 text-xs text-muted-foreground bg-muted/40 px-4 py-2 rounded-xl border border-border/50">
            <Box size={14} className="text-accent" />
            <span className="font-semibold text-foreground">{Object.keys(groupedApps).length} Apps</span>
          </div>
          <div className="flex items-center gap-2.5 text-xs text-muted-foreground bg-muted/40 px-4 py-2 rounded-xl border border-border/50">
            <Layers size={14} className="text-accent" />
            <span className="font-semibold text-foreground">{entries.length} Builds</span>
          </div>
          <div className="flex items-center gap-2.5 text-xs text-muted-foreground bg-muted/40 px-4 py-2 rounded-xl border border-border/50">
            <Clock size={14} className="text-accent" />
            <span>Updated {manifest?.updated_at ? new Date(manifest.updated_at).toLocaleDateString() : 'Recently'}</span>
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
      <div id="apps-catalog-section" className="space-y-4 pt-4">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          
          {/* Search Bar */}
          <div className="relative flex-1 max-w-md">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60" />
            <input
              type="text"
              placeholder="Search apps by name, package..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-card/60 border border-border/60 rounded-xl text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all shadow-xs"
            />
            {searchQuery && (
              <button 
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground p-1"
              >
                Clear
              </button>
            )}
          </div>

          {/* Architecture Filter Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
            <button
              onClick={() => setSelectedArch('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${
                selectedArch === 'all' 
                  ? 'bg-accent text-accent-foreground shadow-sm' 
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
                    ? 'bg-accent text-accent-foreground shadow-sm' 
                    : 'bg-muted/40 hover:bg-muted text-muted-foreground'
                }`}
              >
                {arch}
              </button>
            ))}
          </div>
        </div>

        {/* Source Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 text-xs">
          <span className="text-muted-foreground/70 font-semibold uppercase tracking-wider text-[11px] mr-1 flex items-center gap-1">
            <Filter size={12} />
            Source:
          </span>
          <button
            onClick={() => setSelectedSource('all')}
            className={`px-3 py-1 rounded-lg font-medium transition-colors ${
              selectedSource === 'all' 
                ? 'bg-foreground text-background font-semibold shadow-xs' 
                : 'bg-card/60 hover:bg-muted text-muted-foreground border border-border/50'
            }`}
          >
            All Sources
          </button>
          {sources.map(src => (
            <button
              key={src}
              onClick={() => setSelectedSource(src)}
              className={`px-3 py-1 rounded-lg font-medium capitalize transition-colors ${
                selectedSource === src 
                  ? 'bg-foreground text-background font-semibold shadow-xs' 
                  : 'bg-card/60 hover:bg-muted text-muted-foreground border border-border/50'
              }`}
            >
              {src}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Second Section: Recently Updated Apps (if any) */}
      {recentlyUpdatedApps.length > 0 && (
        <section className="space-y-5">
          <div className="flex items-center gap-2.5 text-xl font-bold text-foreground">
            <div className="w-7 h-7 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
              <Flame size={18} className="animate-bounce" />
            </div>
            <h3>Recently Updated Apps</h3>
            <span className="px-2 py-0.5 rounded-full bg-accent/10 text-accent text-xs font-semibold">
              {recentlyUpdatedApps.length}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
      <section className="space-y-5">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 text-xl font-bold text-foreground">
            <div className="w-7 h-7 rounded-lg bg-muted text-muted-foreground flex items-center justify-center">
              <Smartphone size={18} />
            </div>
            <h3>
              {recentlyUpdatedApps.length > 0 ? "All Other Apps" : "All Apps"}
            </h3>
            <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-xs font-semibold">
              {otherApps.length}
            </span>
          </div>
        </div>

        {otherApps.length === 0 && recentlyUpdatedApps.length === 0 ? (
          <div className="text-center p-16 bg-muted/10 border border-border/50 rounded-3xl backdrop-blur-md">
            <Box className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
            <h4 className="text-lg font-medium mb-1 text-foreground">No matching apps found</h4>
            <p className="text-muted-foreground text-sm">Try adjusting your search query or source/architecture filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
