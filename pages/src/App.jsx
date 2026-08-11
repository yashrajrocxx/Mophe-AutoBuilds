import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { StorePage } from './pages/StorePage';
import { LogsPage } from './pages/LogsPage';

function App() {
  const [activeTab, setActiveTab] = useState('store');

  return (
    <div className="flex h-[100dvh] w-screen bg-background text-foreground overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 h-full overflow-y-auto">
        {activeTab === 'store' && <StorePage />}
        {activeTab === 'logs' && <LogsPage />}
        {activeTab === 'settings' && (
          <div className="p-8 w-full h-full flex items-center justify-center text-muted-foreground">
            Settings module not yet implemented.
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
