'use client';

import { useState } from 'react';
import { Sparkles } from 'lucide-react';
import TabSelector from '@/components/TabSelector';
import AudioCleaner from '@/components/AudioCleaner';
import BgRemover from '@/components/BgRemover';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'audio' | 'image'>('audio');

  return (
    <main className="min-h-screen bg-slate-950 flex flex-col items-center justify-center py-12 px-4">
      <div className="w-full max-w-xl bg-white text-slate-900 rounded-3xl shadow-2xl p-8 border border-slate-100">
        
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center p-3 bg-indigo-50 text-indigo-600 rounded-2xl mb-3">
            <Sparkles size={26} />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">AI Media Cleanup Studio</h1>
          <p className="text-slate-500 text-sm mt-1">
            Instantly remove background noise from voice or extract subjects from images.
          </p>
        </div>

        {/* Tab Switcher */}
        <TabSelector activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Dynamic Tool Render */}
        {activeTab === 'audio' ? <AudioCleaner /> : <BgRemover />}

      </div>
    </main>
  );
}