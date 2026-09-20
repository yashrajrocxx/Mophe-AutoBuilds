import React from 'react';
import { LayoutGrid, ScrollText, Info } from 'lucide-react';

export function MobileNav({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'store', label: 'Store', icon: LayoutGrid },
    { id: 'logs', label: 'Logs', icon: ScrollText },
    { id: 'info', label: 'Info', icon: Info },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-background border-t border-border z-50">
      <div className="grid grid-cols-3 px-2 pb-[env(safe-area-inset-bottom)]">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              aria-current={isActive ? 'page' : undefined}
              className="relative flex flex-col items-center gap-1 py-2.5 text-muted-foreground transition-colors"
            >
              <span
                className={`absolute top-0 h-0.5 w-12 rounded-full transition-colors ${
                  isActive ? 'bg-foreground' : 'bg-transparent'
                }`}
              />
              <Icon
                size={20}
                className={isActive ? 'text-foreground' : 'text-muted-foreground'}
              />
              <span
                className={`text-[11px] ${
                  isActive ? 'text-foreground font-semibold' : 'font-medium'
                }`}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
