import React, { useState, useEffect } from 'react';
import { Download, CheckCircle2, Box, Smartphone, Clock, ArrowRight } from 'lucide-react';

function timeAgo(dateString) {
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
}

export function StorePage() {
  const [manifest, setManifest] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}manifest.json`)
      .then(res => res.json())
      .then(data => {
        setManifest(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch manifest:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-background/50 backdrop-blur-sm">
        <div className="flex flex-col items-center gap-4 yr-fade-up">
          <div className="w-10 h-10 rounded-full border-2 border-accent/20 border-t-accent animate-spin" />
          <p className="text-muted-foreground text-sm font-medium tracking-wide">Syncing catalog...</p>
        </div>
      </div>
    );
  }

  const entries = manifest?.entries ? Object.values(manifest.entries) : [];
  
  // Group by app_name
  const apps = entries.reduce((acc, entry) => {
    if (!acc[entry.app_name]) {
      acc[entry.app_name] = [];
    }
    acc[entry.app_name].push(entry);
    return acc;
  }, {});

  return (
    <div className="p-8 md:p-12 max-w-[1400px] mx-auto w-full yr-fade-up">
      <div className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-4xl font-bold tracking-tight mb-3 text-foreground">
            App Store
          </h2>
          <p className="text-muted-foreground text-[15px] max-w-xl leading-relaxed">
            Download the latest patched apps directly from the release pipeline. 
            Optimized, ad-free, and updated automatically.
          </p>
        </div>
        <div className="flex items-center gap-3 text-sm text-muted-foreground bg-muted/40 px-4 py-2 rounded-full border border-border/50">
          <Clock size={14} className="text-accent" />
          <span>Last sync: {timeAgo(manifest?.updated_at)}</span>
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="text-center p-16 bg-muted/10 border border-border/50 rounded-3xl backdrop-blur-md">
          <Box className="w-12 h-12 text-muted-foreground/30 mx-auto mb-5" />
          <h3 className="text-xl font-medium mb-2">Library is empty</h3>
          <p className="text-muted-foreground text-sm">The release manifest could not be loaded or no builds exist yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Object.entries(apps).map(([appName, appEntries]) => {
            const firstEntry = appEntries[0];
            const hasIcon = Boolean(firstEntry.icon_url);
            
            return (
              <div 
                key={appName} 
                className="bg-background/60 backdrop-blur-xl rounded-3xl border border-border/50 shadow-sm hover:shadow-xl hover:shadow-accent/5 hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col group relative"
              >
                {/* Subtle gradient glow effect on hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-accent/0 to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

                <div className="p-7 flex-1 relative z-10">
                  <div className="flex justify-between items-start mb-6">
                    {hasIcon ? (
                      <div className="relative">
                        <img 
                          src={firstEntry.icon_url} 
                          alt={appName} 
                          className="w-14 h-14 rounded-2xl object-cover shadow-sm border border-border/50 bg-white"
                        />
                        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-background rounded-full flex items-center justify-center">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        </div>
                      </div>
                    ) : (
                      <div className="relative">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center border border-accent/20">
                          <Smartphone className="w-6 h-6 text-accent" />
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-background rounded-full flex items-center justify-center">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <h3 className="text-xl font-bold mb-1.5 capitalize text-foreground/90 group-hover:text-foreground transition-colors">{appName.replace(/-/g, ' ')}</h3>
                  <div className="flex flex-col gap-2.5 mt-5 text-[13px] text-muted-foreground/80 font-medium">
                    <div className="flex items-center gap-2.5">
                      <Box size={14} className="opacity-60" />
                      <span>{appEntries.length} {appEntries.length === 1 ? 'Architecture' : 'Architectures'}</span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <Clock size={14} className="opacity-60" />
                      <span>
                        {(() => {
                          // The new check_app_updates.py ensures built_at is preserved
                          const dateStr = firstEntry.built_at || manifest.updated_at;
                          return `Updated ${timeAgo(dateStr)}`;
                        })()}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 bg-muted/20 border-t border-border/30 flex flex-col gap-2.5 relative z-10">
                  {appEntries.map((entry, idx) => (
                    entry.apk ? (
                      <a 
                        key={idx}
                        href={`https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/download/latest/${entry.apk}`}
                        className="w-full flex items-center justify-between px-4 py-3 bg-background/50 border border-border/40 rounded-xl text-sm font-semibold hover:border-accent/40 hover:bg-accent/5 hover:text-accent transition-all group/btn"
                      >
                        <span className="uppercase text-[11px] font-bold tracking-widest opacity-70 group-hover/btn:opacity-100 transition-opacity">{entry.arch}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-[12px] opacity-0 group-hover/btn:opacity-80 transition-opacity translate-x-2 group-hover/btn:translate-x-0 font-medium">v{entry.built_version}</span>
                          <div className="w-7 h-7 rounded-full bg-accent/10 flex items-center justify-center group-hover/btn:bg-accent group-hover/btn:text-accent-foreground transition-colors">
                            <Download size={13} className="group-hover/btn:animate-bounce" />
                          </div>
                        </div>
                      </a>
                    ) : null
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
