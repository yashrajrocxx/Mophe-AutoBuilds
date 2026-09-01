import React from 'react';
import { Layers, Activity, Settings } from 'lucide-react';

export function MobileNav({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'store', label: 'App Store', icon: Layers },
    { id: 'logs', label: 'Build Logs', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-14 bg-card/95 backdrop-blur-xl border-t border-border/70 flex items-center justify-around px-4 z-50 shadow-lg">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex flex-col items-center justify-center gap-1 py-1 px-3 rounded-xl transition-all ${
              isActive ? 'text-accent font-bold' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Icon size={18} className={isActive ? 'text-accent stroke-[2.5]' : 'opacity-70'} />
            <span className="text-[10px] tracking-tight">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
