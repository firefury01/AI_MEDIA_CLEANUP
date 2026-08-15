'use client';

import { Mic, Image as ImageIcon } from 'lucide-react';

interface TabSelectorProps {
  activeTab: 'audio' | 'image';
  onTabChange: (tab: 'audio' | 'image') => void;
}

export default function TabSelector({ activeTab, onTabChange }: TabSelectorProps) {
  return (
    <div className="flex bg-slate-100 p-1.5 rounded-xl mb-8 w-full max-w-sm mx-auto">
      <button
        onClick={() => onTabChange('audio')}
        className={`flex-1 py-2.5 rounded-lg text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
          activeTab === 'audio'
            ? 'bg-white shadow text-indigo-600'
            : 'text-slate-500 hover:text-slate-900'
        }`}
      >
        <Mic size={16} /> Audio Denoiser
      </button>
      <button
        onClick={() => onTabChange('image')}
        className={`flex-1 py-2.5 rounded-lg text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
          activeTab === 'image'
            ? 'bg-white shadow text-indigo-600'
            : 'text-slate-500 hover:text-slate-900'
        }`}
      >
        <ImageIcon size={16} /> BG Remover
      </button>
    </div>
  );
}
