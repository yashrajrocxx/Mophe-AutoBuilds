import React from 'react';
import { ExternalLink, ChevronDown, Tag, Calendar } from 'lucide-react';
import { ChangelogViewer } from './ChangelogViewer';

export function PatchChangelogsSection({ patchChangelogs, onFilterByApp }) {
  if (!patchChangelogs || Object.keys(patchChangelogs).length === 0) {
    return null;
  }

  const entries = Object.entries(patchChangelogs);
  const [expandedSources, setExpandedSources] = React.useState({});

  const toggleExpand = (key) => {
    setExpandedSources(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const getSourceDisplayName = (source) => {
    const map = {
      morphe: 'Morphe Patches',
      piko: 'Piko Patches',
      paresh: 'Paresh Patches',
      durgesh: 'Durgesh (Chiggi) Patches',
      rookie: 'Rookie Patches',
      rushiranpise: 'Rushi Patches',
      browzomje: 'Browzomje Patches',
    };
    return map[source.toLowerCase()] || `${source.charAt(0).toUpperCase() + source.slice(1)} Patches`;
  };

  return (
    <section className="fade-up">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg sm:text-xl font-bold tracking-tight">
              What&apos;s new in patches
            </h3>
            <span className="px-2 py-0.5 rounded-md bg-muted text-muted-foreground text-[11px] font-semibold">
              {entries.length} updated
            </span>
          </div>
          <p className="text-muted-foreground text-[13px] mt-0.5">
            Upstream fixes and features from the patch developers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpandedSources(entries.reduce((acc, [key]) => ({ ...acc, [key]: true }), {}))}
            className="h-8 px-3 rounded-lg text-xs font-medium border border-border hover:bg-muted transition-colors"
          >
            Expand all
          </button>
          <button
            onClick={() => setExpandedSources({})}
            className="h-8 px-3 rounded-lg text-xs font-medium border border-border hover:bg-muted transition-colors"
          >
            Collapse
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {entries.map(([sourceKey, data]) => {
          const isExpanded = Boolean(expandedSources[sourceKey]);
          const oldTag = data.old_tag || '';
          const newTag = data.new_tag || data.tag || 'latest';
          const affectedApps = data.affected_apps || [];
          const publishedAt = data.published_at ? data.published_at.split('T')[0] : '';
          const versionTransition = oldTag && oldTag !== newTag ? `${oldTag} → ${newTag}` : newTag;

          return (
            <div key={sourceKey} className="bg-card rounded-xl border border-border overflow-hidden">
              <button
                onClick={() => toggleExpand(sourceKey)}
                aria-expanded={isExpanded}
                className="w-full p-4 flex items-center justify-between gap-3 text-left hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 rounded-lg bg-muted flex items-center justify-center shrink-0">
                    <Tag size={15} />
                  </div>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[15px] font-semibold truncate">
                        {getSourceDisplayName(sourceKey)}
                      </span>
                      <span className="px-2 py-0.5 rounded-md bg-muted text-[11px] font-mono font-medium">
                        {versionTransition}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1 text-xs text-muted-foreground">
                      {publishedAt && (
                        <span className="flex items-center gap-1">
                          <Calendar size={12} />
                          {publishedAt}
                        </span>
                      )}
                      {data.url && (
                        <span
                          role="link"
                          tabIndex={0}
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(data.url, '_blank', 'noopener');
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.stopPropagation();
                              window.open(data.url, '_blank', 'noopener');
                            }
                          }}
                          className="flex items-center gap-1 font-medium text-foreground underline underline-offset-2 hover:opacity-70"
                        >
                          Upstream release
                          <ExternalLink size={11} />
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <ChevronDown
                  size={17}
                  className={`shrink-0 text-muted-foreground transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                />
              </button>

              {(affectedApps.length > 0 || isExpanded) && (
                <div className="px-4 pb-4">
                  {affectedApps.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap mb-1">
                      <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mr-1">
                        Apps
                      </span>
                      {affectedApps.map(app => (
                        <button
                          key={app}
                          onClick={() => onFilterByApp && onFilterByApp(app)}
                          title={`Filter by ${app}`}
                          className="h-7 px-2.5 rounded-md border border-border text-xs font-medium capitalize hover:bg-muted transition-colors"
                        >
                          {app.replace(/-/g, ' ')}
                        </button>
                      ))}
                    </div>
                  )}
                  {isExpanded && (
                    <div className="pt-3 mt-1 border-t border-border">
                      <ChangelogViewer text={data.body} />
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
