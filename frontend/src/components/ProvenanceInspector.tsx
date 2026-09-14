"use client";

import React from "react";
import { SourceReference } from "@/types/retrieval";
import {
  FileText,
  Layers,
  X,
  BookOpen,
  Hash,
  Sparkles,
} from "lucide-react";

interface ProvenanceInspectorProps {
  sourceReferences: SourceReference[];
  retrievedChunkIds?: string[];
  retrievalScores?: number[];
  documentFilename?: string;
  documentId?: string;
  onClose?: () => void;
}

export function ProvenanceInspector({
  sourceReferences,
  retrievedChunkIds = [],
  retrievalScores = [],
  documentFilename,
  documentId,
  onClose,
}: ProvenanceInspectorProps) {
  return (
    <div className="rounded-2xl border border-indigo-500/30 bg-slate-900/95 backdrop-blur-xl p-5 shadow-2xl space-y-5 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Source Provenance &amp; Grounding Traceability
            </h3>
            <p className="text-[11px] text-slate-400">
              Discrete chunks retrieved from the dense vector index to ground this transformation.
            </p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close provenance inspector"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Metadata Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-slate-950/60 p-3 rounded-xl border border-slate-800">
        <div>
          <span className="text-[10px] uppercase font-mono text-slate-500 block">Source Document</span>
          <span className="font-semibold text-slate-200 truncate block">
            {documentFilename || "Active Ingested Document"}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-mono text-slate-500 block">Grounding Chunks</span>
          <span className="font-semibold text-indigo-400 font-mono">
            {sourceReferences.length} chunk{sourceReferences.length !== 1 ? "s" : ""} utilized
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-mono text-slate-500 block">Source Document ID</span>
          <span className="font-mono text-slate-400 text-[11px] truncate block">
            {documentId ? `${documentId.slice(0, 16)}...` : "—"}
          </span>
        </div>
      </div>

      {/* Source Reference Chunks List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            Retrieved Context Citations
          </span>
          <span className="text-[11px] font-normal text-slate-500 lowercase">
            ordered by dense retrieval rank
          </span>
        </div>

        {sourceReferences.length === 0 ? (
          <div className="text-center py-6 rounded-xl bg-slate-950/40 border border-slate-800 text-slate-500 text-xs">
            No source references recorded for this transformation run.
          </div>
        ) : (
          <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
            {sourceReferences.map((ref, idx) => {
              const simScore = retrievalScores[idx];
              const chunkId = retrievedChunkIds[idx] || ref.chunk_id;

              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-slate-700/80 transition space-y-2"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs border-b border-slate-800/60 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 font-mono text-[10px] font-bold">
                        Ref #{idx + 1}
                      </span>
                      <span className="text-slate-200 font-medium flex items-center gap-1">
                        <FileText className="w-3.5 h-3.5 text-slate-400" />
                        {ref.source_filename || "Document"}
                      </span>
                      {ref.section_title && (
                        <span className="text-indigo-400 font-medium">
                          § {ref.section_title}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-[11px] font-mono">
                      {ref.page_number && (
                        <span className="text-slate-400">
                          Page {ref.page_number}
                        </span>
                      )}
                      {ref.chunk_index !== undefined && ref.chunk_index !== null && (
                        <span className="text-slate-500 flex items-center gap-0.5">
                          <Hash className="w-3 h-3" /> Chunk {ref.chunk_index}
                        </span>
                      )}
                      {simScore !== undefined && simScore !== null && (
                        <span className="text-emerald-400 font-semibold">
                          Sim: {(simScore * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </div>

                  {chunkId && (
                    <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
                      <span>Chunk ID:</span>
                      <span className="text-slate-400">{chunkId}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Grounding Notice Footer */}
      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-2 text-[11px] text-slate-400">
        <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Strict Anti-Fabrication Boundary: </span>
          The transformation pipeline injects solely these indexed chunks into the context normalization layer. All output claims must derive from these citations.
        </div>
      </div>
    </div>
  );
}
