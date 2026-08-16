"use client";

import { useState, useEffect } from "react";
import {
  Sparkles,
  Upload,
  Download,
  Layers,
  FileText,
  Zap,
  ShieldCheck,
  FileCheck,
  Plus,
  Trash2,
  Minimize2,
  PenTool,
  UserCheck,
  SlidersHorizontal,
  ArrowRightLeft,
  CheckCircle2,
} from "lucide-react";

type ToolType =
  | "remove-bg"
  | "upscale"
  | "document-clean"
  | "denoise"
  | "compress-kb"
  | "signature-extract"
  | "passport-maker"
  | "image-to-pdf";

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
    id: "compress-kb",
    title: "Target KB Reducer",
    desc: "Compress images down to strict 20KB, 50KB, or 100KB limits.",
    icon: Minimize2,
    endpointPath: "/api/vision/compress-kb",
  },
  {
    id: "signature-extract",
    title: "Signature Extractor",
    desc: "Remove paper background & shadows to get clean transparent signatures.",
    icon: PenTool,
    endpointPath: "/api/vision/signature-extract",
    isTransparent: true,
  },
  {
    id: "passport-maker",
    title: "Passport Photo",
    desc: "Crop to 3.5x4.5cm ratio with clean White / Blue background.",
    icon: UserCheck,
    endpointPath: "/api/vision/passport-maker",
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
  const [processedSize, setProcessedSize] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState<string>("Analyzing image...");
  const [error, setError] = useState<string | null>(null);
  
  // Default to Render URL to avoid Next.js domain 404
  const [backendBaseUrl, setBackendBaseUrl] = useState("https://ai-media-cleanup-1.onrender.com/");

  // Options & Comparison
  const [targetKb, setTargetKb] = useState<number>(50);
  const [passportBgColor, setPassportBgColor] = useState<string>("white");
  const [sliderPos, setSliderPos] = useState<number>(50);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<"slider" | "side-by-side">("slider");

  useEffect(() => {
    if (typeof window !== "undefined") {
      if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
        setBackendBaseUrl("http://127.0.0.1:8000");
      } else {
        setBackendBaseUrl("https://ai-media-cleanup-1.onrender.com/");
      }
    }
  }, []);

  const currentTool = TOOLS.find((t) => t.id === activeTool)!;

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const processFiles = async (
    files: File[],
    endpointPath: string,
    opts?: { kb?: number; bg?: string }
  ) => {
    if (!files.length) return;
    setIsLoading(true);
    setError(null);
    setProcessedResultUrl(null);
    setProcessedSize(null);

    setLoadingStep("Uploading image payload...");
    const timer1 = setTimeout(() => setLoadingStep("Running computer vision pipeline..."), 1200);
    const timer2 = setTimeout(() => setLoadingStep("Enhancing & rendering output..."), 3500);

    const formData = new FormData();
    if (activeTool === "image-to-pdf") {
      files.forEach((f) => formData.append("files", f));
    } else {
      formData.append("file", files[files.length - 1]);
    }

    if (activeTool === "compress-kb") {
      formData.append("target_kb", String(opts?.kb ?? targetKb));
    } else if (activeTool === "passport-maker") {
      formData.append("bg_color", opts?.bg ?? passportBgColor);
    }

    try {
      const activeBase = (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"))
        ? "http://127.0.0.1:8000"
        : "https://ai-media-cleanup-1.onrender.com";

      const targetUrl = `${activeBase}${endpointPath}`;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      const response = await fetch(targetUrl, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      clearTimeout(timer1);
      clearTimeout(timer2);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        throw new Error(errData.detail || `Server returned error ${response.status}`);
      }

      const blob = await response.blob();
      setProcessedSize(formatFileSize(blob.size));
      const outputUrl = URL.createObjectURL(blob);
      setProcessedResultUrl(outputUrl);
    } catch (err: any) {
      if (err.name === "AbortError") {
        setError("Request timed out. Backend free-tier is waking up, please retry in 10-15 seconds.");
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

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files ? Array.from(e.dataTransfer.files) : [];
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
    setProcessedSize(null);
    setError(null);
    setIsLoading(false);
  };

  const clearSelection = () => {
    setSelectedPreviews([]);
    setRawFiles([]);
    setProcessedResultUrl(null);
    setProcessedSize(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 sm:p-8 relative overflow-hidden">
      {/* Ambient Glassmorphism Backlight */}
      <div className="absolute top-1/4 -left-20 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-5xl w-full bg-slate-900/70 backdrop-blur-xl border border-slate-800/80 rounded-3xl p-6 sm:p-8 shadow-[0_0_60px_-15px_rgba(79,70,229,0.2)] space-y-6 relative z-10">
        
        {/* Top Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full text-xs font-semibold uppercase tracking-wider backdrop-blur-sm">
            <ShieldCheck className="w-3.5 h-3.5" /> High-Performance Vision Engine
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
            AI Media Cleanup Studio
          </h1>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">{currentTool.desc}</p>
        </div>

        {/* Tool Navigation Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-950/70 p-1.5 rounded-2xl border border-slate-800/80">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            const isActive = activeTool === tool.id;
            return (
              <button
                key={tool.id}
                onClick={() => switchTool(tool.id)}
                className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-xs font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 ring-1 ring-indigo-400/40"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{tool.title}</span>
              </button>
            );
          })}
        </div>

        {/* Dynamic Controls Strip */}
        {activeTool === "compress-kb" && (
          <div className="flex flex-wrap items-center justify-center gap-3 bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/60">
            <span className="text-xs text-slate-300 font-medium flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-400" /> Target Limit:
            </span>
            <div className="flex items-center gap-1.5">
              {[20, 50, 100, 200].map((kb) => (
                <button
                  key={kb}
                  onClick={() => {
                    setTargetKb(kb);
                    if (rawFiles.length > 0) processFiles(rawFiles, currentTool.endpointPath, { kb });
                  }}
                  className={`px-3 py-1 text-xs rounded-lg font-medium transition ${
                    targetKb === kb
                      ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                      : "bg-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {kb} KB
                </button>
              ))}
            </div>
          </div>
        )}

        {activeTool === "passport-maker" && (
          <div className="flex items-center justify-center gap-3 bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/60">
            <span className="text-xs text-slate-300 font-medium">Background Color:</span>
            <div className="flex items-center gap-2">
              {["white", "blue"].map((bg) => (
                <button
                  key={bg}
                  onClick={() => {
                    setPassportBgColor(bg);
                    if (rawFiles.length > 0) processFiles(rawFiles, currentTool.endpointPath, { bg });
                  }}
                  className={`px-4 py-1 text-xs capitalize rounded-lg font-medium transition flex items-center gap-1.5 ${
                    passportBgColor === bg
                      ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                      : "bg-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <span className={`w-2.5 h-2.5 rounded-full border border-slate-600 ${bg === "white" ? "bg-white" : "bg-sky-400"}`} />
                  {bg}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-xs text-center font-medium">
            {error}
          </div>
        )}

        {/* Upload Zone */}
        {selectedPreviews.length === 0 ? (
          <label
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`flex flex-col items-center justify-center border-2 border-dashed rounded-3xl p-14 cursor-pointer transition-all duration-300 ${
              isDragging
                ? "border-indigo-500 bg-indigo-600/10 scale-[1.01]"
                : "border-slate-800 hover:border-indigo-500/60 bg-slate-950/50 hover:bg-slate-900/40"
            }`}
          >
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mb-4 shadow-inner">
              <Upload className="w-7 h-7 text-indigo-400" />
            </div>
            <span className="font-semibold text-slate-100 text-base">
              Drop image here or click to browse
            </span>
            <span className="text-xs text-slate-400 mt-1">
              Supports PNG, JPG, WEBP • Max 20MB
            </span>
            <input
              type="file"
              accept="image/*"
              multiple={activeTool === "image-to-pdf"}
              className="hidden"
              onChange={handleInitialUpload}
            />
          </label>
        ) : (
          <div className="space-y-6">
            {/* View Mode Toggle for Single Image Output */}
            {!currentTool.isPdf && processedResultUrl && (
              <div className="flex justify-end gap-2 text-xs">
                <button
                  onClick={() => setViewMode(viewMode === "slider" ? "side-by-side" : "slider")}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg inline-flex items-center gap-1.5 transition"
                >
                  <ArrowRightLeft className="w-3.5 h-3.5 text-indigo-400" />
                  {viewMode === "slider" ? "Side by Side View" : "Comparison Slider"}
                </button>
              </div>
            )}

            {/* Split Comparison Slider / Grid */}
            {!currentTool.isPdf && processedResultUrl && viewMode === "slider" ? (
              <div className="bg-slate-950 rounded-2xl p-4 border border-slate-800 relative">
                <div className="relative w-full max-h-[380px] h-[340px] overflow-hidden rounded-xl select-none flex items-center justify-center bg-slate-900">
                  {/* Original Image (Left Side) */}
                  <img
                    src={selectedPreviews[0]}
                    alt="Original"
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                  />
                  <div className="absolute top-3 left-3 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-md text-[10px] font-semibold text-slate-300 border border-slate-800">
                    Original ({rawFiles[0] ? formatFileSize(rawFiles[0].size) : ""})
                  </div>

                  {/* Processed Image (Right Side with Clip Path) */}
                  <div
                    className="absolute inset-0 w-full h-full overflow-hidden"
                    style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
                  >
                    <img
                      src={processedResultUrl}
                      alt="Processed"
                      className={`w-full h-full object-contain pointer-events-none ${
                        currentTool.isTransparent
                          ? "bg-[linear-gradient(45deg,#1e293b_25%,transparent_25%),linear-gradient(-45deg,#1e293b_25%,transparent_25%),linear-gradient(45deg,transparent_75%,#1e293b_75%),linear-gradient(-45deg,transparent_75%,#1e293b_75%)] bg-[size:16px_16px]"
                          : ""
                      }`}
                    />
                    <div className="absolute top-3 right-3 bg-indigo-600/90 backdrop-blur-md px-2.5 py-1 rounded-md text-[10px] font-semibold text-white border border-indigo-400/40">
                      Enhanced {processedSize ? `(${processedSize})` : ""}
                    </div>
                  </div>

                  {/* Vertical Divider Handle */}
                  <div
                    className="absolute top-0 bottom-0 w-1 bg-white shadow-[0_0_10px_rgba(255,255,255,0.7)] pointer-events-none"
                    style={{ left: `${sliderPos}%` }}
                  >
                    <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-7 h-7 bg-white text-slate-900 rounded-full shadow-lg flex items-center justify-center text-[10px] font-bold">
                      ↔
                    </div>
                  </div>

                  {/* Native Range Drag Track */}
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={sliderPos}
                    onChange={(e) => setSliderPos(Number(e.target.value))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
                  />
                </div>
              </div>
            ) : (
              /* Standard Side-by-Side Dual View */
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Input Previews */}
                <div className="bg-slate-950 rounded-2xl p-4 border border-slate-800 flex flex-col justify-between">
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
                      <img
                        key={i}
                        src={src}
                        alt={`Input ${i}`}
                        className="max-h-28 rounded-lg object-contain border border-slate-800 bg-slate-950 p-1"
                      />
                    ))}
                  </div>
                </div>

                {/* Output Screen */}
                <div className="bg-slate-950 rounded-2xl p-4 border border-slate-800 flex flex-col justify-between relative min-h-[260px]">
                  <div className="flex items-center justify-between px-1 mb-2">
                    <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">
                      {currentTool.title} Output
                    </span>
                    {processedSize && (
                      <span className="text-[10px] px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded font-medium">
                        {processedSize}
                      </span>
                    )}
                  </div>

                  <div className="flex-1 flex items-center justify-center">
                    {isLoading ? (
                      <div className="flex flex-col items-center justify-center space-y-3 p-8">
                        <div className="relative">
                          <div className="w-12 h-12 rounded-full border-2 border-indigo-500/20 border-t-indigo-500 animate-spin" />
                          <Sparkles className="w-4 h-4 text-indigo-400 absolute inset-0 m-auto animate-pulse" />
                        </div>
                        <span className="text-xs text-slate-300 font-medium animate-pulse">
                          {loadingStep}
                        </span>
                      </div>
                    ) : processedResultUrl ? (
                      currentTool.isPdf ? (
                        <div className="flex flex-col items-center justify-center gap-3 p-6 text-center">
                          <CheckCircle2 className="w-12 h-12 text-emerald-400 animate-bounce" />
                          <span className="text-xs text-slate-200 font-semibold">
                            PDF Generated Successfully
                          </span>
                          <span className="text-[11px] text-slate-500">
                            {rawFiles.length} page{rawFiles.length > 1 ? "s" : ""} compiled
                          </span>
                        </div>
                      ) : (
                        <div
                          className={`rounded-xl p-2 ${
                            currentTool.isTransparent
                              ? "bg-[linear-gradient(45deg,#1e293b_25%,transparent_25%),linear-gradient(-45deg,#1e293b_25%,transparent_25%),linear-gradient(45deg,transparent_75%,#1e293b_75%),linear-gradient(-45deg,transparent_75%,#1e293b_75%)] bg-[size:16px_16px]"
                              : ""
                          }`}
                        >
                          <img
                            src={processedResultUrl}
                            alt="Processed"
                            className="max-h-64 mx-auto object-contain rounded-lg shadow-md"
                          />
                        </div>
                      )
                    ) : null}
                  </div>
                </div>
              </div>
            )}

            {/* Bottom Actions Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-2">
                <label className="px-4 py-2.5 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 rounded-xl cursor-pointer text-xs font-semibold transition inline-flex items-center gap-2">
                  <Plus className="w-3.5 h-3.5" /> Add Images
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={handleAddMore}
                  />
                </label>

                <label className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl cursor-pointer text-xs font-semibold transition inline-flex items-center gap-2">
                  <Upload className="w-3.5 h-3.5" /> Replace
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
                  download={
                    currentTool.isPdf
                      ? "converted_document.pdf"
                      : `${activeTool}-result.${currentTool.isTransparent ? "png" : "jpg"}`
                  }
                  className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition inline-flex items-center gap-2 shadow-lg shadow-indigo-600/25 hover:shadow-indigo-600/40 active:scale-95"
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