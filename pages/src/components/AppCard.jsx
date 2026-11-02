import React, { useState } from 'react';
import { Download, CheckCircle2, Clock, Smartphone, Copy, Check, Sparkles } from 'lucide-react';
import { formatTimeAgo } from '../utils/dateUtils';
import { getAppMeta } from '../utils/appMeta';

export function AppCard({ appName, appEntries, isRecentlyUpdated, manifestUpdatedAt }) {
  const [imgError, setImgError] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedPkg, setCopiedPkg] = useState(false);

  const meta = getAppMeta(appName);
  const firstEntry = appEntries[0] || {};
  const patchSource = firstEntry.source || 'morphe';
  const packageName = firstEntry.package || meta.package || '';

  const iconUrl = (!imgError && (firstEntry.icon_url || meta.icon)) || meta.icon;

  const latestBuildDate = appEntries.reduce((latest, e) => {
    if (!e.built_at) return latest;
    if (!latest) return e.built_at;
    return e.built_at > latest ? e.built_at : latest;
  }, firstEntry.built_at || manifestUpdatedAt);

  const versionDisplay = firstEntry.built_version || firstEntry.config_version || 'Latest';
  const hasApk = appEntries.some((e) => Boolean(e.apk));

  const copyPackageName = () => {
    if (!packageName) return;
    navigator.clipboard?.writeText(packageName);
    setCopiedPkg(true);
    setTimeout(() => setCopiedPkg(false), 2000);
  };

  const copyApkUrl = (url) => {
    if (!url) return;
    navigator.clipboard?.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  return (
    <div className="group relative bg-card rounded-2xl border border-border flex flex-col justify-between overflow-hidden hover:border-foreground/40 hover:shadow-sm transition-all duration-200">
      {/* Top Banner (Recently updated or featured) */}
      {isRecentlyUpdated && (
        <div className="px-3.5 py-1.5 border-b border-border flex items-center justify-between bg-muted/60 text-xs">
          <span className="flex items-center gap-1.5 font-semibold text-[11px] tracking-wide">
            <Sparkles size={12} className="text-foreground" />
            Recently updated
          </span>
          <span className="text-[11px] text-muted-foreground font-medium">
            {formatTimeAgo(latestBuildDate)}
          </span>
        </div>
      )}

      {/* Main card body */}
      <div className="p-4 sm:p-5 flex-1">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="relative w-12 h-12 shrink-0">
            {iconUrl ? (
              <img
                src={iconUrl}
                alt={meta.name}
                onError={() => setImgError(true)}
                className="w-12 h-12 rounded-xl object-contain border border-border bg-background p-1.5 shadow-xs"
                loading="lazy"
              />
            ) : (
              <div className="w-12 h-12 rounded-xl bg-muted border border-border flex items-center justify-center text-foreground font-bold text-lg">
                {meta.name.charAt(0)}
              </div>
            )}
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-background rounded-full flex items-center justify-center border border-border">
              <CheckCircle2 className="w-3 h-3 text-foreground" />
            </div>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap justify-end">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold border border-border text-muted-foreground bg-muted/30 capitalize">
              {patchSource}
            </span>
          </div>
        </div>

        {/* Title and category */}
        <h4 className="text-[15px] sm:text-base font-bold tracking-tight truncate text-foreground mb-1">
          {meta.name}
        </h4>

        {packageName && (
          <button
            type="button"
            onClick={copyPackageName}
            title="Click to copy package name"
            className="flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground hover:text-foreground transition-colors mb-2.5 max-w-full text-left truncate group/pkg"
          >
            <span className="truncate">{packageName}</span>
            {copiedPkg ? (
              <Check size={11} className="text-foreground shrink-0" />
            ) : (
              <Copy size={11} className="opacity-0 group-hover/pkg:opacity-100 shrink-0 transition-opacity" />
            )}
          </button>
        )}

        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3 flex-wrap">
          <span className="truncate font-medium">{meta.category}</span>
          <span aria-hidden="true" className="opacity-50">·</span>
          <span className="font-mono font-semibold text-foreground/80 shrink-0">
            v{versionDisplay}
          </span>
        </div>

        {!isRecentlyUpdated && latestBuildDate && (
          <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground pt-2.5 border-t border-border">
            <Clock size={12} className="shrink-0" />
            <span>Updated {formatTimeAgo(latestBuildDate)}</span>
          </div>
        )}
      </div>

      {/* Action buttons footer */}
      <div className="px-3 pb-3 sm:px-4 sm:pb-4 flex flex-col gap-2 pt-2 border-t border-border/60 bg-muted/10">
        {hasApk ? (
          appEntries.map((entry, idx) => {
            if (!entry.apk) return null;
            const isUniversal = (entry.arch || '').toLowerCase().includes('universal');
            const archLabel = isUniversal ? 'Universal' : (entry.arch || 'arm64-v8a');
            const apkUrl = `https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/latest/download/${entry.apk}`;
            const obtainiumUrl = entry.obtainium_url;

            return (
              <div key={idx} className="flex flex-col gap-1.5">
                <div className="flex items-center gap-1.5">
                  <a
                    href={apkUrl}
                    title={`Download ${archLabel} APK`}
                    className="flex-1 flex items-center justify-between px-3 h-10 sm:h-9 bg-foreground text-background rounded-xl text-[13px] font-semibold hover:opacity-90 active:scale-[0.99] transition-all shadow-xs"
                  >
                    <span className="flex items-center gap-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${
                        isUniversal
                          ? 'bg-background/20 text-background'
                          : 'bg-background/15 text-background'
                      }`}>
                        {archLabel}
                      </span>
                      <span className="text-xs font-mono font-normal opacity-85">
                        v{entry.built_version || versionDisplay}
                      </span>
                    </span>
                    <Download size={14} className="shrink-0" />
                  </a>

                  {obtainiumUrl && (
                    <a
                      href={obtainiumUrl}
                      title="Add to Obtainium (1-click auto-updater)"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="h-10 sm:h-9 px-2.5 sm:px-3 flex items-center gap-1.5 bg-background text-foreground border border-border rounded-xl text-[12px] font-semibold hover:bg-muted active:scale-[0.98] transition-all shrink-0 shadow-xs"
                    >
                      <Smartphone size={13} className="shrink-0" />
                      <span className="hidden sm:inline">Obtainium</span>
                    </a>
                  )}

                  <button
                    type="button"
                    onClick={() => copyApkUrl(apkUrl)}
                    title="Copy direct APK link"
                    className="h-10 sm:h-9 w-9 flex items-center justify-center bg-background text-muted-foreground hover:text-foreground border border-border rounded-xl hover:bg-muted active:scale-[0.98] transition-all shrink-0"
                    aria-label="Copy direct download link"
                  >
                    {copiedLink ? <Check size={13} className="text-foreground" /> : <Copy size={13} />}
                  </button>
                </div>
              </div>
            );
          })
        ) : (
          <div className="py-2.5 px-3 rounded-xl border border-dashed border-border bg-muted/40 text-center">
            <p className="text-xs font-medium text-foreground mb-1">
              Build queued / ready in next run
            </p>
            <p className="text-[11px] text-muted-foreground">
              Configured in catalog. Triggers on the daily cron or via manual dispatch.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
