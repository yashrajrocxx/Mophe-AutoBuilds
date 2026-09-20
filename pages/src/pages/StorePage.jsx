import React, { useState, useEffect, useMemo } from 'react';
import {
  PackageSearch,
  Clock,
  Flame,
  Smartphone,
  Download,
  Copy,
  Check,
  X
} from 'lucide-react';
import { PatchChangelogsSection } from '../components/PatchChangelogsSection';
import { AppCard } from '../components/AppCard';
import { FilterBar } from '../components/FilterBar';
import { formatTimeAgo } from '../utils/dateUtils';

const BULK_URL = 'https://raw.githubusercontent.com/yashrajrocxx/Mophe-AutoBuilds/main/obtainium.json';

export function StorePage() {
  const [manifest, setManifest] = useState(null);
  const [patchChangelogs, setPatchChangelogs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showObtainiumModal, setShowObtainiumModal] = useState(false);
  const [copied, setCopied] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState('all');
  const [selectedArch, setSelectedArch] = useState('all');

  useEffect(() => {
    Promise.allSettled([
      fetch(`${import.meta.env.BASE_URL}manifest.json`).then(r => r.ok ? r.json() : null),
      fetch(`${import.meta.env.BASE_URL}patch_changelogs.json`).then(r => r.ok ? r.json() : null)
    ]).then(([manifestRes, changelogsRes]) => {
      const manifestData = manifestRes.status === 'fulfilled' ? manifestRes.value : null;
      const changelogsData = changelogsRes.status === 'fulfilled' ? changelogsRes.value : null;

      setManifest(manifestData);
      setPatchChangelogs(manifestData?.patch_changelogs || changelogsData || {});
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const entries = useMemo(() => {
    if (!manifest?.entries) return [];
    return Object.values(manifest.entries);
  }, [manifest]);

  const groupedApps = useMemo(() => {
    return entries.reduce((acc, entry) => {
      if (!acc[entry.app_name]) acc[entry.app_name] = [];
      acc[entry.app_name].push(entry);
      return acc;
    }, {});
  }, [entries]);

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
    entries.forEach(e => { if (e.source) s.add(e.source.toLowerCase()); });
    return Array.from(s);
  }, [entries]);

  const arches = useMemo(() => {
    const a = new Set();
    entries.forEach(e => { if (e.arch) a.add(e.arch.toLowerCase()); });
    return Array.from(a);
  }, [entries]);

  const filteredAppNames = useMemo(() => {
    return Object.keys(groupedApps).filter(appName => {
      const appEntries = groupedApps[appName];
      const firstEntry = appEntries[0] || {};

      const matchesSearch = !searchQuery ||
        appName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (firstEntry.package || '').toLowerCase().includes(searchQuery.toLowerCase());

      const matchesSource = selectedSource === 'all' ||
        (firstEntry.source || '').toLowerCase() === selectedSource.toLowerCase();

      const matchesArch = selectedArch === 'all' ||
        appEntries.some(e => (e.arch || '').toLowerCase() === selectedArch.toLowerCase());

      return matchesSearch && matchesSource && matchesArch;
    });
  }, [groupedApps, searchQuery, selectedSource, selectedArch]);

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

  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-6xl mx-auto w-full fade-up space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-border">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">App store</h2>
          <p className="text-muted-foreground text-[13px] sm:text-sm mt-1 max-w-lg">
            Patched Android apps, rebuilt daily. {entries.length > 0 && `${Object.keys(groupedApps).length} apps available.`}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowObtainiumModal(true)}
            className="flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-border text-[13px] font-semibold hover:bg-muted transition-colors"
          >
            <Smartphone size={14} />
            <span>Obtainium setup</span>
          </button>
          <div className="flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-border text-xs text-muted-foreground">
            <Clock size={13} />
            <span>Updated {formatTimeAgo(manifest?.updated_at)}</span>
          </div>
        </div>
      </div>

      <PatchChangelogsSection
        patchChangelogs={patchChangelogs}
        onFilterByApp={handleFilterByApp}
      />

      <div id="apps-catalog-section" className="space-y-3 scroll-mt-4">
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

      {recentlyUpdatedApps.length > 0 && (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Flame size={15} />
            <h3 className="text-[15px] font-bold">Recently updated</h3>
            <span className="px-1.5 py-0.5 rounded-md bg-muted text-muted-foreground text-[11px] font-semibold">
              {recentlyUpdatedApps.length}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
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

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Smartphone size={15} className="text-muted-foreground" />
          <h3 className="text-[15px] font-bold">
            {recentlyUpdatedApps.length > 0 ? 'All other apps' : 'All apps'}
          </h3>
          <span className="px-1.5 py-0.5 rounded-md bg-muted text-muted-foreground text-[11px] font-semibold">
            {otherApps.length}
          </span>
        </div>

        {otherApps.length === 0 && recentlyUpdatedApps.length === 0 ? (
          <div className="text-center p-10 border border-border rounded-xl">
            <PackageSearch size={28} className="mx-auto mb-2 text-muted-foreground" />
            <h4 className="text-sm font-semibold mb-1">No matching apps found</h4>
            <p className="text-muted-foreground text-xs">Try adjusting your search or filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
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

      {/* Obtainium modal */}
      {showObtainiumModal && (
        <div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/50"
          onClick={() => setShowObtainiumModal(false)}
        >
          <div
            className="bg-card border border-border rounded-t-2xl sm:rounded-2xl w-full sm:max-w-lg p-5 sm:p-6 relative fade-up max-h-[90dvh] overflow-y-auto"
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
              <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center shrink-0">
                <Smartphone size={19} />
              </div>
              <div>
                <h3 className="text-base font-bold">Obtainium setup</h3>
                <p className="text-xs text-muted-foreground">Auto-update every app from GitHub releases</p>
              </div>
            </div>

            <div className="space-y-1.5 mb-4">
              <label className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Bulk config URL
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={BULK_URL}
                  onFocus={(e) => e.target.select()}
                  className="flex-1 h-10 bg-background border border-border rounded-lg px-3 text-xs font-mono focus:outline-none focus:border-foreground min-w-0"
                />
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(BULK_URL);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="flex items-center gap-1.5 h-10 px-3.5 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-85 transition-opacity shrink-0"
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>

            <ol className="list-decimal list-inside space-y-1.5 text-[13px] text-muted-foreground bg-muted/50 border border-border rounded-xl p-4 mb-4">
              <li>In Obtainium, tap <strong className="text-foreground">+</strong> → <strong className="text-foreground">Import / Export</strong>.</li>
              <li>Choose <strong className="text-foreground">Import from URL</strong>.</li>
              <li>Paste the URL above and tap <strong className="text-foreground">Import</strong>.</li>
            </ol>

            <div className="flex items-center justify-between pt-1">
              <a
                href={`${import.meta.env.BASE_URL}obtainium.json`}
                download="obtainium.json"
                className="flex items-center gap-1.5 text-[13px] text-muted-foreground hover:text-foreground font-medium transition-colors"
              >
                <Download size={14} />
                <span>Download obtainium.json</span>
              </a>
              <button
                onClick={() => setShowObtainiumModal(false)}
                className="h-9 px-4 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-85 transition-opacity"
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
