import React, { useState, useEffect } from 'react';
import { Sun, Moon, GitBranch } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { MobileNav } from './components/MobileNav';
import { StorePage } from './pages/StorePage';
import { LogsPage } from './pages/LogsPage';
import { InfoPage } from './pages/InfoPage';

function App() {
  const [activeTab, setActiveTab] = useState('store');
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('morphe-theme') || 'light';
    } catch {
      return 'light';
    }
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    try {
      localStorage.setItem('morphe-theme', theme);
    } catch {
      /* storage unavailable */
    }
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  return (
    <div className="flex h-[100dvh] w-screen bg-background text-foreground overflow-hidden font-sans">
      {/* Desktop sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        theme={theme}
        toggleTheme={toggleTheme}
      />

      {/* Content column (mobile header + scrollable page) */}
      <div className="flex-1 h-full flex flex-col min-w-0">
        {/* Mobile top bar */}
        <header className="md:hidden shrink-0 h-14 flex items-center justify-between px-4 border-b border-border bg-background">
          <button
            onClick={() => setActiveTab('store')}
            className="text-lg font-bold tracking-tight"
            aria-label="Morphe Builds home"
          >
            morphe<span className="text-muted-foreground">.</span>
          </button>
          <div className="flex items-center gap-1">
            <button
              onClick={toggleTheme}
              className="w-9 h-9 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
            </button>
            <a
              href="https://github.com/yashrajrocxx/Mophe-AutoBuilds"
              target="_blank"
              rel="noopener noreferrer"
              className="w-9 h-9 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="GitHub repository"
            >
              <GitBranch size={17} />
            </a>
          </div>
        </header>

        <main className="flex-1 h-full overflow-y-auto pb-20 md:pb-0">
          {activeTab === 'store' && <StorePage />}
          {activeTab === 'logs' && <LogsPage />}
          {activeTab === 'info' && <InfoPage />}
        </main>
      </div>

      {/* Mobile bottom navigation */}
      <MobileNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}

export default App;
