import React, { useState, useEffect, useMemo } from 'react';
import {
  Search, X, ChevronDown, CheckCircle2, XCircle, Download,
  Plus, Minus, Zap, ExternalLink, Calendar, Package, Globe
} from 'lucide-react';
import { ChangelogViewer } from '../components/ChangelogViewer';
import { formatTimeAgo } from '../utils/dateUtils';

const DL_LABELS = {
  download_direct: 'Manual link',
  download_playstore: 'Google Play',
  download_apkmirror: 'APKMirror',
  download_uptodown: 'Uptodown',
  download_apkpure: 'APKPure',
  download_apkcombo: 'APKCombo',
  download_aptoide: 'Aptoide',
  download_github: 'GitHub',
};

function StatusBadge({ status }) {
  const ok = status === 'success';
  return (
    <span className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded-md border border-border text-xs font-semibold shrink-0">
      {ok ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
      {ok ? 'Success' : 'Failed'}
    </span>
  );
}

function PatchList({ title, icon, items, emptyText }) {
  return (
    <div>
      <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">
        {icon}
        {title}
        <span className="font-mono font-normal">({items.length})</span>
      </p>
      {items.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {items.map((p, i) => (
            <span key={i} className="px-2 py-1 rounded-md bg-muted text-xs font-medium font-mono">
              {p}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">{emptyText}</p>
      )}
    </div>
  );
}

export function LogsPage() {
  const [reports, setReports] = useState(null);
  const [manifest, setManifest] = useState(null);
  const [patchLists, setPatchLists] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    Promise.allSettled([
      fetch(`${import.meta.env.BASE_URL}build_report.json`).then(r => r.ok ? r.json() : null),
      fetch(`${import.meta.env.BASE_URL}manifest.json`).then(r => r.ok ? r.json() : null),
      fetch(`${import.meta.env.BASE_URL}patch_lists.json`).then(r => r.ok ? r.json() : null),
    ]).then(([repRes, manRes, listsRes]) => {
      setReports(repRes.status === 'fulfilled' ? repRes.value : null);
      setManifest(manRes.status === 'fulfilled' ? manRes.value : null);
      setPatchLists(listsRes.status === 'fulfilled' && listsRes.value ? listsRes.value : {});
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const manifestByKey = useMemo(() => {
    const map = {};
    const entries = manifest?.entries || {};
    Object.values(entries).forEach(e => {
      map[`${e.app_name}|${e.arch}`] = e;
    });
    return map;
  }, [manifest]);

  const rows = useMemo(() => {
    const list = Array.isArray(reports) ? reports : [];
    return list
      .map((r, idx) => ({ ...r, _idx: idx, _entry: manifestByKey[`${r.app}|${r.arch}`] || null }))
      .filter(r => {
        if (statusFilter !== 'all' && r.status !== statusFilter) return false;
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (r.app || '').toLowerCase().includes(q) ||
          (r.source || '').toLowerCase().includes(q) ||
          (r.version || '').toLowerCase().includes(q);
      });
  }, [reports, manifestByKey, searchQuery, statusFilter]);

  const counts = useMemo(() => {
    const list = Array.isArray(reports) ? reports : [];
    return {
      total: list.length,
      success: list.filter(r => r.status === 'success').length,
      failed: list.filter(r => r.status !== 'success').length,
    };
  }, [reports]);

  const toggle = (idx) => setExpanded(prev => ({ ...prev, [idx]: !prev[idx] }));

  if (loading) {
    return (
      <div className="w-full flex items-center justify-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-3 fade-up">
          <div className="w-7 h-7 rounded-full border-2 border-border border-t-foreground animate-spin" />
          <p className="text-muted-foreground text-xs font-medium">Loading build logs…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-4xl mx-auto w-full fade-up space-y-5">
      {/* Header */}
      <div className="pb-5 border-b border-border">
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Build logs</h2>
        <p className="text-muted-foreground text-[13px] sm:text-sm mt-1">
          Per-app results from the latest pipeline run — download source, every patch switch, and upstream changelogs.
        </p>
        <div className="flex flex-wrap gap-2 mt-4">
          {[
            { label: 'Total', value: counts.total },
            { label: 'Success', value: counts.success },
            { label: 'Failed', value: counts.failed },
          ].map(s => (
            <div key={s.label} className="px-3 py-1.5 rounded-lg border border-border bg-card">
              <span className="text-[11px] text-muted-foreground font-medium mr-2">{s.label}</span>
              <span className="text-sm font-bold font-mono">{s.value}</span>
            </div>
          ))}
          {manifest?.updated_at && (
            <div className="px-3 py-1.5 rounded-lg border border-border bg-card flex items-center gap-1.5 text-xs text-muted-foreground">
              <Calendar size={12} />
              <span>Updated {formatTimeAgo(manifest.updated_at)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Search + status filter */}
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            placeholder="Search by app, source, or version…"
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
        <div className="flex gap-1 p-1 rounded-lg border border-border bg-card self-start">
          {['all', 'success', 'failed'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`h-8 px-3 rounded-md text-xs font-semibold capitalize transition-colors ${
                statusFilter === s ? 'bg-foreground text-background' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Rows */}
      {!rows.length ? (
        <div className="text-center p-12 border border-border rounded-xl">
          <Package size={28} className="mx-auto mb-3 text-muted-foreground" />
          <h3 className="text-sm font-semibold mb-1">No matching builds</h3>
          <p className="text-muted-foreground text-xs">Try a different search or filter.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rows.map((r) => {
            const isOpen = Boolean(expanded[r._idx]);
            const entry = r._entry;
            const lists = patchLists[`${r.app}|${r.source}`] || { include: [], exclude: [] };
            const injected = (r.patches || []).filter(p => p && p !== '-e');
            const apkUrl = r.apk
              ? `https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/download/latest/${r.apk}`
              : null;

            return (
              <div key={r._idx} className="bg-card rounded-xl border border-border overflow-hidden">
                <button
                  onClick={() => toggle(r._idx)}
                  aria-expanded={isOpen}
                  className="w-full p-4 flex items-center gap-3 text-left hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[15px] font-semibold capitalize truncate">{r.app}</span>
                      <span className="px-1.5 py-0.5 rounded bg-muted text-[10px] font-mono font-bold uppercase">
                        {r.arch}
                      </span>
                      <span className="px-1.5 py-0.5 rounded bg-muted text-[10px] font-semibold capitalize">
                        {r.source}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground font-mono mt-1 truncate">
                      v{r.version || entry?.built_version || 'unknown'}
                      {entry?.built_at ? ` · built ${formatTimeAgo(entry.built_at)}` : ''}
                    </p>
                  </div>
                  <StatusBadge status={r.status} />
                  <ChevronDown size={17} className={`shrink-0 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                </button>

                {isOpen && (
                  <div className="px-4 pb-5 pt-1 border-t border-border space-y-5 mt-1">
                    {/* Build facts */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3">
                      {[
                        { label: 'Version', value: `v${r.version || entry?.built_version || '—'}` },
                        { label: 'Downloaded via', value: DL_LABELS[r.dl_method] || r.dl_method || '—' },
                        { label: 'Patch tag', value: entry?.patch_tag || '—' },
                        { label: 'Built', value: entry?.built_at ? formatTimeAgo(entry.built_at) : '—' },
                      ].map(f => (
                        <div key={f.label} className="rounded-lg border border-border p-2.5">
                          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{f.label}</p>
                          <p className="text-[13px] font-semibold font-mono mt-0.5 truncate" title={f.value}>{f.value}</p>
                        </div>
                      ))}
                    </div>

                    {/* Patch switches */}
                    <PatchList
                      title="Included patches"
                      icon={<Plus size={12} />}
                      items={lists.include}
                      emptyText="No explicit includes — defaults apply."
                    />
                    <PatchList
                      title="Excluded patches"
                      icon={<Minus size={12} />}
                      items={lists.exclude}
                      emptyText="Nothing excluded."
                    />
                    <PatchList
                      title="Auto-injected at build time"
                      icon={<Zap size={12} />}
                      items={injected}
                      emptyText="None."
                    />

                    {/* Upstream changelog */}
                    {entry?.patch_changelog && (
                      <div>
                        <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                          <Globe size={12} />
                          Upstream patch notes
                          {entry.patch_url && (
                            <a
                              href={entry.patch_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="ml-1 flex items-center gap-1 normal-case tracking-normal font-medium text-foreground underline underline-offset-2 hover:opacity-70"
                            >
                              {entry.patch_tag || 'release'}
                              <ExternalLink size={11} />
                            </a>
                          )}
                        </p>
                        <div className="rounded-lg border border-border p-3.5 max-h-80 overflow-y-auto">
                          <ChangelogViewer text={entry.patch_changelog} />
                        </div>
                      </div>
                    )}

                    {apkUrl && r.status === 'success' && (
                      <a
                        href={apkUrl}
                        className="inline-flex items-center gap-2 h-9 px-4 rounded-lg bg-foreground text-background text-[13px] font-semibold hover:opacity-85 transition-opacity"
                      >
                        <Download size={14} />
                        Download APK
                      </a>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
