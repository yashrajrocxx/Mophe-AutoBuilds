import React, { useState } from 'react';
import { Download, CheckCircle2, Clock, Smartphone } from 'lucide-react';
import { formatTimeAgo } from '../utils/dateUtils';
import { getAppMeta } from '../utils/appMeta';

export function AppCard({ appName, appEntries, isRecentlyUpdated, manifestUpdatedAt }) {
  const [imgError, setImgError] = useState(false);
  const meta = getAppMeta(appName);
  const firstEntry = appEntries[0] || {};
  const patchSource = firstEntry.source || 'morphe';

  const iconUrl = (!imgError && (firstEntry.icon_url || meta.icon)) || meta.icon;

  const latestBuildDate = appEntries.reduce((latest, e) => {
    if (!e.built_at) return latest;
    if (!latest) return e.built_at;
    return e.built_at > latest ? e.built_at : latest;
  }, firstEntry.built_at || manifestUpdatedAt);

  const versionDisplay = firstEntry.built_version || firstEntry.config_version || 'Latest';

  return (
    <div className="relative bg-card rounded-xl border border-border flex flex-col justify-between overflow-hidden hover:border-foreground/30 transition-colors">
      {isRecentlyUpdated && (
        <div className="px-4 py-1.5 border-b border-border flex items-center justify-between bg-muted/50">
          <span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide">
            <span className="w-1.5 h-1.5 rounded-full bg-foreground" />
            Recently updated
          </span>
          <span className="text-[11px] text-muted-foreground">
            {formatTimeAgo(latestBuildDate)}
          </span>
        </div>
      )}

      <div className="p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="w-12 h-12 relative shrink-0">
            {iconUrl ? (
              <img
                src={iconUrl}
                alt={meta.name}
                onError={() => setImgError(true)}
                className="w-12 h-12 rounded-xl object-contain border border-border bg-white p-1"
                loading="lazy"
              />
            ) : (
              <div className="w-12 h-12 rounded-xl bg-muted border border-border flex items-center justify-center text-foreground font-bold text-lg">
                {meta.name.charAt(0)}
              </div>
            )}
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-background rounded-full flex items-center justify-center border border-border">
              <CheckCircle2 className="w-3 h-3" />
            </div>
          </div>

          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold border border-border text-muted-foreground capitalize shrink-0">
            {patchSource}
          </span>
        </div>

        <h4 className="text-[15px] font-semibold truncate mb-0.5">
          {meta.name}
        </h4>
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
          <span className="truncate">{meta.category}</span>
          <span aria-hidden="true">·</span>
          <span className="font-mono shrink-0">v{versionDisplay}</span>
        </div>

        {!isRecentlyUpdated && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground pt-2.5 border-t border-border">
            <Clock size={12} className="shrink-0" />
            <span>Updated {formatTimeAgo(latestBuildDate)}</span>
          </div>
        )}
      </div>

      <div className="px-3 pb-3 flex flex-col gap-2">
        {appEntries.map((entry, idx) => {
          if (!entry.apk) return null;
          const archLabel = (entry.arch || 'universal').toUpperCase();
          const apkUrl = `https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/download/latest/${entry.apk}`;
          const obtainiumUrl = entry.obtainium_url;

          return (
            <div key={idx} className="flex items-center gap-2">
              <a
                href={apkUrl}
                title={`Download ${archLabel} APK`}
                className="flex-1 flex items-center justify-between px-3 h-9 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-85 transition-opacity"
              >
                <span className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold tracking-wide">
                    {archLabel}
                  </span>
                  <span className="text-xs font-mono font-normal opacity-70">
                    v{entry.built_version || versionDisplay}
                  </span>
                </span>
                <Download size={14} />
              </a>

              {obtainiumUrl && (
                <a
                  href={obtainiumUrl}
                  title="Add to Obtainium"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="h-9 px-3 flex items-center gap-1.5 bg-background text-foreground border border-border rounded-lg text-[13px] font-semibold hover:bg-muted transition-colors shrink-0"
                >
                  <Smartphone size={14} />
                  <span>Obtainium</span>
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
