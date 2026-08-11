import React from 'react';
import { Layers, Activity, Settings } from 'lucide-react';

export function Sidebar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'store', label: 'App Store', icon: Layers },
    { id: 'logs', label: 'Build Logs', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-16 md:w-[280px] h-full flex flex-col bg-sidebar border-r border-border shrink-0 text-foreground transition-all duration-300 z-50">
      <div className="h-16 flex items-center justify-center md:justify-start md:px-6 border-b border-border">
        <h1 className="yr-brand hidden md:block text-2xl text-accent font-bold tracking-tight">morphe.</h1>
        <h1 className="yr-brand md:hidden text-2xl text-accent font-bold tracking-tight">m.</h1>
      </div>
      
      <div className="flex-1 overflow-y-auto py-4 px-2 md:px-4 space-y-2">
        <div className="hidden md:block text-[12px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-3 pt-2">Menu</div>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              title={tab.label}
              className={`w-full flex items-center justify-center md:justify-start gap-3 p-3 md:px-3 md:py-2 rounded-md text-[14.5px] font-medium transition-colors ${
                isActive 
                  ? 'bg-accent/10 text-accent' 
                  : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
              }`}
            >
              <Icon size={20} className={isActive ? 'text-accent' : 'opacity-70'} />
              <span className="hidden md:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
