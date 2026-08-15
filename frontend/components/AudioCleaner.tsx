'use client';

import { useState, useRef } from 'react';
import { Mic, Square, Upload, Download, RefreshCw, Volume2, AlertCircle } from 'lucide-react';

const API_BASE_URL = 'https://ai-media-cleanup.onrender.com';

export default function AudioCleaner() {
  const [isRecording, setIsRecording] = useState(false);
  const [originalAudio, setOriginalAudio] = useState<string | null>(null);
  const [cleanedAudio, setCleanedAudio] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    setError(null);
    setOriginalAudio(null);
    setCleanedAudio(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setOriginalAudio(URL.createObjectURL(blob));
        sendAudio(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setError('Microphone access denied. Please verify browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setError(null);
      setOriginalAudio(URL.createObjectURL(file));
      setCleanedAudio(null);
      sendAudio(file);
    }
  };

  const sendAudio = async (data: Blob | File) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', data, 'audio.wav');

    try {
      const res = await fetch(`${API_BASE_URL}/api/audio/clean`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Audio denoising failed on server');

      const blob = await res.blob();
      setCleanedAudio(URL.createObjectURL(blob));
    } catch (err) {
      setError('Failed to process audio. Please try again.');
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

      {!originalAudio && (
        <div className="w-full flex flex-col items-center gap-4">
          <div className="p-8 bg-slate-50 border border-dashed border-slate-300 rounded-2xl w-full flex flex-col items-center justify-center">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`w-20 h-20 rounded-full flex items-center justify-center text-white transition-all shadow-md ${
                isRecording ? 'bg-red-500 animate-pulse' : 'bg-indigo-600 hover:bg-indigo-700'
              }`}
            >
              {isRecording ? <Square size={26} /> : <Mic size={32} />}
            </button>
            <span className="text-sm font-medium text-slate-700 mt-4">
              {isRecording ? 'Recording voice... Click to stop' : 'Click to Record Voice'}
            </span>
          </div>

          <div className="relative flex py-1 items-center w-full">
            <div className="flex-grow border-t border-slate-200" />
            <span className="flex-shrink mx-4 text-xs font-semibold text-slate-400 uppercase">OR</span>
            <div className="flex-grow border-t border-slate-200" />
          </div>

          <label className="w-full flex items-center justify-center gap-2 p-3.5 border border-slate-200 hover:bg-slate-50 rounded-xl cursor-pointer transition text-slate-700 font-medium text-sm">
            <Upload size={18} />
            <span>Upload Audio File (.wav, .mp3)</span>
            <input type="file" accept="audio/*" className="hidden" onChange={handleFileUpload} />
          </label>
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-3 text-indigo-600 py-8 font-medium">
          <RefreshCw className="animate-spin" size={22} />
          <span>Subtracting noise profile...</span>
        </div>
      )}

      {originalAudio && !loading && (
        <div className="w-full flex flex-col gap-4">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Original Audio</span>
            <audio src={originalAudio} controls className="w-full mt-2" />
          </div>

          {cleanedAudio && (
            <div className="bg-indigo-50/60 p-4 rounded-xl border border-indigo-100">
              <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider flex items-center gap-1.5">
                <Volume2 size={14} /> Denoised Audio
              </span>
              <audio src={cleanedAudio} controls className="w-full mt-2" />
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => {
                setOriginalAudio(null);
                setCleanedAudio(null);
              }}
              className="flex-1 py-2.5 border border-slate-300 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition"
            >
              Record / Upload Another
            </button>
            {cleanedAudio && (
              <a
                href={cleanedAudio}
                download="cleaned_voice.wav"
                className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium flex items-center justify-center gap-2 shadow-sm transition"
              >
                <Download size={16} /> Download WAV
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}