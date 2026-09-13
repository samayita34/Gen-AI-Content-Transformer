"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Layers,
  Hash,
  BookOpen,
  ChevronRight,
  Database,
} from "lucide-react";
import { fetchDocument, fetchDocumentChunks } from "@/lib/api";
import { DocumentDetail, DocumentChunk } from "@/types/document";

interface DocumentDetailViewProps {
  documentId: string;
}

export const DocumentDetailView: React.FC<DocumentDetailViewProps> = ({ documentId }) => {
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [chunksLoading, setChunksLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeChunkIndex, setActiveChunkIndex] = useState<number>(0);

  const loadDocument = useCallback(async () => {
    try {
      const data = await fetchDocument(documentId);
      setDoc(data);

      if (data.processing_status === "completed") {
        setChunksLoading(true);
        try {
          const chunkData = await fetchDocumentChunks(documentId);
          setChunks(chunkData.chunks);
        } finally {
          setChunksLoading(false);
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load document details.");
      }
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    loadDocument();
  }, [loadDocument]);

  // Poll status while processing
  useEffect(() => {
    if (!doc || doc.processing_status === "completed" || doc.processing_status === "failed") {
      return;
    }

    const interval = setInterval(() => {
      loadDocument();
    }, 2000);

    return () => clearInterval(interval);
  }, [doc, loadDocument]);

  if (loading) {
    return (
      <div className="w-full bg-slate-900/80 border border-slate-800 rounded-xl p-8 flex items-center justify-center gap-3 text-slate-400">
        <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
        <span className="text-xs">Loading document intelligence data...</span>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="w-full bg-rose-950/40 border border-rose-800 rounded-xl p-6 text-xs text-rose-300">
        <p className="font-semibold">Error Loading Document</p>
        <p className="mt-1">{error || "Document not found."}</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-2xl">
      {/* Header & Status */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-5 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-950/80 border border-indigo-800 flex items-center justify-center text-indigo-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100">{doc.original_filename}</h3>
            <p className="text-xs text-slate-400 mt-0.5">ID: <span className="font-mono text-slate-300">{doc.id}</span></p>
          </div>
        </div>

        <div>
          {doc.processing_status === "completed" && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800">
              <CheckCircle2 className="w-3.5 h-3.5" /> Pipeline Completed
            </span>
          )}
          {doc.processing_status === "processing" && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Processing Elements...
            </span>
          )}
          {doc.processing_status === "uploaded" && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-950/80 text-sky-400 border border-sky-800">
              <Clock className="w-3.5 h-3.5" /> Queued
            </span>
          )}
          {doc.processing_status === "failed" && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-400 border border-rose-800">
              <XCircle className="w-3.5 h-3.5" /> Processing Failed
            </span>
          )}
        </div>
      </div>

      {/* Failure message if failed */}
      {doc.error_message && (
        <div className="mt-4 p-4 bg-rose-950/40 border border-rose-800 rounded-lg text-xs text-rose-300">
          <p className="font-semibold text-rose-200">Pipeline Error Details:</p>
          <p className="mt-1 font-mono">{doc.error_message}</p>
        </div>
      )}

      {/* Document Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-6">
        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
            <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
            <span>Pages / Format</span>
          </div>
          <p className="text-sm font-semibold text-slate-200 uppercase font-mono">
            {doc.page_count ? `${doc.page_count}p &bull; ` : ""}{doc.file_type}
          </p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
            <Hash className="w-3.5 h-3.5 text-sky-400" />
            <span>Words / Chars</span>
          </div>
          <p className="text-sm font-semibold text-slate-200 font-mono">
            {doc.word_count?.toLocaleString() || "—"} w / {doc.character_count?.toLocaleString() || "—"} c
          </p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
            <Layers className="w-3.5 h-3.5 text-teal-400" />
            <span>Chunks Created</span>
          </div>
          <p className="text-sm font-semibold text-slate-200 font-mono">
            {doc.total_chunks} chunks
          </p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
            <Database className="w-3.5 h-3.5 text-violet-400" />
            <span>Chunking Method</span>
          </div>
          <p className="text-xs font-semibold text-slate-200 font-mono capitalize">
            {doc.chunking_strategy.replace("_", " ")}
          </p>
        </div>
      </div>

      {/* Chunks Provenance Inspector */}
      {doc.processing_status === "completed" && (
        <div className="mt-6 pt-5 border-t border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Chunk Provenance & Vector Representation Inspector
              </h4>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Vector: 384-dim (all-MiniLM-L6-v2)
            </span>
          </div>

          {chunksLoading ? (
            <div className="p-8 flex items-center justify-center gap-2 text-slate-400 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Retrieving chunk vector metadata...</span>
            </div>
          ) : chunks.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Chunk List Sidebar */}
              <div className="lg:col-span-4 max-h-80 overflow-y-auto pr-2 space-y-2 border-r border-slate-800/60">
                {chunks.map((c, idx) => (
                  <button
                    key={c.id}
                    onClick={() => setActiveChunkIndex(idx)}
                    className={`w-full p-2.5 rounded-lg border text-left text-xs transition-colors flex items-center justify-between ${
                      activeChunkIndex === idx
                        ? "border-indigo-500 bg-indigo-950/40 text-indigo-200"
                        : "border-slate-800/60 bg-slate-950/40 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <div className="truncate pr-2">
                      <span className="font-semibold text-slate-300 font-mono">Chunk #{c.chunk_index + 1}</span>
                      <span className="block text-[11px] text-slate-400 truncate mt-0.5">
                        {c.section_title || c.content.slice(0, 40)}
                      </span>
                    </div>
                    <ChevronRight className={`w-3.5 h-3.5 flex-shrink-0 ${activeChunkIndex === idx ? "text-indigo-400" : "text-slate-600"}`} />
                  </button>
                ))}
              </div>

              {/* Chunk Content & Provenance Viewer */}
              <div className="lg:col-span-8 bg-slate-950/60 border border-slate-800/80 rounded-lg p-4">
                {chunks[activeChunkIndex] && (
                  <div className="space-y-3">
                    {/* Provenance Badges */}
                    <div className="flex flex-wrap items-center gap-2 pb-3 border-b border-slate-800 text-[11px]">
                      <span className="px-2 py-0.5 rounded bg-slate-800 font-mono text-slate-300">
                        Index: #{chunks[activeChunkIndex].chunk_index + 1}
                      </span>
                      {chunks[activeChunkIndex].page_number && (
                        <span className="px-2 py-0.5 rounded bg-slate-800 font-mono text-indigo-300">
                          Page {chunks[activeChunkIndex].page_number}
                        </span>
                      )}
                      {chunks[activeChunkIndex].section_title && (
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-teal-300 font-medium truncate max-w-xs">
                          Sec: {chunks[activeChunkIndex].section_title}
                        </span>
                      )}
                      <span className="px-2 py-0.5 rounded bg-slate-800 font-mono text-slate-400">
                        {chunks[activeChunkIndex].character_count} chars &bull; {chunks[activeChunkIndex].token_count} words
                      </span>
                      <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800/80 font-mono text-[10px]">
                        Indexed in pgvector
                      </span>
                    </div>

                    {/* Chunk Text Content */}
                    <div className="p-3 bg-slate-900/80 rounded border border-slate-800/60 text-xs text-slate-200 font-mono leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto">
                      {chunks[activeChunkIndex].content}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic p-4 text-center">No chunks found for this document.</p>
          )}
        </div>
      )}
    </div>
  );
};
