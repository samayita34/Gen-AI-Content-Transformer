"use client";

import React, { useState, useEffect } from "react";
import { SystemStatusCard } from "@/components/SystemStatusCard";
import { DocumentUploadZone } from "@/components/DocumentUploadZone";
import { DocumentDetailView } from "@/components/DocumentDetailView";
import { SemanticSearchZone } from "@/components/SemanticSearchZone";
import { TransformationWorkspace } from "@/components/TransformationWorkspace";
import { DocumentDetail } from "@/types/document";
import { fetchDocuments } from "@/lib/api";
import { Cpu, ShieldCheck, Sparkles, BookOpen, Layers, FileCode2, Search, Wand2 } from "lucide-react";

export default function Home() {
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
      {/* Top Banner / Navbar */}
      <nav className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur sticky top-0 z-50 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
              T
            </div>
            <div>
              <span className="font-bold text-slate-100 tracking-tight text-base">TransformAI</span>
              <span className="ml-2 px-2 py-0.5 text-[10px] uppercase font-mono font-bold bg-indigo-950 text-indigo-400 border border-indigo-800 rounded">
                SIH26154
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-indigo-400 font-mono transition-colors"
            >
              API Docs (Swagger) &rarr;
            </a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-6 pt-10 pb-6">
        <div className="max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 text-xs font-medium rounded-full bg-slate-900 border border-slate-800 text-indigo-400">
            <Sparkles className="w-3.5 h-3.5" />
            Milestone 4: Multi-Format Generative AI Active
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
            Gen AI Platform for <br className="hidden sm:inline" />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-sky-300 to-teal-300">
              Automated Content Transformation
            </span>
          </h1>
          <p className="text-sm text-slate-400 leading-relaxed">
            A research-oriented platform transforming technical documents (PDF, DOCX, TXT) into Executive Summaries, Advisories, Presentation Decks, and Video Scripts with source-grounding and anti-fabrication constraints.
          </p>
        </div>

        {/* Live Infrastructure Telemetry */}
        <div className="mt-8">
          <SystemStatusCard />
        </div>

        {/* Milestone 4: Multi-Format Transformation Studio */}
        <div className="mt-12 space-y-4">
          <div className="flex items-center gap-2 mb-1">
            <Wand2 className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Content Transformation Studio</h2>
          </div>
          <TransformationWorkspace documents={documents} />
        </div>

        {/* Milestone 3: Semantic Vector Retrieval Section */}
        <div className="mt-14 space-y-4">
          <div className="flex items-center gap-2 mb-1">
            <Search className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Semantic Search & Provenance Grounding</h2>
          </div>
          <SemanticSearchZone documents={documents} />
        </div>

        {/* Milestone 2: Document Intelligence Workstation */}
        <div className="mt-14 space-y-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <FileCode2 className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-slate-100">Document Intelligence Layer</h2>
            </div>
            <p className="text-xs text-slate-400">
              Upload source materials to execute the deterministic parsing, cleaning, structure detection, and embedding pipeline.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8">
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
        </div>

        {/* Research Objectives & Architecture Pillars */}
        <div className="mt-16">
          <h2 className="text-lg font-bold text-slate-100 mb-6 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Core Research & Architecture Pillars
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Pillar 1 */}
            <div className="p-6 bg-slate-900/40 border border-slate-800/80 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-indigo-950/60 border border-indigo-800 flex items-center justify-center text-indigo-400 mb-4">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-slate-200 mb-2 text-sm">
                Deterministic Ingestion
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Native parsing across PDF, DOCX, and TXT with layout extraction, Unicode normalization, and line-wrap reconstruction.
              </p>
            </div>

            {/* Pillar 2 */}
            <div className="p-6 bg-slate-900/40 border border-slate-800/80 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-teal-950/60 border border-teal-800 flex items-center justify-center text-teal-400 mb-4">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-slate-200 mb-2 text-sm">
                Multi-Format Synthesis
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Source-grounded pipelines generating decision briefs, advisories, slide decks, and storyboard scripts.
              </p>
            </div>

            {/* Pillar 3 */}
            <div className="p-6 bg-slate-900/40 border border-slate-800/80 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-sky-950/60 border border-sky-800 flex items-center justify-center text-sky-400 mb-4">
                <BookOpen className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-slate-200 mb-2 text-sm">
                Strict Provenance Traceability
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Every generated artifact links back to discrete source citations, page numbers, and chunk references.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
