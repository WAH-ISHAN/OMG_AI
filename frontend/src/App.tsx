import React, { useState, useEffect } from 'react';

function App() {
  const [status, setStatus] = useState('Initializing...');

  useEffect(() => {
    // Ping backend status
    fetch('http://127.0.0.1:8000/status')
      .then(res => res.json())
      .then(data => setStatus(`Backend Status: ${data.status.toUpperCase()} (v${data.version})`))
      .catch(err => setStatus('Backend disconnected'));
  }, []);

  return (
    <div className="w-screen h-screen flex flex-col bg-black/60 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden font-sans text-white relative">
      {/* Draggable header area for PyWebView */}
      <div className="h-10 w-full flex items-center justify-between px-4" style={{ WebkitAppRegion: 'drag' } as any}>
        <div className="text-sm font-semibold opacity-70 tracking-widest">OMG_AI V10</div>
        <div className="w-3 h-3 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
      </div>

      {/* Main Avatar / Orb Area */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="w-32 h-32 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 animate-pulse shadow-[0_0_40px_rgba(139,92,246,0.6)] flex items-center justify-center relative group cursor-pointer transition-transform hover:scale-105">
          <div className="absolute inset-2 rounded-full bg-black/40 backdrop-blur-sm z-10 flex items-center justify-center">
            <span className="text-xs font-mono opacity-50">IDLE</span>
          </div>
        </div>
        
        <div className="mt-8 text-center space-y-2">
          <p className="text-xl font-medium tracking-tight">Good evening, Sir.</p>
          <p className="text-sm text-gray-400 font-mono">{status}</p>
        </div>
      </div>

      {/* Chat / Input Panel */}
      <div className="p-4 bg-black/40 border-t border-white/5">
        <div className="relative">
          <input 
            type="text" 
            placeholder="Ask me anything..." 
            className="w-full bg-white/5 border border-white/10 rounded-full px-6 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-gray-500"
          />
          <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
