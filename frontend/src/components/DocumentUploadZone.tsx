"use client";

import React, { useState, useRef } from "react";
import {
  Upload,
  FileText,
  Image as ImageIcon,
  Mic,
  Video,
  CheckCircle,
  AlertCircle,
  Loader2,
  Sparkles,
  Layers,
} from "lucide-react";
import { uploadDocument } from "@/lib/api";
import { ChunkingStrategy, SourceModality } from "@/types/document";

interface DocumentUploadZoneProps {
  onUploadSuccess: (documentId: string) => void;
}

const TEXT_EXTS = [".pdf", ".docx", ".txt", ".text", ".md"];
const IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"];
const AUDIO_EXTS = [".mp3", ".wav", ".m4a", ".ogg", ".flac"];
const VIDEO_EXTS = [".mp4", ".avi", ".mov", ".mkv", ".webm"];
const ALL_SUPPORTED_EXTS = [...TEXT_EXTS, ...IMAGE_EXTS, ...AUDIO_EXTS, ...VIDEO_EXTS];

export const DocumentUploadZone: React.FC<DocumentUploadZoneProps> = ({ onUploadSuccess }) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedModality, setSelectedModality] = useState<SourceModality>("text");
  const [chunkingStrategy, setChunkingStrategy] = useState<ChunkingStrategy>("structure_aware");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const detectModality = (ext: string): SourceModality => {
    if (IMAGE_EXTS.includes(ext)) return "image";
    if (AUDIO_EXTS.includes(ext)) return "audio";
    if (VIDEO_EXTS.includes(ext)) return "video";
    return "text";
  };

  const getMaxLimitBytes = (modality: SourceModality): number => {
    switch (modality) {
      case "image":
        return 20 * 1024 * 1024;
      case "audio":
        return 50 * 1024 * 1024;
      case "video":
        return 100 * 1024 * 1024;
      default:
        return 15 * 1024 * 1024;
    }
  };

  const handleFileSelect = (file: File) => {
    setError(null);
    const fileExt = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();

    if (!ALL_SUPPORTED_EXTS.includes(fileExt)) {
      setError(`Unsupported format '${fileExt}'. Supported: PDF, DOCX, TXT, Images, Audio, Video.`);
      setSelectedFile(null);
      return;
    }

    const modality = detectModality(fileExt);
    const maxLimit = getMaxLimitBytes(modality);
    if (file.size > maxLimit) {
      const maxMb = maxLimit / (1024 * 1024);
      setError(`File size exceeds maximum allowed limit of ${maxMb} MB for ${modality} sources.`);
      setSelectedFile(null);
      return;
    }

    setSelectedModality(modality);
    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError(null);

    try {
      const response = await uploadDocument(selectedFile, chunkingStrategy);
      setSelectedFile(null);
      onUploadSuccess(response.document_id);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred during source upload.");
      }
    } finally {
      setUploading(false);
    }
  };

  const renderModalityBadge = (modality: SourceModality) => {
    switch (modality) {
      case "image":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-950/70 text-amber-300 border border-amber-800">
            <ImageIcon className="w-3.5 h-3.5" /> Image (OCR)
          </span>
        );
      case "audio":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-violet-950/70 text-violet-300 border border-violet-800">
            <Mic className="w-3.5 h-3.5" /> Audio (STT)
          </span>
        );
      case "video":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950/70 text-rose-300 border border-rose-800">
            <Video className="w-3.5 h-3.5" /> Video (Transcript + Scenes)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-950/70 text-blue-300 border border-blue-800">
            <FileText className="w-3.5 h-3.5" /> Text Document
          </span>
        );
    }
  };

  return (
    <div className="w-full bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Upload className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-slate-100">Ingest Multimodal Source Material</h3>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <span className="flex items-center gap-1"><FileText className="w-3 h-3 text-blue-400" /> Text</span>
          <span className="text-slate-600">&bull;</span>
          <span className="flex items-center gap-1"><ImageIcon className="w-3 h-3 text-amber-400" /> Image</span>
          <span className="text-slate-600">&bull;</span>
          <span className="flex items-center gap-1"><Mic className="w-3 h-3 text-violet-400" /> Audio</span>
          <span className="text-slate-600">&bull;</span>
          <span className="flex items-center gap-1"><Video className="w-3 h-3 text-rose-400" /> Video</span>
        </div>
      </div>
      <p className="text-xs text-slate-400 mb-6">
        Upload text documents, diagrams, audio recordings, or video walkthroughs for deterministic normalization, semantic chunking, and pgvector dense indexing.
      </p>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200 ${
          dragOver
            ? "border-indigo-500 bg-indigo-950/20"
            : selectedFile
            ? "border-emerald-500/80 bg-emerald-950/10"
            : "border-slate-700/80 hover:border-slate-600 bg-slate-950/40"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.text,.md,.png,.jpg,.jpeg,.webp,.bmp,.tiff,.mp3,.wav,.m4a,.ogg,.flac,.mp4,.avi,.mov,.mkv,.webm"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />

        {selectedFile ? (
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 rounded-full bg-emerald-950 border border-emerald-700 flex items-center justify-center text-emerald-400 mb-3">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div className="flex items-center gap-2 mb-1">
              <p className="text-sm font-semibold text-slate-200">{selectedFile.name}</p>
              {renderModalityBadge(selectedModality)}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {(selectedFile.size / 1024).toFixed(1)} KB &bull; Ready to process into common representation
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-indigo-400 mb-3">
              <Upload className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-200">
              Drag & drop source material here, or <span className="text-indigo-400 underline">browse files</span>
            </p>
            <p className="text-xs text-slate-500 mt-1.5">
              Supported: PDF, DOCX, TXT, PNG, JPG, MP3, WAV, MP4 (Modality-specific limits up to 100 MB)
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-rose-950/50 border border-rose-800 rounded-lg flex items-center gap-2.5 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Chunking Strategy Selector */}
      <div className="mt-6 pt-4 border-t border-slate-800">
        <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
          Research Chunking Strategy:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setChunkingStrategy("structure_aware")}
            className={`p-3 rounded-lg border text-left transition-all ${
              chunkingStrategy === "structure_aware"
                ? "border-indigo-500 bg-indigo-950/40 text-indigo-200 shadow-md shadow-indigo-950"
                : "border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700"
            }`}
          >
            <div className="flex items-center gap-1.5 font-medium text-xs text-slate-200">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Structure-Aware (Proposed)</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1 leading-snug">
              Preserves section headings, paragraph boundaries, and transcript timestamp intervals.
            </p>
          </button>

          <button
            type="button"
            onClick={() => setChunkingStrategy("fixed_size")}
            className={`p-3 rounded-lg border text-left transition-all ${
              chunkingStrategy === "fixed_size"
                ? "border-indigo-500 bg-indigo-950/40 text-indigo-200 shadow-md shadow-indigo-950"
                : "border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700"
            }`}
          >
            <div className="flex items-center gap-1.5 font-medium text-xs text-slate-200">
              <Layers className="w-3.5 h-3.5 text-sky-400" />
              <span>Fixed-Size Window (Baseline)</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1 leading-snug">
              Fixed character window with sliding overlap for empirical comparison.
            </p>
          </button>
        </div>
      </div>

      {/* Upload Action Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-lg shadow-indigo-600/30 transition-colors"
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Normalizing & Embedding...</span>
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              <span>Start Multimodal Ingestion</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
