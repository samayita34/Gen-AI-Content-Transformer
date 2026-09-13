"use client";

import React, { useState } from "react";
import { DocumentDetail } from "@/types/document";
import {
  OutputType,
  AudienceType,
  ToneType,
  DetailLevel,
  CommunicationObjective,
  TransformationResult,
  ExecutiveSummaryContent,
  AdvisoryContent,
  PresentationContent,
  VideoScriptContent,
} from "@/types/generation";
import { transformDocument, verifyTransformation } from "@/lib/api";
import { VerificationReport } from "@/types/verification";
import { VerificationReportCard } from "@/components/VerificationReportCard";
import {
  FileText,
  AlertTriangle,
  Presentation,
  Video,
  Sparkles,
  Sliders,
  ChevronRight,
  Clock,
  Cpu,
  Layers,
  Info,
  ShieldCheck,
} from "lucide-react";

interface TransformationWorkspaceProps {
  documents: DocumentDetail[];
}

export function TransformationWorkspace({ documents }: TransformationWorkspaceProps) {
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [outputType, setOutputType] = useState<OutputType>("executive_summary");
  const [audience, setAudience] = useState<AudienceType>("executive");
  const [tone, setTone] = useState<ToneType>("professional");
  const [detailLevel, setDetailLevel] = useState<DetailLevel>("moderate");
  const [objective, setObjective] = useState<CommunicationObjective>("inform");
  const [customIntent, setCustomIntent] = useState<string>("");
  const [lengthConstraint, setLengthConstraint] = useState<string>("");
  const [topK, setTopK] = useState<number>(5);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TransformationResult | null>(null);
  const [activeSlideIdx, setActiveSlideIdx] = useState<number>(0);

  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verificationReport, setVerificationReport] = useState<VerificationReport | null>(null);
  const [verificationError, setVerificationError] = useState<string | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDocId) {
      setError("Please select an ingested source document first.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setVerificationReport(null);
    setVerificationError(null);

    try {
      const res = await transformDocument({
        document_id: selectedDocId,
        output_type: outputType,
        audience,
        tone,
        detail_level: detailLevel,
        communication_objective: objective,
        custom_intent: customIntent.trim() || null,
        length_constraint: lengthConstraint.trim() || null,
        top_k: topK,
      });
      setResult(res);
      setActiveSlideIdx(0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Transformation failed";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!selectedDocId || !result) return;
    setIsVerifying(true);
    setVerificationError(null);

    try {
      const rep = await verifyTransformation({
        document_id: selectedDocId,
        output_type: result.output_type,
        transformation_content: result.content as unknown as Record<string, unknown>,
      });
      setVerificationReport(rep);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Verification failed";
      setVerificationError(msg);
    } finally {
      setIsVerifying(false);
    }
  };

  const FORMATS = [
    {
      id: "executive_summary" as OutputType,
      title: "Executive Summary",
      desc: "Decision-oriented overview, key findings, and strategic implications.",
      icon: FileText,
      color: "from-blue-500/20 to-indigo-500/20 text-blue-400 border-blue-500/30",
    },
    {
      id: "advisory" as OutputType,
      title: "Advisory Briefing",
      desc: "Situation, key information, risks, and grounded recommendations.",
      icon: AlertTriangle,
      color: "from-amber-500/20 to-orange-500/20 text-amber-400 border-amber-500/30",
    },
    {
      id: "presentation" as OutputType,
      title: "Presentation Deck",
      desc: "Narrative slide deck with bullet points and spoken presenter notes.",
      icon: Presentation,
      color: "from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/30",
    },
    {
      id: "video_script" as OutputType,
      title: "Video Storyboard",
      desc: "Multi-scene script with visual cues, voiceover narration, and text.",
      icon: Video,
      color: "from-purple-500/20 to-pink-500/20 text-purple-400 border-purple-500/30",
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            Multi-Format Content Transformation Studio
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Transform source documents into executive summaries, advisories, slide decks, or video scripts with strict source-grounding.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-mono text-amber-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
            Source Grounded (Unverified)
          </span>
          <span className="px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-mono font-medium">
            Milestone 4
          </span>
        </div>
      </div>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Configuration Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          <form onSubmit={handleGenerate} className="space-y-4">
            {/* 1. Document Selection */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                1. Select Source Document
              </label>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="w-full bg-slate-800/90 border border-slate-700 text-slate-100 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="">-- Choose Ingested Document --</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    📄 {doc.original_filename} ({doc.processing_status})
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Format Selection Cards */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                2. Target Output Format
              </label>
              <div className="grid grid-cols-2 gap-2.5">
                {FORMATS.map((fmt) => {
                  const Icon = fmt.icon;
                  const isSelected = outputType === fmt.id;
                  return (
                    <button
                      key={fmt.id}
                      type="button"
                      onClick={() => setOutputType(fmt.id)}
                      className={`p-3 rounded-xl text-left border transition-all flex flex-col justify-between ${
                        isSelected
                          ? `bg-gradient-to-br ${fmt.color} ring-2 ring-indigo-500 shadow-lg`
                          : "bg-slate-800/40 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className="w-4 h-4 flex-shrink-0" />
                        <span className="font-semibold text-xs text-slate-200">{fmt.title}</span>
                      </div>
                      <p className="text-[11px] leading-tight text-slate-400">{fmt.desc}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 3. Parameter Controls */}
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-3">
              <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                3. Transformation Parameters
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Target Audience</label>
                  <select
                    value={audience}
                    onChange={(e) => setAudience(e.target.value as AudienceType)}
                    className="w-full bg-slate-900 border border-slate-750 text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="executive">Executive</option>
                    <option value="technical">Technical</option>
                    <option value="general_public">General Public</option>
                    <option value="academic">Academic</option>
                    <option value="operational">Operational</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Stylistic Tone</label>
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value as ToneType)}
                    className="w-full bg-slate-900 border border-slate-750 text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="professional">Professional</option>
                    <option value="concise">Concise</option>
                    <option value="formal">Formal</option>
                    <option value="explanatory">Explanatory</option>
                    <option value="neutral">Neutral</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Detail Level</label>
                  <select
                    value={detailLevel}
                    onChange={(e) => setDetailLevel(e.target.value as DetailLevel)}
                    className="w-full bg-slate-900 border border-slate-750 text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="moderate">Moderate</option>
                    <option value="brief">Brief</option>
                    <option value="detailed">Detailed</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Objective</label>
                  <select
                    value={objective}
                    onChange={(e) => setObjective(e.target.value as CommunicationObjective)}
                    className="w-full bg-slate-900 border border-slate-750 text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="inform">Inform</option>
                    <option value="brief">Brief</option>
                    <option value="explain">Explain</option>
                    <option value="persuade">Persuade</option>
                    <option value="prepare_action">Prepare Action</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Top-K Context Chunks</label>
                  <select
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                    className="w-full bg-slate-900 border border-slate-750 text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                  >
                    <option value={3}>3 chunks</option>
                    <option value={5}>5 chunks</option>
                    <option value={8}>8 chunks</option>
                    <option value={12}>12 chunks</option>
                  </select>
                </div>
              </div>

              {/* Length & Custom Focus */}
              <div className="space-y-2 pt-1 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Length / Format Bounds (Optional)</label>
                  <input
                    type="text"
                    value={lengthConstraint}
                    onChange={(e) => setLengthConstraint(e.target.value)}
                    placeholder="e.g. '5-7 slides', 'under 400 words', '90s script'"
                    className="w-full bg-slate-900 border border-slate-750 text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Custom Focus / Intent (Optional)</label>
                  <input
                    type="text"
                    value={customIntent}
                    onChange={(e) => setCustomIntent(e.target.value)}
                    placeholder="e.g. 'Focus on system architecture and vector indexing constraints'"
                    className="w-full bg-slate-900 border border-slate-750 text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>
            </div>

            {/* Action Button */}
            <button
              type="submit"
              disabled={isLoading || !selectedDocId}
              className={`w-full py-3 px-4 rounded-xl font-medium text-sm transition-all flex items-center justify-center gap-2 ${
                isLoading || !selectedDocId
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                  : "bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-xl shadow-indigo-600/30"
              }`}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Transforming Content (Grounding & LLM)...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Execute Multi-Format Transformation</span>
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Right Column: Output Viewer & Evidence (7 cols) */}
        <div className="lg:col-span-7 bg-slate-950/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between min-h-[520px]">
          {result ? (
            <div className="space-y-5">
              {/* Result Meta Bar */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div>
                  <span className="text-xs font-mono uppercase text-indigo-400 font-semibold tracking-wider">
                    {result.output_type.replace("_", " ")}
                  </span>
                  <div className="text-[11px] text-slate-400 flex items-center gap-3 mt-0.5">
                    <span className="flex items-center gap-1">
                      <Cpu className="w-3 h-3" /> {result.provider} / {result.model}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {result.generation_latency_ms.toFixed(0)}ms
                    </span>
                    <span className="flex items-center gap-1">
                      <Layers className="w-3 h-3" /> {result.number_of_retrieved_chunks} chunks used
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleVerify}
                    disabled={isVerifying}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition disabled:opacity-50"
                  >
                    {isVerifying ? (
                      <>
                        <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        <span>Verifying Claims...</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Verify Grounding</span>
                      </>
                    )}
                  </button>

                  <div className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono">
                    Schema Validated
                  </div>
                </div>
              </div>

              {/* Verification Error Alert */}
              {verificationError && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{verificationError}</span>
                </div>
              )}

              {/* Verification Report Card */}
              {verificationReport && (
                <VerificationReportCard
                  report={verificationReport}
                  onClose={() => setVerificationReport(null)}
                />
              )}

              {/* 1. EXECUTIVE SUMMARY RENDERER */}
              {result.output_type === "executive_summary" && (
                <div className="space-y-4 text-xs">
                  <h3 className="text-base font-bold text-slate-100">
                    {(result.content as ExecutiveSummaryContent).title}
                  </h3>

                  <div className="p-3.5 bg-slate-900/90 rounded-lg border border-slate-800 text-slate-300 leading-relaxed font-serif">
                    <span className="text-[10px] font-mono text-indigo-400 uppercase block mb-1">Strategic Overview</span>
                    {(result.content as ExecutiveSummaryContent).overview}
                  </div>

                  {/* Key Points */}
                  <div>
                    <h4 className="font-semibold text-slate-300 uppercase tracking-wider mb-2">Core Findings</h4>
                    <ul className="space-y-1.5">
                      {(result.content as ExecutiveSummaryContent).key_points.map((pt, i) => (
                        <li key={i} className="p-2 bg-slate-900/60 rounded border border-slate-800/80 text-slate-300 flex items-start gap-2">
                          <span className="text-indigo-400 font-bold">•</span>
                          <span>{pt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Important Facts */}
                  {(result.content as ExecutiveSummaryContent).important_facts?.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-slate-300 uppercase tracking-wider mb-2">Grounded Facts</h4>
                      <ul className="space-y-1 text-slate-400">
                        {(result.content as ExecutiveSummaryContent).important_facts.map((fact, i) => (
                          <li key={i} className="p-1.5 bg-slate-900/40 rounded border border-slate-800 text-slate-300">
                            - {fact}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Implications & Conclusion */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
                      <span className="text-[10px] font-mono text-amber-400 uppercase block mb-1">Implications</span>
                      <ul className="space-y-1 text-slate-400">
                        {(result.content as ExecutiveSummaryContent).implications.map((imp, i) => (
                          <li key={i}>• {imp}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
                      <span className="text-[10px] font-mono text-emerald-400 uppercase block mb-1">Conclusion</span>
                      <p className="text-slate-300 font-serif">{(result.content as ExecutiveSummaryContent).conclusion}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* 2. ADVISORY RENDERER */}
              {result.output_type === "advisory" && (
                <div className="space-y-4 text-xs">
                  <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    {(result.content as AdvisoryContent).title}
                  </h3>

                  <div className="p-3 bg-amber-950/20 border border-amber-800/40 rounded-lg text-amber-200/90 font-serif">
                    <span className="text-[10px] font-mono text-amber-400 uppercase block mb-1">Current Situation</span>
                    {(result.content as AdvisoryContent).situation}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg space-y-2">
                      <span className="text-[10px] font-mono text-indigo-400 uppercase block">Key Information</span>
                      <ul className="space-y-1 text-slate-300">
                        {(result.content as AdvisoryContent).key_information.map((k, i) => (
                          <li key={i}>• {k}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg space-y-2">
                      <span className="text-[10px] font-mono text-rose-400 uppercase block">Risks & Considerations</span>
                      <ul className="space-y-1 text-slate-300">
                        {(result.content as AdvisoryContent).risks_or_considerations.map((r, i) => (
                          <li key={i}>• {r}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Grounded Recommended Actions */}
                  <div className="p-3.5 bg-emerald-950/20 border border-emerald-800/40 rounded-lg space-y-2">
                    <span className="text-[10px] font-mono text-emerald-400 uppercase block font-bold">
                      Grounded Recommended Actions
                    </span>
                    <ul className="space-y-1.5 text-slate-200">
                      {(result.content as AdvisoryContent).recommended_actions.map((act, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <ChevronRight className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-2.5 bg-slate-900/60 rounded border border-slate-800 text-slate-400 text-[11px]">
                    <span className="text-slate-300 font-semibold">Conclusion:</span> {(result.content as AdvisoryContent).conclusion}
                  </div>
                </div>
              )}

              {/* 3. PRESENTATION RENDERER */}
              {result.output_type === "presentation" && (
                <div className="space-y-4 text-xs">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-slate-100">
                      {(result.content as PresentationContent).presentation_title}
                    </h3>
                    <span className="text-slate-400 font-mono text-[11px]">
                      Slide {activeSlideIdx + 1} of {(result.content as PresentationContent).slides.length}
                    </span>
                  </div>

                  {/* Slide Carousel Tabs */}
                  <div className="flex gap-1.5 overflow-x-auto pb-1">
                    {(result.content as PresentationContent).slides.map((s, idx) => (
                      <button
                        key={idx}
                        onClick={() => setActiveSlideIdx(idx)}
                        className={`px-3 py-1.5 rounded text-xs font-mono transition-all flex-shrink-0 ${
                          activeSlideIdx === idx
                            ? "bg-indigo-600 text-white font-bold shadow"
                            : "bg-slate-900 text-slate-400 hover:bg-slate-800"
                        }`}
                      >
                        Slide {s.slide_number}
                      </button>
                    ))}
                  </div>

                  {/* Active Slide Card */}
                  {(() => {
                    const slide = (result.content as PresentationContent).slides[activeSlideIdx];
                    if (!slide) return null;
                    return (
                      <div className="p-5 bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-xl space-y-4 shadow-xl">
                        <div className="border-b border-slate-800 pb-2">
                          <span className="text-[10px] font-mono text-indigo-400 uppercase">Slide {slide.slide_number}</span>
                          <h4 className="text-base font-bold text-white mt-0.5">{slide.title}</h4>
                        </div>

                        <ul className="space-y-2 pl-2">
                          {slide.bullets.map((b, i) => (
                            <li key={i} className="flex items-start gap-2 text-slate-200 text-xs">
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0"></span>
                              <span className="leading-relaxed">{b}</span>
                            </li>
                          ))}
                        </ul>

                        {slide.speaker_notes && (
                          <div className="mt-4 p-3 bg-slate-950/80 rounded-lg border border-slate-800/80">
                            <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1 flex items-center gap-1">
                              <Info className="w-3 h-3 text-indigo-400" /> Presenter Spoken Notes
                            </span>
                            <p className="text-slate-300 italic font-serif text-[11px] leading-relaxed">
                              &ldquo;{slide.speaker_notes}&rdquo;
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* 4. VIDEO SCRIPT RENDERER */}
              {result.output_type === "video_script" && (
                <div className="space-y-4 text-xs">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                      <Video className="w-4 h-4 text-purple-400" />
                      {(result.content as VideoScriptContent).title}
                    </h3>
                    <span className="px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/40 text-[11px] font-mono">
                      ⏱ Duration: {(result.content as VideoScriptContent).target_duration}
                    </span>
                  </div>

                  <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
                    {(result.content as VideoScriptContent).scenes.map((scene) => (
                      <div
                        key={scene.scene_number}
                        className="p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl space-y-2.5"
                      >
                        <div className="flex items-center justify-between text-[11px] border-b border-slate-800 pb-1.5">
                          <span className="font-mono font-bold text-purple-400">Scene #{scene.scene_number}</span>
                          {scene.on_screen_text && (
                            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                              📺 On-Screen: {scene.on_screen_text}
                            </span>
                          )}
                        </div>

                        <div className="text-[11px] text-slate-300 space-y-1.5">
                          <p className="text-slate-400">
                            <strong className="text-slate-300">Visual:</strong> {scene.visual_description}
                          </p>
                          <div className="p-2 bg-slate-950 rounded border border-slate-800/80 text-slate-200 font-serif italic">
                            &ldquo;{scene.narration}&rdquo;
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="my-auto text-center py-12 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto shadow-inner">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-slate-300">Transformation Studio Ready</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Select an uploaded document on the left, pick an output format (Executive Summary, Advisory, Presentation, or Video Script), configure target parameters, and execute generation.
              </p>
            </div>
          )}

          {/* Footer Evidence Banner */}
          {result && (
            <div className="border-t border-slate-800/80 pt-3 mt-4 text-[10px] text-slate-500 flex items-center justify-between font-mono">
              <span>Provenance: {result.source_references.length} source references linked</span>
              <span>Transformation ID: {result.transformation_id.slice(0, 8)}...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
