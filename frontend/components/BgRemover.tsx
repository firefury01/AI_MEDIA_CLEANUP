'use client';

import { useState } from 'react';
import { Upload, Download, RefreshCw, Sparkles, AlertCircle } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function BgRemover() {
  const [originalImage, setOriginalImage] = useState<string | null>(null);
  const [cleanedImage, setCleanedImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setOriginalImage(URL.createObjectURL(file));
    setCleanedImage(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE_URL}/api/remove-bg`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Background removal failed on server');

      const blob = await res.blob();
      setCleanedImage(URL.createObjectURL(blob));
    } catch (err) {
      setError('Error processing image. Ensure backend server is active on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 w-full">
      {error && (
        <div className="w-full p-3.5 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl flex items-center gap-2">
          <AlertCircle size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!originalImage ? (
        <label className="w-full flex flex-col items-center justify-center p-10 border-2 border-dashed border-slate-300 rounded-2xl cursor-pointer hover:bg-slate-50 transition">
          <Upload size={32} className="text-slate-400 mb-2" />
          <span className="font-semibold text-slate-700">Upload an image to isolate subject</span>
          <span className="text-xs text-slate-400 mt-1">PNG, JPG, or WebP</span>
          <input type="file" accept="image/*" className="hidden" onChange={handleFileUpload} />
        </label>
      ) : (
        <div className="w-full flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Original Input */}
            <div className="flex flex-col items-center gap-2">
              <span className="text-xs font-semibold uppercase text-slate-500 tracking-wider">Original</span>
              <div className="w-full h-64 bg-slate-100 rounded-xl overflow-hidden flex items-center justify-center border border-slate-200 p-2">
                <img src={originalImage} alt="Original" className="max-h-full max-w-full object-contain rounded" />
              </div>
            </div>

            {/* Segmented Result */}
            <div className="flex flex-col items-center gap-2">
              <span className="text-xs font-semibold uppercase text-indigo-600 tracking-wider flex items-center gap-1">
                <Sparkles size={14} /> Transparent Result
              </span>
              <div
                className="w-full h-64 rounded-xl overflow-hidden flex items-center justify-center border border-slate-200 p-2 relative"
                style={{
                  backgroundImage: `linear-gradient(45deg, #cbd5e1 25%, transparent 25%), 
                                    linear-gradient(-45deg, #cbd5e1 25%, transparent 25%), 
                                    linear-gradient(45deg, transparent 75%, #cbd5e1 75%), 
                                    linear-gradient(-45deg, transparent 75%, #cbd5e1 75%)`,
                  backgroundSize: '16px 16px',
                  backgroundPosition: '0 0, 0 8px, 8px -8px, -8px 0px',
                }}
              >
                {loading && (
                  <div className="flex items-center gap-2 text-indigo-600 bg-white/90 px-4 py-2 rounded-lg shadow-sm">
                    <RefreshCw className="animate-spin" size={18} />
                    <span className="text-sm font-medium">Extracting subject...</span>
                  </div>
                )}
                {cleanedImage && !loading && (
                  <img src={cleanedImage} alt="Transparent cutout" className="max-h-full max-w-full object-contain" />
                )}
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => {
                setOriginalImage(null);
                setCleanedImage(null);
              }}
              className="flex-1 py-2.5 border border-slate-300 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition"
            >
              Upload Another
            </button>
            {cleanedImage && (
              <a
                href={cleanedImage}
                download="transparent_output.png"
                className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium flex items-center justify-center gap-2 shadow-sm transition"
              >
                <Download size={16} /> Download PNG
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
