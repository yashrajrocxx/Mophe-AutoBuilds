import React from 'react';
import { LayoutGrid, ScrollText, Info, Sun, Moon, GitBranch } from 'lucide-react';

export function Sidebar({ activeTab, setActiveTab, theme, toggleTheme }) {
  const tabs = [
    { id: 'store', label: 'Store', icon: LayoutGrid },
    { id: 'logs', label: 'Build Logs', icon: ScrollText },
    { id: 'info', label: 'Info', icon: Info },
  ];

  return (
    <aside className="hidden md:flex w-60 h-full flex-col bg-sidebar border-r border-border shrink-0">
      {/* Brand */}
      <div className="h-16 flex items-center px-5 border-b border-border">
        <span className="text-xl font-bold tracking-tight">
          morphe<span className="text-muted-foreground">.</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider px-3 pb-1">
          Menu
        </p>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              aria-current={isActive ? 'page' : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-foreground text-background font-semibold'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground font-medium'
              }`}
            >
              <Icon size={17} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-border space-y-1">
        <button
          onClick={toggleTheme}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
        </button>
        <a
          href="https://github.com/yashrajrocxx/Mophe-AutoBuilds"
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <GitBranch size={17} />
          <span>Repository</span>
        </a>
      </div>
    </aside>
  );
}
