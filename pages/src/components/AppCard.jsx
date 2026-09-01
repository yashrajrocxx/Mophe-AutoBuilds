import React from 'react';
import { Download, CheckCircle2, Smartphone, Box, Clock, Layers, Sparkles } from 'lucide-react';

export function AppCard({ appName, appEntries, isRecentlyUpdated, onSelectApp, manifestUpdatedAt }) {
  const firstEntry = appEntries[0] || {};
  const hasIcon = Boolean(firstEntry.icon_url);
  const patchSource = firstEntry.source || "morphe";
  const packageName = firstEntry.package || "";

  // Get most recent built_at timestamp among all arch entries
  const latestBuildDate = appEntries.reduce((latest, e) => {
    if (!e.built_at) return latest;
    if (!latest) return e.built_at;
    return new Date(e.built_at) > new Date(latest) ? e.built_at : latest;
  }, firstEntry.built_at || manifestUpdatedAt);

  const formatTimeAgo = (dateString) => {
    if (!dateString) return "Recently";
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return "Just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    const months = Math.floor(days / 30);
    return `${months}mo ago`;
  };

  const getSourceBadgeColor = (source) => {
    const s = (source || "").toLowerCase();
    if (s.includes("piko-dev")) return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    if (s.includes("piko")) return "bg-purple-500/10 text-purple-500 border-purple-500/20";
    if (s.includes("morphe")) return "bg-sky-500/10 text-sky-500 border-sky-500/20";
    if (s.includes("paresh")) return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    if (s.includes("rookie")) return "bg-indigo-500/10 text-indigo-500 border-indigo-500/20";
    if (s.includes("rushi")) return "bg-rose-500/10 text-rose-500 border-rose-500/20";
    return "bg-accent/10 text-accent border-accent/20";
  };

  return (
    <div className={`bg-card/70 backdrop-blur-xl rounded-3xl border ${isRecentlyUpdated ? 'border-accent/40 shadow-lg shadow-accent/5' : 'border-border/60'} shadow-sm hover:shadow-xl hover:shadow-accent/5 hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col group relative`}>
      {/* Subtle hover gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent/0 to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

      {/* Top Banner if recently updated */}
      {isRecentlyUpdated && (
        <div className="bg-gradient-to-r from-accent/20 via-accent/10 to-transparent px-5 py-1.5 border-b border-accent/20 flex items-center justify-between text-[11px] font-bold text-accent">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
            </span>
            <span>RECENTLY UPDATED</span>
          </div>
          <span className="text-muted-foreground font-normal text-[10px]">
            {formatTimeAgo(latestBuildDate)}
          </span>
        </div>
      )}

      {/* Card Content */}
      <div className="p-6 flex-1 relative z-10">
        <div className="flex justify-between items-start mb-5">
          {hasIcon ? (
            <div className="relative">
              <img 
                src={firstEntry.icon_url} 
                alt={appName} 
                className="w-14 h-14 rounded-2xl object-cover shadow-sm border border-border/50 bg-white"
                loading="lazy"
              />
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-background rounded-full flex items-center justify-center shadow-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>
            </div>
          ) : (
            <div className="relative">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center border border-accent/20">
                <Smartphone className="w-6 h-6 text-accent" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-background rounded-full flex items-center justify-center shadow-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>
            </div>
          )}

          {/* Source Badge */}
          <span className={`px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase tracking-wider border ${getSourceBadgeColor(patchSource)}`}>
            {patchSource}
          </span>
        </div>

        <h4 className="text-xl font-bold mb-1 capitalize text-foreground/95 group-hover:text-foreground transition-colors">
          {appName.replace(/-/g, ' ')}
        </h4>
        
        {packageName && (
          <p className="text-[11.5px] font-mono text-muted-foreground/70 truncate mb-4">
            {packageName}
          </p>
        )}

        <div className="flex flex-col gap-2 pt-2 border-t border-border/40 text-[12.5px] text-muted-foreground font-medium">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 opacity-80">
              <Box size={13} className="text-accent" />
              <span>Version</span>
            </span>
            <span className="font-semibold text-foreground">
              v{firstEntry.built_version || firstEntry.config_version || 'Latest'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 opacity-80">
              <Clock size={13} className="text-accent" />
              <span>Updated</span>
            </span>
            <span className="font-medium text-muted-foreground">
              {formatTimeAgo(latestBuildDate)}
            </span>
          </div>
        </div>
      </div>

      {/* Action / Architecture Downloads */}
      <div className="p-4 bg-muted/20 border-t border-border/30 flex flex-col gap-2 relative z-10">
        {appEntries.map((entry, idx) => (
          entry.apk ? (
            <a 
              key={idx}
              href={`https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/download/latest/${entry.apk}`}
              className="w-full flex items-center justify-between px-3.5 py-2.5 bg-background/70 hover:bg-accent/10 border border-border/50 hover:border-accent/30 rounded-xl text-xs font-semibold text-foreground hover:text-accent transition-all group/btn"
            >
              <div className="flex items-center gap-2">
                <span className="uppercase text-[11px] font-mono font-bold tracking-wider opacity-80 group-hover/btn:opacity-100">{entry.arch}</span>
              </div>
              <div className="flex items-center gap-2.5">
                <span className="text-[11px] font-mono opacity-60 group-hover/btn:opacity-90 transition-opacity">v{entry.built_version}</span>
                <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center group-hover/btn:bg-accent group-hover/btn:text-accent-foreground transition-colors">
                  <Download size={12} className="group-hover/btn:animate-bounce" />
                </div>
              </div>
            </a>
          ) : null
        ))}
      </div>
    </div>
  );
}
