import React, { useState } from 'react';
import { Download, CheckCircle2, Clock } from 'lucide-react';
import { formatTimeAgo } from '../utils/dateUtils';
import { getAppMeta } from '../utils/appMeta';

export function AppCard({ appName, appEntries, isRecentlyUpdated, manifestUpdatedAt }) {
  const [imgError, setImgError] = useState(false);
  const meta = getAppMeta(appName);
  const firstEntry = appEntries[0] || {};
  const patchSource = firstEntry.source || "morphe";

  // Use icon from manifest, fallback to curated high-res icon
  const iconUrl = (!imgError && (firstEntry.icon_url || meta.icon)) || meta.icon;

  // Get most recent built_at timestamp among all arch entries
  const latestBuildDate = appEntries.reduce((latest, e) => {
    if (!e.built_at) return latest;
    if (!latest) return e.built_at;
    return e.built_at > latest ? e.built_at : latest;
  }, firstEntry.built_at || manifestUpdatedAt);

  const getSourceBadge = (source) => {
    const s = (source || "").toLowerCase();
    if (s.includes("piko-dev")) {
      return { label: "Piko (Dev)", bg: "bg-accent/10 text-accent border-accent/20" };
    }
    if (s.includes("piko")) {
      return { label: "Piko", bg: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20" };
    }
    if (s.includes("morphe")) {
      return { label: "Morphe", bg: "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20" };
    }
    if (s.includes("paresh")) {
      return { label: "Paresh", bg: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20" };
    }
    if (s.includes("rookie")) {
      return { label: "Rookie", bg: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20" };
    }
    if (s.includes("rushi")) {
      return { label: "Rushi", bg: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20" };
    }
    return { label: source, bg: "bg-accent/10 text-accent border-accent/20" };
  };

  const sourceBadge = getSourceBadge(patchSource);
  const versionDisplay = firstEntry.built_version || firstEntry.config_version || "Latest";

  return (
    <div className={`group relative bg-card/90 backdrop-blur-md rounded-2xl border ${isRecentlyUpdated ? 'border-accent/40 shadow-xs' : 'border-border/60'} hover:border-accent/40 hover:shadow-md transition-all duration-200 flex flex-col justify-between overflow-hidden`}>
      
      {/* Subtle top indicator for recently updated */}
      {isRecentlyUpdated && (
        <div className="bg-accent/10 px-3.5 py-1 border-b border-accent/20 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10.5px] font-bold text-accent tracking-wide uppercase">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
            </span>
            <span>Recently Updated</span>
          </div>
          <span className="text-[10.5px] font-medium text-muted-foreground">
            {formatTimeAgo(latestBuildDate)}
          </span>
        </div>
      )}

      {/* Main Info */}
      <div className="p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3 mb-3.5">
          
          {/* Strictly Sized App Icon */}
          <div className="w-12 h-12 sm:w-13 sm:h-13 relative shrink-0">
            {iconUrl ? (
              <img
                src={iconUrl}
                alt={meta.name}
                onError={() => setImgError(true)}
                className="w-12 h-12 sm:w-13 sm:h-13 rounded-xl object-contain shadow-2xs border border-border/60 bg-white p-1"
                loading="lazy"
              />
            ) : (
              <div 
                className="w-12 h-12 sm:w-13 sm:h-13 rounded-xl flex items-center justify-center text-white font-bold text-base shadow-2xs"
                style={{ backgroundColor: meta.color || '#FF6F61' }}
              >
                {meta.name.charAt(0)}
              </div>
            )}
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-background rounded-full flex items-center justify-center shadow-2xs border border-border/40">
              <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            </div>
          </div>

          {/* Source Badge */}
          <span className={`px-2.5 py-0.5 rounded-full text-[10.5px] font-semibold tracking-wide border ${sourceBadge.bg} shrink-0`}>
            {sourceBadge.label}
          </span>
        </div>

        {/* Title & Metadata */}
        <div className="mb-2.5">
          <h4 className="text-sm sm:text-base font-bold text-foreground group-hover:text-accent transition-colors truncate mb-0.5">
            {meta.name}
          </h4>
          <div className="flex items-center gap-2 text-[11.5px] text-muted-foreground">
            <span className="truncate">{meta.category}</span>
            <span className="opacity-40">•</span>
            <span className="font-mono text-[11px] font-medium text-foreground/80 shrink-0">v{versionDisplay}</span>
          </div>
        </div>

        {/* Timestamp */}
        {!isRecentlyUpdated && (
          <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground pt-2 border-t border-border/40">
            <Clock size={11} className="opacity-60 shrink-0" />
            <span>Updated {formatTimeAgo(latestBuildDate)}</span>
          </div>
        )}
      </div>

      {/* Downloads Section */}
      <div className="p-2.5 bg-muted/20 border-t border-border/40 flex flex-col gap-1.5">
        {appEntries.map((entry, idx) => {
          if (!entry.apk) return null;
          const archLabel = (entry.arch || 'universal').toUpperCase();
          const apkUrl = `https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/download/latest/${entry.apk}`;

          return (
            <a
              key={idx}
              href={apkUrl}
              className="flex items-center justify-between px-3 py-1.5 bg-background hover:bg-accent hover:text-white border border-border/60 hover:border-accent rounded-lg text-xs font-semibold text-foreground transition-all duration-150 group/btn shadow-2xs"
            >
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] font-bold tracking-wider opacity-90 group-hover/btn:opacity-100">
                  {archLabel}
                </span>
                <span className="text-[10.5px] font-mono font-normal opacity-60 group-hover/btn:opacity-90">
                  v{entry.built_version || versionDisplay}
                </span>
              </div>

              <div className="flex items-center gap-1">
                <Download size={12} className="group-hover/btn:translate-y-0.5 transition-transform" />
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
