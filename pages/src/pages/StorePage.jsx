import React, { useState, useEffect, useMemo } from 'react';
import {
  PackageSearch,
  Clock,
  Flame,
  Smartphone,
  Download,
  Copy,
  Check,
  X,
  Layers
} from 'lucide-react';
import { PatchChangelogsSection } from '../components/PatchChangelogsSection';
import { AppCard } from '../components/AppCard';
import { FilterBar } from '../components/FilterBar';
import { formatTimeAgo } from '../utils/dateUtils';
import { getAppMeta } from '../utils/appMeta';

const BULK_URL = 'https://raw.githubusercontent.com/yashrajrocxx/Mophe-AutoBuilds/main/obtainium.json';

export function StorePage() {
  const [manifest, setManifest] = useState(null);
  const [patchConfig, setPatchConfig] = useState(null);
  const [patchChangelogs, setPatchChangelogs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showObtainiumModal, setShowObtainiumModal] = useState(false);
  const [copied, setCopied] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    Promise.allSettled([
      fetch(`${import.meta.env.BASE_URL}manifest.json`).then(r => r.ok ? r.json() : null),
      fetch(`${import.meta.env.BASE_URL}patch_changelogs.json`).then(r => r.ok ? r.json() : null),
      fetch(`${import.meta.env.BASE_URL}patch-config.json`).then(r => r.ok ? r.json() : null)
    ]).then(([manifestRes, changelogsRes, patchConfigRes]) => {
      const manifestData = manifestRes.status === 'fulfilled' ? manifestRes.value : null;
      const changelogsData = changelogsRes.status === 'fulfilled' ? changelogsRes.value : null;
      const patchConfigData = patchConfigRes.status === 'fulfilled' ? patchConfigRes.value : null;

      setManifest(manifestData);
      setPatchChangelogs(manifestData?.patch_changelogs || changelogsData || {});
      setPatchConfig(patchConfigData);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const entries = useMemo(() => {
    if (!manifest?.entries) return [];
    return Object.values(manifest.entries);
  }, [manifest]);

  const groupedApps = useMemo(() => {
    const acc = {};
    // First, populate entries from manifest
    entries.forEach(entry => {
      if (!acc[entry.app_name]) acc[entry.app_name] = [];
      acc[entry.app_name].push(entry);
    });

    // Also ensure all apps in patch-config.json are listed (even if pending first build)
    if (patchConfig?.patch_list && Array.isArray(patchConfig.patch_list)) {
      patchConfig.patch_list.forEach(item => {
        const name = item.app_name;
        if (!name) return;
        if (!acc[name] || acc[name].length === 0) {
          const meta = getAppMeta(name);
          acc[name] = [{
            app_name: name,
            source: item.source || 'morphe',
            package: meta.package || '',
            apk: null,
            built_version: null,
            built_at: null,
          }];
        }
      });
    }

    return acc;
  }, [entries, patchConfig]);

  const updatedAppNames = useMemo(() => {
    const set = new Set();
    if (patchChangelogs) {
      Object.values(patchChangelogs).forEach(src => {
        (src.affected_apps || []).forEach(a => set.add(a.toLowerCase()));
      });
    }
    return set;
  }, [patchChangelogs]);

  const sources = useMemo(() => {
    const s = new Set();
    Object.values(groupedApps).forEach(appEntries => {
      appEntries.forEach(e => {
        if (e.source) s.add(e.source.toLowerCase());
      });
    });
    return Array.from(s).sort();
  }, [groupedApps]);

  const categories = useMemo(() => {
    const c = new Set();
    Object.keys(groupedApps).forEach(appName => {
      const meta = getAppMeta(appName);
      if (meta?.category) c.add(meta.category);
    });
    return Array.from(c).sort();
  }, [groupedApps]);

  const filteredAppNames = useMemo(() => {
    return Object.keys(groupedApps).filter(appName => {
      const appEntries = groupedApps[appName];
      const firstEntry = appEntries[0] || {};
      const meta = getAppMeta(appName);

      const matchesSearch = !searchQuery ||
        appName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        meta.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (firstEntry.package || '').toLowerCase().includes(searchQuery.toLowerCase());

      const matchesSource = selectedSource === 'all' ||
        (firstEntry.source || '').toLowerCase() === selectedSource.toLowerCase();

      const matchesCategory = selectedCategory === 'all' ||
        meta.category === selectedCategory;

      return matchesSearch && matchesSource && matchesCategory;
    });
  }, [groupedApps, searchQuery, selectedSource, selectedCategory]);

  const { recentlyUpdatedApps, otherApps } = useMemo(() => {
    const recent = [];
    const others = [];
    filteredAppNames.forEach(appName => {
      if (updatedAppNames.has(appName.toLowerCase())) recent.push(appName);
      else others.push(appName);
    });
    return { recentlyUpdatedApps: recent, otherApps: others };
  }, [filteredAppNames, updatedAppNames]);

  const handleFilterByApp = (appName) => {
    setSearchQuery(appName);
    const el = document.getElementById('apps-catalog-section');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  if (loading) {
    return (
      <div className="w-full flex items-center justify-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-3 fade-up">
          <div className="w-7 h-7 rounded-full border-2 border-border border-t-foreground animate-spin" />
          <p className="text-muted-foreground text-xs font-medium">Loading app catalog…</p>
        </div>
      </div>
    );
  }

  const totalCatalogCount = Object.keys(groupedApps).length;

  return (
    <div className="p-3.5 sm:p-6 md:p-8 max-w-6xl mx-auto w-full fade-up space-y-6 sm:space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">App Store</h2>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-muted text-foreground border border-border">
              {totalCatalogCount} apps
            </span>
          </div>
          <p className="text-muted-foreground text-xs sm:text-sm max-w-lg">
            Ready-to-install custom patched Android APKs for non-rooted devices. Rebuilt continuously with the latest community patches.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowObtainiumModal(true)}
            className="flex items-center gap-1.5 h-9 px-3.5 rounded-xl border border-border text-xs sm:text-[13px] font-semibold bg-card hover:bg-muted active:scale-[0.98] transition-all shadow-xs"
          >
            <Smartphone size={14} className="text-foreground" />
            <span>Obtainium setup</span>
          </button>
          <a
            href={`${import.meta.env.BASE_URL}downloads.html`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 h-9 px-3 rounded-xl border border-border text-xs sm:text-[13px] font-medium bg-card hover:bg-muted text-muted-foreground hover:text-foreground transition-all shadow-xs"
          >
            <Download size={13} />
            <span className="hidden sm:inline">All downloads</span>
          </a>
          <div className="flex items-center gap-1.5 h-9 px-3 rounded-xl border border-border text-xs text-muted-foreground bg-muted/20">
            <Clock size={12} />
            <span>{formatTimeAgo(manifest?.updated_at)}</span>
          </div>
        </div>
      </div>

      {/* Upstream Patch Changelogs */}
      <PatchChangelogsSection
        patchChangelogs={patchChangelogs}
        onFilterByApp={handleFilterByApp}
      />

      {/* Filter and Search Bar */}
      <div id="apps-catalog-section" className="space-y-3 scroll-mt-4">
        <FilterBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
          sources={sources}
          totalResults={filteredAppNames.length}
        />

        {/* Quick Category Pills */}
        {categories.length > 0 && (
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`h-7 px-3 rounded-full text-xs font-semibold whitespace-nowrap transition-colors shrink-0 ${
                selectedCategory === 'all'
                  ? 'bg-foreground text-background'
                  : 'bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
            >
              All categories
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(selectedCategory === cat ? 'all' : cat)}
                className={`h-7 px-3 rounded-full text-xs font-medium whitespace-nowrap transition-colors shrink-0 ${
                  selectedCategory === cat
                    ? 'bg-foreground text-background font-semibold'
                    : 'bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Recently Updated Apps Section */}
      {recentlyUpdatedApps.length > 0 && (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Flame size={16} className="text-foreground" />
            <h3 className="text-sm sm:text-base font-bold">Recently updated</h3>
            <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-[11px] font-semibold border border-border">
              {recentlyUpdatedApps.length}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
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

      {/* Main Apps Catalog */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-muted-foreground" />
          <h3 className="text-sm sm:text-base font-bold">
            {recentlyUpdatedApps.length > 0 ? 'All other apps' : 'All apps'}
          </h3>
          <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-[11px] font-semibold border border-border">
            {otherApps.length}
          </span>
        </div>

        {otherApps.length === 0 && recentlyUpdatedApps.length === 0 ? (
          <div className="text-center p-8 sm:p-12 border border-dashed border-border rounded-2xl bg-card">
            <PackageSearch size={32} className="mx-auto mb-2.5 text-muted-foreground" />
            <h4 className="text-sm font-semibold mb-1">No matching apps found</h4>
            <p className="text-muted-foreground text-xs mb-3">Try adjusting your search terms or category filter.</p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedSource('all');
                setSelectedCategory('all');
              }}
              className="px-3.5 py-1.5 rounded-lg bg-muted text-xs font-semibold hover:bg-muted/80 transition-colors"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
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

      {/* Obtainium Modal */}
      {showObtainiumModal && (
        <div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-xs transition-opacity"
          onClick={() => setShowObtainiumModal(false)}
        >
          <div
            className="bg-card border border-border rounded-t-3xl sm:rounded-2xl w-full sm:max-w-lg p-5 sm:p-6 relative fade-up max-h-[92dvh] overflow-y-auto shadow-xl"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Obtainium setup"
          >
            <button
              onClick={() => setShowObtainiumModal(false)}
              className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="Close"
            >
              <X size={17} />
            </button>

            <div className="flex items-center gap-3 mb-4 pr-8">
              <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center shrink-0 border border-border">
                <Smartphone size={20} className="text-foreground" />
              </div>
              <div>
                <h3 className="text-base font-bold">Obtainium auto-updates</h3>
                <p className="text-xs text-muted-foreground">Auto-update every APK seamlessly in the background</p>
              </div>
            </div>

            <div className="space-y-1.5 mb-4">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Bulk import URL
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={BULK_URL}
                  onFocus={(e) => e.target.select()}
                  className="flex-1 h-10 bg-background border border-border rounded-xl px-3 text-xs font-mono focus:outline-none focus:border-foreground min-w-0"
                />
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(BULK_URL);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="flex items-center gap-1.5 h-10 px-3.5 bg-foreground text-background rounded-xl text-xs font-semibold hover:opacity-90 active:scale-[0.98] transition-all shrink-0"
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>

            <div className="space-y-2 text-xs text-muted-foreground bg-muted/40 border border-border rounded-xl p-3.5 mb-4">
              <p className="font-semibold text-foreground">How to import:</p>
              <ol className="list-decimal list-inside space-y-1 pl-1">
                <li>Install and open <strong className="text-foreground">Obtainium</strong> on your Android phone.</li>
                <li>Tap <strong className="text-foreground">+ Add App</strong> → select <strong className="text-foreground">Import / Export</strong>.</li>
                <li>Choose <strong className="text-foreground">Import from URL</strong> and paste the link above.</li>
              </ol>
            </div>

            <div className="flex items-center justify-between pt-1 flex-wrap gap-2">
              <a
                href={`${import.meta.env.BASE_URL}obtainium.json`}
                download="obtainium.json"
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground font-medium transition-colors"
              >
                <Download size={13} />
                <span>Download obtainium.json</span>
              </a>
              <button
                onClick={() => setShowObtainiumModal(false)}
                className="h-9 px-4 bg-foreground text-background rounded-xl text-xs font-semibold hover:opacity-90 transition-opacity"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
