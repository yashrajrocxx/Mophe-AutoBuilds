import React, { useState, useEffect } from 'react';
import { Tag, Calendar, ChevronDown, Check, RefreshCw, Archive, ExternalLink } from 'lucide-react';
import { formatTimeAgo, formatExactDate } from '../utils/dateUtils';

export function ReleaseSelector({ currentReleaseTag, onSelectRelease, isArchivedView }) {
  const [releases, setReleases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Fetch GitHub releases list
    setLoading(true);
    fetch('https://api.github.com/repos/yashrajrocxx/Mophe-AutoBuilds/releases?per_page=20')
      .then(res => {
        if (res.ok) return res.json();
        return [];
      })
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setReleases(data);
        } else {
          // Fallback if rate limited or no API
          setReleases([
            {
              id: 'latest',
              tag_name: 'latest',
              name: 'Latest Release (Current)',
              published_at: new Date().toISOString()
            }
          ]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.warn("Failed to fetch releases list:", err);
        setReleases([
          {
            id: 'latest',
            tag_name: 'latest',
            name: 'Latest Release (Current)',
            published_at: new Date().toISOString()
          }
        ]);
        setLoading(false);
      });
  }, []);

  const selectedRelease = releases.find(r => r.tag_name === currentReleaseTag) || releases[0] || {
    tag_name: currentReleaseTag || 'latest',
    name: 'Latest Release',
    published_at: ''
  };

  const handleSelect = (rel) => {
    setIsOpen(false);
    if (onSelectRelease) {
      onSelectRelease(rel);
    }
  };

  return (
    <div className="relative inline-block text-left z-30">
      {/* Selector Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all duration-150 ${
          isArchivedView
            ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30 hover:bg-amber-500/20'
            : 'bg-card/90 hover:bg-muted text-foreground border-border/70 hover:border-accent/40 shadow-2xs'
        }`}
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <Tag size={13} className={isArchivedView ? 'text-amber-500' : 'text-accent'} />
        <div className="flex items-center gap-1.5">
          <span className="font-mono">{selectedRelease.tag_name}</span>
          <span className="text-muted-foreground font-normal hidden sm:inline">
            ({formatExactDate(selectedRelease.published_at) || 'Current'})
          </span>
        </div>
        <ChevronDown size={13} className={`text-muted-foreground transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-20" 
          onClick={() => setIsOpen(false)} 
        />
      )}

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 sm:w-80 rounded-2xl bg-card border border-border/80 shadow-xl backdrop-blur-xl z-30 py-2 yr-fade-up overflow-hidden">
          <div className="px-4 py-2 border-b border-border/50 flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Archive size={12} />
              Release History
            </span>
            <a
              href="https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] text-accent hover:underline flex items-center gap-1"
            >
              <span>GitHub</span>
              <ExternalLink size={10} />
            </a>
          </div>

          <div className="max-h-64 overflow-y-auto py-1 divide-y divide-border/20">
            {releases.map((rel) => {
              const isSelected = rel.tag_name === currentReleaseTag;
              const formattedDate = formatTimeAgo(rel.published_at);
              const exactDate = formatExactDate(rel.published_at);

              return (
                <button
                  key={rel.id || rel.tag_name}
                  onClick={() => handleSelect(rel)}
                  className={`w-full text-left px-4 py-2.5 flex items-start justify-between gap-2 hover:bg-muted/50 transition-colors text-xs ${
                    isSelected ? 'bg-accent/10 font-semibold text-accent' : 'text-foreground'
                  }`}
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono font-bold">{rel.tag_name}</span>
                      {rel.tag_name === 'latest' && (
                        <span className="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold">
                          LATEST
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-muted-foreground truncate max-w-[200px]">
                      {rel.name || 'Automated Build'}
                    </span>
                    <span className="text-[10px] text-muted-foreground/80">
                      {exactDate} ({formattedDate})
                    </span>
                  </div>

                  {isSelected && (
                    <Check size={14} className="text-accent mt-1 shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
