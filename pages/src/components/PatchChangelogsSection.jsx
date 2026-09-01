import React, { useState } from 'react';
import { Sparkles, ExternalLink, ChevronDown, ChevronUp, Tag, Calendar } from 'lucide-react';
import { ChangelogViewer } from './ChangelogViewer';

export function PatchChangelogsSection({ patchChangelogs, onFilterByApp }) {
  if (!patchChangelogs || Object.keys(patchChangelogs).length === 0) {
    return null;
  }

  const entries = Object.entries(patchChangelogs);
  const [expandedSources, setExpandedSources] = useState(
    entries.slice(0, 2).reduce((acc, [key]) => ({ ...acc, [key]: true }), {})
  );

  const toggleExpand = (key) => {
    setExpandedSources(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const expandAll = () => {
    setExpandedSources(entries.reduce((acc, [key]) => ({ ...acc, [key]: true }), {}));
  };

  const collapseAll = () => {
    setExpandedSources({});
  };

  const getSourceDisplayName = (source) => {
    const map = {
      morphe: "Morphe Patches",
      piko: "Piko Patches",
      "piko-dev": "Piko (Dev) Patches",
      paresh: "Paresh Patches",
      durgesh: "Durgesh (Chiggi) Patches",
      rookie: "Rookie Patches",
      rushiranpise: "Rushi Patches",
      browzomje: "Browzomje Patches",
      dh6k: "dh6k Patches",
    };
    return map[source.toLowerCase()] || `${source.charAt(0).toUpperCase() + source.slice(1)} Patches`;
  };

  return (
    <section className="mb-10 yr-fade-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent shrink-0">
            <Sparkles size={16} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                What's New in Patches
              </h3>
              <span className="px-2 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-accent text-[10px] font-bold tracking-wider uppercase">
                {entries.length} {entries.length === 1 ? 'Source Updated' : 'Sources Updated'}
              </span>
            </div>
            <p className="text-muted-foreground text-xs sm:text-sm">
              Upstream bug fixes, features, and app compatibility updates from the patch developers.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={expandAll}
            className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Changelog Cards Grid */}
      <div className="grid grid-cols-1 gap-4">
        {entries.map(([sourceKey, data]) => {
          const isExpanded = Boolean(expandedSources[sourceKey]);
          const oldTag = data.old_tag || "";
          const newTag = data.new_tag || data.tag || "latest";
          const displayName = getSourceDisplayName(sourceKey);
          const affectedApps = data.affected_apps || [];
          const publishedAt = data.published_at ? data.published_at.split("T")[0] : "";
          const versionTransition = oldTag && oldTag !== newTag ? `${oldTag} ➔ ${newTag}` : newTag;

          return (
            <div
              key={sourceKey}
              className="bg-card/80 backdrop-blur-md rounded-xl border border-border/60 shadow-2xs overflow-hidden transition-all duration-200 hover:border-accent/30"
            >
              {/* Card Top Header */}
              <div 
                className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-3 cursor-pointer select-none bg-muted/10 hover:bg-muted/20 transition-colors"
                onClick={() => toggleExpand(sourceKey)}
              >
                <div className="flex items-start sm:items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent shrink-0 mt-0.5 sm:mt-0">
                    <Tag size={15} />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-base font-bold text-foreground hover:text-accent transition-colors">
                        {displayName}
                      </h4>
                      <span className="px-2 py-0.5 rounded-md bg-accent/10 text-accent text-[11px] font-mono font-bold tracking-tight border border-accent/20">
                        {versionTransition}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-[11.5px] text-muted-foreground">
                      {publishedAt && (
                        <div className="flex items-center gap-1">
                          <Calendar size={12} className="opacity-70" />
                          <span>Released on {publishedAt}</span>
                        </div>
                      )}
                      {data.url && (
                        <a
                          href={data.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-accent hover:underline flex items-center gap-1 font-medium"
                        >
                          <span>Upstream Release</span>
                          <ExternalLink size={11} />
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Side: Affected Apps & Toggle Button */}
                <div className="flex items-center justify-between md:justify-end gap-2.5 pt-2 md:pt-0 border-t md:border-t-0 border-border/40">
                  {affectedApps.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className="text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mr-1 hidden sm:inline">
                        Apps:
                      </span>
                      {affectedApps.map(app => (
                        <button
                          key={app}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onFilterByApp) onFilterByApp(app);
                          }}
                          title={`Filter by ${app}`}
                          className="px-2 py-0.5 rounded-md bg-background hover:bg-accent/10 hover:border-accent/30 text-foreground text-[11px] font-medium border border-border/60 capitalize transition-colors"
                        >
                          {app.replace(/-/g, ' ')}
                        </button>
                      ))}
                    </div>
                  )}

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleExpand(sourceKey);
                    }}
                    className="p-1.5 rounded-md bg-muted/60 text-muted-foreground hover:text-foreground transition-transform shrink-0"
                    aria-label={isExpanded ? "Collapse changelog" : "Expand changelog"}
                  >
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                </div>
              </div>

              {/* Expandable Changelog Body */}
              {isExpanded && (
                <div className="p-4 sm:p-6 border-t border-border/50 bg-background/40">
                  <ChangelogViewer text={data.body} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
