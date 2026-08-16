"use client";

import { useState, useEffect } from "react";
import { Sparkles, Upload, Download, RefreshCw, Layers, FileText, Zap, ShieldCheck, FileCheck, Plus, Trash2 } from "lucide-react";

type ToolType = "remove-bg" | "upscale" | "document-clean" | "denoise" | "image-to-pdf";

interface ToolConfig {
  id: ToolType;
  title: string;
  desc: string;
  icon: any;
  endpointPath: string;
  isTransparent?: boolean;
  isPdf?: boolean;
}

const TOOLS: ToolConfig[] = [
  {
    id: "remove-bg",
    title: "BG Remover",
    desc: "Isolate foreground subjects with transparent alpha cutouts.",
    icon: Layers,
    endpointPath: "/api/vision/remove-bg",
    isTransparent: true,
  },
  {
    id: "upscale",
    title: "AI Upscaler (2x)",
    desc: "Lanczos super-resolution + adaptive unsharp edge mask.",
    icon: Sparkles,
    endpointPath: "/api/vision/upscale",
  },
  {
    id: "document-clean",
    title: "Doc Enhancer",
    desc: "Even out lighting shadows and boost text contrast.",
    icon: FileText,
    endpointPath: "/api/vision/document-clean",
  },
  {
    id: "denoise",
    title: "Denoise Studio",
    desc: "Fast bilateral filter to wipe noise without blurring edges.",
    icon: Zap,
    endpointPath: "/api/vision/denoise",
  },
  {
    id: "image-to-pdf",
    title: "Image to PDF",
    desc: "Convert single or multiple images into a compiled PDF.",
    icon: FileCheck,
    endpointPath: "/api/vision/image-to-pdf",
    isPdf: true,
  },
];

export default function Home() {
  const [activeTool, setActiveTool] = useState<ToolType>("remove-bg");
  const [selectedPreviews, setSelectedPreviews] = useState<string[]>([]);
  const [rawFiles, setRawFiles] = useState<File[]>([]);
  const [processedResultUrl, setProcessedResultUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendBaseUrl, setBackendBaseUrl] = useState("http://127.0.0.1:8000");

  useEffect(() => {
    // Auto-detect environment: Localhost vs Render Production
    if (typeof window !== "undefined") {
      if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
        setBackendBaseUrl("http://127.0.0.1:8000");
      } else {
        setBackendBaseUrl("https://ai-media-cleanup.onrender.com");
      }
    }
  }, []);

  const currentTool = TOOLS.find((t) => t.id === activeTool)!;

  const processFiles = async (files: File[], endpointPath: string) => {
    if (!files.length) return;
    setIsLoading(true);
    setError(null);
    setProcessedResultUrl(null);

    const formData = new FormData();
    if (activeTool === "image-to-pdf") {
      files.forEach((f) => formData.append("files", f));
    } else {
      formData.append("file", files[files.length - 1]);
    }

    try {
      const targetUrl = `${backendBaseUrl}${endpointPath}`;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout for initial cold starts

      const response = await fetch(targetUrl, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        throw new Error(errData.detail || `Server returned error ${response.status}`);
      }

      const blob = await response.blob();
      const outputUrl = URL.createObjectURL(blob);
      setProcessedResultUrl(outputUrl);
    } catch (err: any) {
      if (err.name === "AbortError") {
        setError("Request timed out. Backend may be waking up from free tier sleep, please retry in a few moments.");
      } else {
        setError(err.message || "Failed to process image.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleInitialUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (!files.length) return;

    setRawFiles(files);
    setSelectedPreviews(files.map((file) => URL.createObjectURL(file)));
    processFiles(files, currentTool.endpointPath);
  };

  const handleAddMore = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newFiles = e.target.files ? Array.from(e.target.files) : [];
    if (!newFiles.length) return;

    const updatedFiles = [...rawFiles, ...newFiles];
    const updatedPreviews = [...selectedPreviews, ...newFiles.map((f) => URL.createObjectURL(f))];

    setRawFiles(updatedFiles);
    setSelectedPreviews(updatedPreviews);
    processFiles(updatedFiles, currentTool.endpointPath);
  };

  const switchTool = (toolId: ToolType) => {
    setActiveTool(toolId);
    setSelectedPreviews([]);
    setRawFiles([]);
    setProcessedResultUrl(null);
    setError(null);
    setIsLoading(false);
  };

  const clearSelection = () => {
    setSelectedPreviews([]);
    setRawFiles([]);
    setProcessedResultUrl(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-6">
      <div className="max-w-4xl w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl space-y-6">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full text-xs font-semibold uppercase tracking-wider">
            <ShieldCheck className="w-3.5 h-3.5" /> High-Performance Vision Engine
          </div>
          <h1 className="text-3xl font-bold tracking-tight">AI Media Cleanup Studio</h1>
          <p className="text-slate-400 text-sm">{currentTool.desc}</p>
        </div>

        {/* Tool Switcher Tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 bg-slate-950/60 p-1.5 rounded-2xl border border-slate-800">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            const isActive = activeTool === tool.id;
            return (
              <button
                key={tool.id}
                onClick={() => switchTool(tool.id)}
                className={`flex items-center justify-center gap-2 py-2.5 px-2 rounded-xl text-xs font-medium transition ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{tool.title}</span>
              </button>
            );
          })}
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-xs text-center font-medium">
            {error}
          </div>
        )}

        {/* Upload Zone */}
        {selectedPreviews.length === 0 ? (
          <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-800 hover:border-indigo-500 rounded-2xl p-14 cursor-pointer transition bg-slate-950/40 hover:bg-slate-800/30">
            <Upload className="w-10 h-10 text-slate-400 mb-3" />
            <span className="font-medium text-slate-200">
              Upload Image for {currentTool.title}
            </span>
            <span className="text-xs text-slate-500 mt-1">PNG, JPG, WEBP (Supports multiple images)</span>
            <input
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={handleInitialUpload}
            />
          </label>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Input Previews */}
              <div className="bg-slate-950 rounded-2xl p-3.5 border border-slate-800 text-center flex flex-col justify-between">
                <div className="flex items-center justify-between px-1 mb-2">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Input ({selectedPreviews.length} File{selectedPreviews.length > 1 ? "s" : ""})
                  </span>
                  <button
                    onClick={clearSelection}
                    className="text-[11px] text-red-400 hover:text-red-300 inline-flex items-center gap-1 transition"
                  >
                    <Trash2 className="w-3 h-3" /> Clear
                  </button>
                </div>

                <div className="flex-1 flex items-center justify-center min-h-[220px] max-h-72 overflow-y-auto gap-2 flex-wrap p-2 border border-slate-800/50 rounded-xl bg-slate-900/40">
                  {selectedPreviews.map((src, i) => (
                    <img key={i} src={src} alt={`Input ${i}`} className="max-h-28 rounded-lg object-contain border border-slate-800 bg-slate-950 p-1" />
                  ))}
                </div>
              </div>

              {/* Processed Output */}
              <div className="bg-slate-950 rounded-2xl p-3.5 border border-slate-800 text-center flex flex-col justify-between relative min-h-[260px]">
                <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider block mb-2">
                  {currentTool.title} Output
                </span>
                
                <div className="flex-1 flex items-center justify-center">
                  {isLoading ? (
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin" />
                      <span className="text-xs text-slate-400">Processing...</span>
                    </div>
                  ) : processedResultUrl ? (
                    currentTool.isPdf ? (
                      <div className="flex flex-col items-center justify-center gap-3 p-6">
                        <FileCheck className="w-14 h-14 text-emerald-400" />
                        <span className="text-xs text-slate-300 font-medium">PDF Ready ({rawFiles.length} page{rawFiles.length > 1 ? "s" : ""})</span>
                      </div>
                    ) : (
                      <div
                        className={`rounded-lg p-2 ${
                          currentTool.isTransparent
                            ? "bg-[linear-gradient(45deg,#1e293b_25%,transparent_25%),linear-gradient(-45deg,#1e293b_25%,transparent_25%),linear-gradient(45deg,transparent_75%,#1e293b_75%),linear-gradient(-45deg,transparent_75%,#1e293b_75%)] bg-[size:16px_16px]"
                            : ""
                        }`}
                      >
                        <img src={processedResultUrl} alt="Processed" className="max-h-72 mx-auto object-contain rounded" />
                      </div>
                    )
                  ) : null}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-2">
                <label className="px-4 py-2.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-xl cursor-pointer text-xs font-medium transition inline-flex items-center gap-2">
                  <Plus className="w-3.5 h-3.5" /> Add More Images
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={handleAddMore}
                  />
                </label>

                <label className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl cursor-pointer text-xs font-medium transition inline-flex items-center gap-2">
                  <Upload className="w-3.5 h-3.5" /> Replace All
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={handleInitialUpload}
                  />
                </label>
              </div>

              {processedResultUrl && (
                <a
                  href={processedResultUrl}
                  download={currentTool.isPdf ? "converted_document.pdf" : `${activeTool}-result.png`}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-semibold transition inline-flex items-center gap-2 shadow-lg shadow-indigo-600/20"
                >
                  <Download className="w-3.5 h-3.5" /> Download {currentTool.isPdf ? "PDF" : "Result"}
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}