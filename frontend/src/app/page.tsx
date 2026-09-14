"use client";

import React, { useState, useEffect } from "react";
import { SystemStatusCard } from "@/components/SystemStatusCard";
import { DocumentUploadZone } from "@/components/DocumentUploadZone";
import { DocumentDetailView } from "@/components/DocumentDetailView";
import { SemanticSearchZone } from "@/components/SemanticSearchZone";
import { TransformationWorkspace } from "@/components/TransformationWorkspace";
import { ResearchEvaluationDashboard } from "@/components/ResearchEvaluationDashboard";
import { DocumentDetail } from "@/types/document";
import { fetchDocuments } from "@/lib/api";
import {
  Sparkles,
  FileCode2,
  Search,
  Wand2,
  FlaskConical,
  FolderArchive,
  ExternalLink,
} from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"workspace" | "documents" | "research">("workspace");
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentDetail[]>([]);

  const loadDocuments = async () => {
    try {
      const data = await fetchDocuments();
      setDocuments(data.documents);
    } catch {
      // Handled gracefully in UI
    }
  };

  useEffect(() => {
    loadDocuments();
    const interval = setInterval(loadDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 bg-grid selection:bg-indigo-500 selection:text-white pb-24">
      {/* Top Navigation Bar */}
      <nav className="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
              T
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-100 tracking-tight text-base">TransformAI</span>
                <span className="px-2 py-0.5 text-[10px] uppercase font-mono font-bold bg-indigo-950 text-indigo-400 border border-indigo-800 rounded">
                  SIH26154
                </span>
              </div>
              <div className="text-[10px] text-slate-400 font-mono hidden sm:block">
                Source-Grounded Multi-Format Content Transformation
              </div>
            </div>
          </div>

          {/* Major Workflow Nav Tabs */}
          <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab("workspace")}
              className={`px-3.5 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                activeTab === "workspace"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Wand2 className="w-3.5 h-3.5" />
              <span>Workspace / Studio</span>
            </button>

            <button
              onClick={() => setActiveTab("documents")}
              className={`px-3.5 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                activeTab === "documents"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <FolderArchive className="w-3.5 h-3.5" />
              <span>Documents ({documents.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("research")}
              className={`px-3.5 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                activeTab === "research"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <FlaskConical className="w-3.5 h-3.5" />
              <span>Research &amp; Evaluation</span>
            </button>
          </div>

          <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-indigo-400 transition-colors flex items-center gap-1"
            >
              <span>Swagger API</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <div className="max-w-6xl mx-auto px-6 pt-8 pb-6 space-y-8">
        {/* Hero Banner */}
        <div className="space-y-2.5">
          <div className="inline-flex items-center gap-2 px-3 py-1 text-xs font-medium rounded-full bg-slate-900 border border-slate-800 text-indigo-400">
            <Sparkles className="w-3.5 h-3.5" />
            TransformAI Platform &mdash; Milestones 1&ndash;8 Complete
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-100">
            Source-Grounded Generative AI Platform
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
            Multi-format content transformation transforming technical source materials into Executive Summaries, Advisory Briefings, Presentation Decks, and Video Scripts with dense vector retrieval, context normalization, claim-level verification, and publication exports.
          </p>
        </div>

        {/* 1. WORKSPACE TAB */}
        {activeTab === "workspace" && (
          <div className="space-y-8 animate-fadeIn">
            {/* System Status Telemetry */}
            <SystemStatusCard />

            {/* Central Transformation Studio */}
            <div className="space-y-3">
              <TransformationWorkspace documents={documents} />
            </div>
          </div>
        )}

        {/* 2. DOCUMENTS TAB */}
        {activeTab === "documents" && (
          <div className="space-y-8 animate-fadeIn">
            {/* Document Ingestion Zone */}
            <div className="space-y-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <FileCode2 className="w-5 h-5 text-indigo-400" />
                  <h2 className="text-lg font-bold text-slate-100">Document Ingestion &amp; Intelligence</h2>
                </div>
                <p className="text-xs text-slate-400">
                  Upload PDF, DOCX, and TXT source documents to execute deterministic parsing, structure detection, and pgvector dense indexing.
                </p>
              </div>

              <DocumentUploadZone
                onUploadSuccess={(docId) => {
                  setSelectedDocId(docId);
                  loadDocuments();
                }}
              />

              {selectedDocId && (
                <div className="transition-all animate-fadeIn">
                  <DocumentDetailView documentId={selectedDocId} />
                </div>
              )}
            </div>

            {/* Semantic Vector Search & Provenance Grounding */}
            <div className="space-y-4 pt-4 border-t border-slate-800">
              <div className="flex items-center gap-2 mb-1">
                <Search className="w-5 h-5 text-indigo-400" />
                <h2 className="text-lg font-bold text-slate-100">Semantic Vector Retrieval</h2>
              </div>
              <SemanticSearchZone documents={documents} />
            </div>
          </div>
        )}

        {/* 3. RESEARCH & EVALUATION TAB */}
        {activeTab === "research" && (
          <div className="space-y-8 animate-fadeIn">
            <ResearchEvaluationDashboard />
          </div>
        )}
      </div>
    </main>
  );
}
