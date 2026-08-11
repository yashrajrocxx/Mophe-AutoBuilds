import React from 'react';
import { Layers, Activity, Settings, User } from 'lucide-react';

export function Sidebar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'store', label: 'App Store', icon: Layers },
    { id: 'logs', label: 'Build Logs', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-[280px] h-full flex flex-col bg-sidebar border-r border-border shrink-0 text-foreground transition-all duration-300">
      <div className="h-16 flex items-center px-6 border-b border-border">
        <h1 className="yr-brand text-2xl text-accent font-bold tracking-tight">morphe.</h1>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-1">
        <div className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-3 pt-2">Menu</div>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-[14.5px] font-medium transition-colors ${
                isActive 
                  ? 'bg-accent/10 text-accent' 
                  : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
              }`}
            >
              <Icon size={18} className={isActive ? 'text-accent' : 'opacity-70'} />
              {tab.label}
            </button>
          );
        })}
      </div>
      
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <User size={16} className="text-muted-foreground" />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-[13px] font-medium leading-tight">Admin</span>
            <span className="text-[12px] text-muted-foreground">Local User</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
