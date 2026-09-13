"use client";

import React, { useState } from "react";
import { DocumentDetail } from "@/types/document";
import {
  RetrievalChunkItem,
  NormalizedContextResponse,
} from "@/types/retrieval";
import { searchRetrieval, fetchNormalizedContext } from "@/lib/api";

interface SemanticSearchZoneProps {
  documents: DocumentDetail[];
}

export function SemanticSearchZone({ documents }: SemanticSearchZoneProps) {
  const [query, setQuery] = useState("");
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [topK, setTopK] = useState<number>(5);
  const [threshold, setThreshold] = useState<number>(0.0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const [results, setResults] = useState<RetrievalChunkItem[] | null>(null);
  const [normalizedContext, setNormalizedContext] = useState<NormalizedContextResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"chunks" | "normalized">("chunks");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const searchReq = {
        query: query.trim(),
        document_id: selectedDocId ? selectedDocId : null,
        top_k: topK,
        similarity_threshold: threshold,
      };

      const [searchRes, contextRes] = await Promise.all([
        searchRetrieval(searchReq),
        fetchNormalizedContext(searchReq),
      ]);

      setResults(searchRes.results);
      setNormalizedContext(contextRes);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Vector search failed";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 0.75) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (score >= 0.5) return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    return "bg-slate-500/10 text-slate-400 border-slate-500/20";
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Semantic Vector Retrieval & Context Normalization
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Search across ingested document chunks using pgvector dense cosine similarity with 100% source-grounded provenance.
            </p>
          </div>
          <div className="px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-mono font-medium">
            Milestone 3 (RAG)
          </div>
        </div>
      </div>

      {/* Search Input Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Natural Language Query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What are the key architectural components or transformation goals?"
              className="w-full bg-slate-800/80 border border-slate-700 text-slate-100 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder-slate-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Document Scope
            </label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full bg-slate-800/80 border border-slate-700 text-slate-100 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">🌐 All Ingested Documents</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  📄 {doc.original_filename} ({doc.processing_status})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Sliders & Parameters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-2 items-center">
          <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-750">
            <div className="flex justify-between text-xs text-slate-300 font-medium mb-1">
              <span>Top K Chunks:</span>
              <span className="text-indigo-400 font-mono font-bold">{topK}</span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value, 10))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
          </div>

          <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-750">
            <div className="flex justify-between text-xs text-slate-300 font-medium mb-1">
              <span>Similarity Threshold:</span>
              <span className="text-indigo-400 font-mono font-bold">{threshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.9"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
          </div>

          <div className="sm:col-span-2 md:col-span-1 flex items-end">
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className={`w-full py-2.5 px-4 rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2 ${
                isLoading || !query.trim()
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                  : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-lg shadow-indigo-600/30"
              }`}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Searching Vector Store...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Execute Vector Search</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-sm flex items-center gap-2">
          <svg className="w-5 h-5 text-rose-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {results !== null && (
        <div className="space-y-4 pt-2">
          {/* Tabs */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab("chunks")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                  activeTab === "chunks"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/20"
                    : "bg-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                Retrieved Chunks ({results.length})
              </button>
              <button
                onClick={() => setActiveTab("normalized")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                  activeTab === "normalized"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/20"
                    : "bg-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                Normalized Context Model
              </button>
            </div>
            <div className="text-xs text-slate-400">
              Metric: <span className="font-mono text-slate-300">Cosine Similarity (1 - dist)</span>
            </div>
          </div>

          {/* Tab 1: Retrieved Chunks List */}
          {activeTab === "chunks" && (
            <div className="space-y-3">
              {results.length === 0 ? (
                <div className="text-center py-8 bg-slate-950/40 rounded-lg border border-slate-800">
                  <p className="text-slate-400 text-sm">No document chunks matched the threshold ({threshold}).</p>
                  <p className="text-slate-500 text-xs mt-1">Try lowering the similarity threshold or refining the search query.</p>
                </div>
              ) : (
                results.map((chunk, idx) => (
                  <div
                    key={chunk.chunk_id}
                    className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 text-xs font-mono font-bold flex items-center justify-center">
                          #{idx + 1}
                        </span>
                        <span className="text-xs font-semibold text-slate-200">
                          {chunk.source_filename || "Document"}
                        </span>
                        {chunk.section_title && (
                          <span className="px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/40 text-[11px] font-medium">
                            § {chunk.section_title}
                          </span>
                        )}
                        {chunk.page_number && (
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[11px]">
                            Page {chunk.page_number}
                          </span>
                        )}
                        <span className="px-2 py-0.5 rounded bg-slate-800/60 text-slate-400 text-[11px] font-mono">
                          Chunk {chunk.chunk_index} ({chunk.chunking_strategy})
                        </span>
                      </div>

                      <div className={`px-2.5 py-1 rounded border text-xs font-mono font-bold ${getScoreBadgeColor(chunk.similarity_score)}`}>
                        Similarity: {chunk.similarity_score.toFixed(4)}
                      </div>
                    </div>

                    <div className="text-sm text-slate-300 leading-relaxed bg-slate-900/80 p-3 rounded-lg border border-slate-800/80 font-serif">
                      {chunk.content}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Tab 2: Normalized Context Preview */}
          {activeTab === "normalized" && normalizedContext && (
            <div className="space-y-4 bg-slate-950/50 p-4 rounded-xl border border-slate-800 text-xs">
              <div>
                <h4 className="font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  Deterministic Source Facts ({normalizedContext.facts.length})
                </h4>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-2">
                  {normalizedContext.facts.map((f, i) => (
                    <div key={i} className="p-2 bg-slate-900/90 rounded border border-slate-800 text-slate-300 flex justify-between gap-4">
                      <span>• {f.fact_text}</span>
                      <span className="text-[10px] text-slate-400 font-mono flex-shrink-0">
                        [{f.source_reference.source_filename} : p.{f.source_reference.page_number || 1} c.{f.source_reference.chunk_index}]
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div>
                  <h4 className="font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                    Recognized Entities ({normalizedContext.entities.length})
                  </h4>
                  <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                    {normalizedContext.entities.map((e, i) => (
                      <span key={i} className="px-2 py-1 rounded bg-slate-900 border border-slate-750 text-slate-300 text-[11px] font-mono">
                        <span className="text-cyan-400">{e.entity_name}</span>{" "}
                        <span className="text-[9px] text-slate-400">({e.entity_type})</span>
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                    Representative Key Passages ({normalizedContext.key_points.length})
                  </h4>
                  <ul className="space-y-1 text-slate-400 max-h-36 overflow-y-auto">
                    {normalizedContext.key_points.map((kp, i) => (
                      <li key={i} className="p-1.5 bg-slate-900/60 rounded border border-slate-800 text-slate-300">
                        “{kp}”
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
