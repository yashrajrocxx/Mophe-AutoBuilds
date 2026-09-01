import React from 'react';
import { Layers, Activity, Settings, GitBranch, ExternalLink } from 'lucide-react';

export function Sidebar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'store', label: 'App Store', icon: Layers },
    { id: 'logs', label: 'Build Logs', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="hidden md:flex w-56 lg:w-64 h-full flex-col bg-card/40 backdrop-blur-xl border-r border-border/70 shrink-0 text-foreground transition-all duration-300 z-50">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-border/60">
        <h1 className="yr-brand text-2xl text-accent font-extrabold tracking-tight">morphe.</h1>
      </div>
      
      {/* Navigation Items */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1.5">
        <div className="text-[10.5px] font-bold text-muted-foreground/70 uppercase tracking-widest px-3 py-1">
          Menu
        </div>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                isActive 
                  ? 'bg-accent text-white shadow-xs' 
                  : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
              }`}
            >
              <Icon size={16} className={isActive ? 'text-white' : 'opacity-70'} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-border/60 text-xs text-muted-foreground space-y-2">
        <a
          href="https://github.com/yashrajrocxx/Mophe-AutoBuilds"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between p-2 rounded-lg bg-muted/40 hover:bg-muted text-foreground transition-colors"
        >
          <div className="flex items-center gap-2">
            <GitBranch size={14} />
            <span className="font-medium text-xs">Repository</span>
          </div>
          <ExternalLink size={12} className="opacity-60" />
        </a>
      </div>
    </aside>
  );
}
