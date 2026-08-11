import React, { useState, useEffect } from 'react';
import { FileCode2, Zap, AlertTriangle, PlayCircle, Settings2, Hash } from 'lucide-react';

export function LogsPage() {
  const [reports, setReports] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}build_report.json`)
      .then(res => res.json())
      .then(data => {
        setReports(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch reports:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 yr-fade-up">
          <div className="w-8 h-8 rounded-full border-2 border-accent border-t-transparent animate-spin" />
          <p className="text-muted-foreground text-sm font-medium">Fetching build telemetry...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto w-full yr-fade-up">
      <div className="mb-10">
        <h2 className="text-3xl font-semibold mb-2">Build Telemetry</h2>
        <p className="text-muted-foreground text-[15px]">Detailed logs of the patching process and global patch injections.</p>
      </div>

      {!reports || reports.length === 0 ? (
        <div className="text-center p-12 bg-muted/20 border border-border rounded-xl">
          <FileCode2 className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-1">No telemetry found</h3>
          <p className="text-muted-foreground text-sm">Awaiting the next CI/CD build cycle.</p>
        </div>
      ) : (
        <div className="space-y-8 relative before:absolute before:inset-0 before:ml-6 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
          {reports.map((report, idx) => (
            <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
              {/* Icon / Node */}
              <div className="flex items-center justify-center w-12 h-12 rounded-full border-4 border-background bg-muted text-muted-foreground shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-colors group-[.is-active]:bg-accent group-[.is-active]:text-white">
                {report.status === 'success' ? <PlayCircle size={20} /> : <AlertTriangle size={20} />}
              </div>
              
              {/* Card */}
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] p-5 rounded-xl border border-border bg-background shadow-sm hover:shadow-md transition-shadow relative">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-lg capitalize">{report.app}</span>
                    <span className="px-2 py-0.5 rounded bg-muted text-[11px] font-bold uppercase tracking-wider text-muted-foreground">{report.arch}</span>
                  </div>
                  {report.status === 'success' ? (
                    <span className="text-[11px] font-medium px-2 py-1 bg-emerald-500/10 text-emerald-500 rounded-md">SUCCESS</span>
                  ) : (
                    <span className="text-[11px] font-medium px-2 py-1 bg-rose-500/10 text-rose-500 rounded-md">FAILED</span>
                  )}
                </div>
                
                <div className="space-y-3 mt-4 text-sm">
                  <div className="flex items-start gap-3 text-muted-foreground">
                    <Settings2 size={16} className="mt-0.5 shrink-0" />
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">Source & Version</span>
                      <span>{report.source} • v{report.version || 'Unknown'}</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 text-muted-foreground">
                    <Zap size={16} className="mt-0.5 shrink-0 text-amber-500" />
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">Injected Patches</span>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {report.patches && report.patches.length > 0 ? (
                          report.patches.filter(p => p !== '-e').map((patch, i) => (
                            <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-accent/10 text-accent text-[11px] font-medium border border-accent/20">
                              <Hash size={10} />
                              {patch}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs opacity-60 italic">No global patches applied</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
