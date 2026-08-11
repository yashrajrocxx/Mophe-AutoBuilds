import React, { useState, useEffect } from 'react';
import { Download, CheckCircle2, Box, Smartphone, Clock } from 'lucide-react';

function timeAgo(dateString) {
  if (!dateString) return "Recently";
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  
  if (seconds < 60) return "Just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min${minutes !== 1 ? 's' : ''} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr${hours !== 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days !== 1 ? 's' : ''} ago`;
  const months = Math.floor(days / 30);
  return `${months} mo${months !== 1 ? 's' : ''} ago`;
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
      <div className="w-full h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 yr-fade-up">
          <div className="w-8 h-8 rounded-full border-2 border-accent border-t-transparent animate-spin" />
          <p className="text-muted-foreground text-sm font-medium">Loading App Store...</p>
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
    <div className="p-8 max-w-7xl mx-auto w-full yr-fade-up">
      <div className="mb-10">
        <h2 className="text-3xl font-semibold mb-2">App Store</h2>
        <p className="text-muted-foreground text-[15px]">Download the latest patched APKs directly from the release pipeline.</p>
      </div>

      {entries.length === 0 ? (
        <div className="text-center p-12 bg-muted/20 border border-border rounded-xl">
          <Box className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-1">No apps found</h3>
          <p className="text-muted-foreground text-sm">The manifest is empty or could not be loaded.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(apps).map(([appName, appEntries]) => (
            <div key={appName} className="bg-background rounded-xl border border-border shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col group">
              <div className="p-6 flex-1">
                <div className="flex justify-between items-start mb-4">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center border border-accent/10">
                    <Smartphone className="w-6 h-6 text-accent" />
                  </div>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[11px] font-medium tracking-wide uppercase">
                    <CheckCircle2 size={12} />
                    Verified
                  </span>
                </div>
                
                <h3 className="text-xl font-semibold mb-1 capitalize">{appName}</h3>
                <div className="flex flex-col gap-2 mt-4 text-[13px] text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Box size={14} className="opacity-70" />
                    <span>Multiple Architectures</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock size={14} className="opacity-70" />
                    <span>
                      {(() => {
                        const dateStr = manifest.updated_at;
                        return `Updated ${timeAgo(dateStr)}`;
                      })()}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="p-4 bg-muted/30 border-t border-border flex flex-col gap-2">
                {appEntries.map((entry, idx) => (
                  entry.apk ? (
                    <a 
                      key={idx}
                      href={`https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/download/latest/${entry.apk}`}
                      className="w-full flex items-center justify-between px-4 py-2.5 bg-background border border-border rounded-lg text-sm font-medium hover:border-accent/50 hover:bg-accent/5 transition-colors group/btn"
                    >
                      <span className="uppercase text-[11px] font-bold tracking-wider opacity-80">{entry.arch}</span>
                      <div className="flex items-center gap-2 text-accent">
                        <span className="text-[12px] opacity-0 group-hover/btn:opacity-100 transition-opacity">v{entry.built_version}</span>
                        <Download size={14} />
                      </div>
                    </a>
                  ) : null
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
