import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Clock, 
  Sparkles, 
  Flame, 
  Layers, 
  Smartphone, 
  Download, 
  CheckCircle2, 
  RefreshCw,
  Archive,
  ArrowLeft
} from 'lucide-react';
import { PatchChangelogsSection } from '../components/PatchChangelogsSection';
import { AppCard } from '../components/AppCard';
import { FilterBar } from '../components/FilterBar';
import { ReleaseSelector } from '../components/ReleaseSelector';
import { formatTimeAgo, formatExactDate } from '../utils/dateUtils';

export function StorePage() {
  const [manifest, setManifest] = useState(null);
  const [patchChangelogs, setPatchChangelogs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentReleaseTag, setCurrentReleaseTag] = useState('latest');
  const [currentReleaseData, setCurrentReleaseData] = useState(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState('all');
  const [selectedArch, setSelectedArch] = useState('all');

  const isArchivedView = currentReleaseTag !== 'latest';

  // Load default/current release data
  useEffect(() => {
    loadReleaseData('latest');
  }, []);

  const loadReleaseData = async (tag) => {
    setLoading(true);
    setCurrentReleaseTag(tag);

    try {
      if (tag === 'latest') {
        // Load default static manifest and patch_changelogs
        const [manifestRes, changelogsRes] = await Promise.allSettled([
          fetch(`${import.meta.env.BASE_URL}manifest.json`).then(r => r.ok ? r.json() : null),
          fetch(`${import.meta.env.BASE_URL}patch_changelogs.json`).then(r => r.ok ? r.json() : null)
        ]);

        const mData = manifestRes.status === 'fulfilled' ? manifestRes.value : null;
        const cData = changelogsRes.status === 'fulfilled' ? changelogsRes.value : null;

        setManifest(mData);
        setPatchChangelogs(mData?.patch_changelogs || cData || {});
        setCurrentReleaseData(null);
      } else {
        // Fetch specific release from GitHub API
        const res = await fetch(`https://api.github.com/repos/yashrajrocxx/Mophe-AutoBuilds/releases/tags/${tag}`);
        if (res.ok) {
          const relData = await res.json();
          setCurrentReleaseData(relData);

          // Check if manifest.json asset exists in that release
          const manifestAsset = (relData.assets || []).find(a => a.name === 'manifest.json');
          if (manifestAsset && manifestAsset.browser_download_url) {
            try {
              const mRes = await fetch(manifestAsset.browser_download_url);
              if (mRes.ok) {
                const mData = await mRes.json();
                setManifest(mData);
                setPatchChangelogs(mData?.patch_changelogs || {});
                setLoading(false);
                return;
              }
            } catch (e) {
              console.warn("Could not load manifest from release asset:", e);
            }
          }

          // Fallback: construct entries from APK assets in the release
          const entriesMap = {};
          (relData.assets || []).forEach(asset => {
            const name = asset.name || "";
            if (!name.endsWith(".apk")) return;

            // Extract parts from name: {app}-{arch}-{source}-v{ver}.apk
            const parts = name.replace(/\.apk$/i, '').split('-');
            const app = parts[0] || 'app';
            let arch = 'universal';
            if (name.includes('arm64-v8a')) arch = 'arm64-v8a';
            else if (name.includes('armeabi-v7a')) arch = 'armeabi-v7a';
            else if (name.includes('x86_64')) arch = 'x86_64';
            else if (name.includes('x86')) arch = 'x86';

            const mkey = `${app}|auto|${arch}`;
            entriesMap[mkey] = {
              app_name: app,
              source: 'auto',
              arch: arch,
              apk: name,
              built_version: '',
              built_at: asset.updated_at || relData.published_at,
            };
          });

          setManifest({ entries: entriesMap, updated_at: relData.published_at });
          setPatchChangelogs({});
        }
      }
    } catch (err) {
      console.error("Failed to load release data:", err);
    } finally {
      setLoading(false);
    }
  };

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
      if (e.source && e.source !== 'auto') s.add(e.source.toLowerCase());
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
    const el = document.getElementById('apps-catalog-section');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSelectRelease = (rel) => {
    loadReleaseData(rel.tag_name || 'latest');
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-background min-h-[50vh]">
        <div className="flex flex-col items-center gap-3 yr-fade-up">
          <div className="w-8 h-8 rounded-full border-2 border-accent/20 border-t-accent animate-spin" />
          <p className="text-muted-foreground text-xs font-medium tracking-wide">Syncing release catalog...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-[1350px] mx-auto w-full yr-fade-up space-y-8">
      
      {/* 1. Header & Release History Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-border/50">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
              App Store
            </h2>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold tracking-wide uppercase border border-emerald-500/20">
              Active
            </span>
          </div>
          <p className="text-muted-foreground text-xs sm:text-sm max-w-lg">
            Verified, ad-free Android apps built automatically from community ReVanced toolchains.
          </p>
        </div>

        {/* Release Version Switcher Dropdown */}
        <div className="flex items-center gap-3 self-start sm:self-auto">
          <ReleaseSelector
            currentReleaseTag={currentReleaseTag}
            onSelectRelease={handleSelectRelease}
            isArchivedView={isArchivedView}
          />
        </div>
      </div>

      {/* Archived Release Notice Banner (if older release selected) */}
      {isArchivedView && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-600 dark:text-amber-400 yr-fade-up">
          <div className="flex items-center gap-2">
            <Archive size={15} className="shrink-0" />
            <span>
              Viewing archived release <strong>{currentReleaseTag}</strong> ({formatExactDate(manifest?.updated_at || currentReleaseData?.published_at)}).
            </span>
          </div>
          <button
            onClick={() => loadReleaseData('latest')}
            className="px-3 py-1 bg-amber-500 text-white rounded-lg font-semibold hover:bg-amber-600 transition-colors shrink-0 self-start sm:self-auto flex items-center gap-1.5"
          >
            <ArrowLeft size={12} />
            <span>Return to Latest</span>
          </button>
        </div>
      )}

      {/* 2. Top Section: What's New in Patches (Only if updated patch changelogs exist) */}
      <PatchChangelogsSection 
        patchChangelogs={patchChangelogs}
        onFilterByApp={handleFilterByApp}
      />

      {/* 3. Sleek Mobile-Friendly Filter & Search Bar */}
      <div id="apps-catalog-section" className="space-y-3">
        <FilterBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
          selectedArch={selectedArch}
          setSelectedArch={setSelectedArch}
          sources={sources}
          arches={arches}
          totalResults={filteredAppNames.length}
        />
      </div>

      {/* 4. Second Section: Recently Updated Apps (if any) */}
      {recentlyUpdatedApps.length > 0 && (
        <section className="space-y-3.5">
          <div className="flex items-center gap-2 text-sm sm:text-base font-bold text-foreground">
            <Flame size={16} className="text-accent" />
            <h3>Recently Updated</h3>
            <span className="px-1.5 py-0.2 rounded-full bg-accent/10 text-accent text-[10.5px] font-semibold">
              {recentlyUpdatedApps.length}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
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
      <section className="space-y-3.5">
        <div className="flex items-center gap-2 text-sm sm:text-base font-bold text-foreground">
          <Smartphone size={16} className="text-muted-foreground" />
          <h3>
            {recentlyUpdatedApps.length > 0 ? "All Other Apps" : "All Apps"}
          </h3>
          <span className="px-1.5 py-0.2 rounded-full bg-muted text-muted-foreground text-[10.5px] font-semibold">
            {otherApps.length}
          </span>
        </div>

        {otherApps.length === 0 && recentlyUpdatedApps.length === 0 ? (
          <div className="text-center p-10 bg-muted/10 border border-border/50 rounded-2xl">
            <Box className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
            <h4 className="text-sm font-medium mb-1 text-foreground">No matching apps found</h4>
            <p className="text-muted-foreground text-xs">Try adjusting your search query or filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
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
