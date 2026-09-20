import React from 'react';
import { GitBranch, Smartphone, RefreshCw, FileJson, ExternalLink } from 'lucide-react';

const PIPELINE_STEPS = [
  { title: 'Check', text: 'Upstream patch releases and app versions are compared against the manifest every day.' },
  { title: 'Download', text: 'Base APKs come from Google Play, APKMirror, Uptodown, APKPure, APKCombo, Aptoide, GitHub, or a pinned manual link.' },
  { title: 'Patch', text: 'Morphe / ReVanced toolchains apply the per-app patch list, then the APK is signed and published.' },
  { title: 'Track', text: 'Obtainium follows the GitHub release per app and installs updates in the background.' },
];

export function InfoPage() {
  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-3xl mx-auto w-full fade-up space-y-5">
      <div className="pb-5 border-b border-border">
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Info</h2>
        <p className="text-muted-foreground text-[13px] sm:text-sm mt-1">
          Automated patched Android builds for non-rooted devices.
        </p>
      </div>

      <section className="bg-card rounded-xl border border-border p-5">
        <h3 className="text-[15px] font-bold mb-3">How it works</h3>
        <ol className="space-y-3">
          {PIPELINE_STEPS.map((s, i) => (
            <li key={s.title} className="flex gap-3">
              <span className="w-6 h-6 rounded-md bg-muted font-mono text-xs font-bold flex items-center justify-center shrink-0">
                {i + 1}
              </span>
              <div>
                <p className="text-sm font-semibold">{s.title}</p>
                <p className="text-[13px] text-muted-foreground">{s.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="bg-card rounded-xl border border-border p-5">
        <h3 className="text-[15px] font-bold mb-1 flex items-center gap-2">
          <Smartphone size={15} />
          Auto-update with Obtainium
        </h3>
        <p className="text-[13px] text-muted-foreground mb-3">
          Import the catalog once — every app then updates itself from new releases.
        </p>
        <code className="block text-xs font-mono bg-muted rounded-lg p-3 break-all">
          https://raw.githubusercontent.com/yashrajrocxx/Mophe-AutoBuilds/main/obtainium.json
        </code>
      </section>

      <section className="bg-card rounded-xl border border-border p-5">
        <h3 className="text-[15px] font-bold mb-3 flex items-center gap-2">
          <FileJson size={15} />
          Data files
        </h3>
        <div className="space-y-2 text-[13px]">
          {[
            { f: 'manifest.json', d: 'Every published build: versions, patch tags, changelogs.' },
            { f: 'build_report.json', d: 'Latest pipeline run, per app and architecture.' },
            { f: 'patch_changelogs.json', d: 'Upstream patch release notes.' },
            { f: 'patch_lists.json', d: 'Included / excluded patches per app.' },
            { f: 'obtainium.json', d: 'Bulk import for Obtainium.' },
          ].map(r => (
            <div key={r.f} className="flex flex-col sm:flex-row sm:items-baseline gap-0.5 sm:gap-3">
              <code className="font-mono text-xs font-semibold shrink-0 sm:w-40">{r.f}</code>
              <span className="text-muted-foreground">{r.d}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-card rounded-xl border border-border p-5">
        <h3 className="text-[15px] font-bold mb-3">Links</h3>
        <div className="flex flex-col gap-1">
          {[
            { icon: <GitBranch size={15} />, label: 'GitHub repository', href: 'https://github.com/yashrajrocxx/Mophe-AutoBuilds' },
            { icon: <RefreshCw size={15} />, label: 'Latest release', href: 'https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/latest' },
          ].map(l => (
            <a
              key={l.label}
              href={l.href}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between h-11 px-3 rounded-lg hover:bg-muted transition-colors text-sm font-medium"
            >
              <span className="flex items-center gap-2.5">
                {l.icon}
                {l.label}
              </span>
              <ExternalLink size={14} className="text-muted-foreground" />
            </a>
          ))}
        </div>
      </section>

      <p className="text-xs text-muted-foreground pb-4">
        Unofficial community builds for convenience only. Use at your own risk.
      </p>
    </div>
  );
}
