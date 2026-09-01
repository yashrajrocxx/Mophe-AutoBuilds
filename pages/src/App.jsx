import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { MobileNav } from './components/MobileNav';
import { StorePage } from './pages/StorePage';
import { LogsPage } from './pages/LogsPage';

function App() {
  const [activeTab, setActiveTab] = useState('store');

  return (
    <div className="flex h-[100dvh] w-screen bg-background text-foreground overflow-hidden font-sans">
      {/* Desktop Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-y-auto pb-16 md:pb-0 scroll-smooth">
        {activeTab === 'store' && <StorePage />}
        {activeTab === 'logs' && <LogsPage />}
        {activeTab === 'settings' && (
          <div className="p-8 w-full h-full flex flex-col items-center justify-center text-muted-foreground gap-2">
            <h3 className="text-base font-semibold text-foreground">Settings</h3>
            <p className="text-xs">Preferences and telemetry configurations.</p>
          </div>
        )}
      </main>

      {/* Mobile Bottom Navigation Bar */}
      <MobileNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}

export default App;
