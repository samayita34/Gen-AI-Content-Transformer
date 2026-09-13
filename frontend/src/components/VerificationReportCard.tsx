"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Clock,
  Layers,
  Info,
} from "lucide-react";
import { VerificationReport, VerificationVerdict } from "@/types/verification";

interface VerificationReportCardProps {
  report: VerificationReport;
  onClose?: () => void;
}

export function VerificationReportCard({ report, onClose }: VerificationReportCardProps) {
  const [selectedVerdictFilter, setSelectedVerdictFilter] = useState<string>("all");
  const [expandedClaimIds, setExpandedClaimIds] = useState<Set<string>>(new Set());

  const toggleClaimExpand = (id: string) => {
    setExpandedClaimIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const getVerdictBadge = (verdict: VerificationVerdict) => {
    switch (verdict) {
      case "supported":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Supported
          </span>
        );
      case "contradicted":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" />
            Contradicted
          </span>
        );
      case "partially_supported":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3.5 h-3.5" />
            Partially Supported
          </span>
        );
      case "insufficient_evidence":
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            <HelpCircle className="w-3.5 h-3.5" />
            Insufficient Evidence
          </span>
        );
    }
  };

  const filteredClaims = report.claim_results.filter((c) => {
    if (selectedVerdictFilter === "all") return true;
    return c.verdict === selectedVerdictFilter;
  });

  return (
    <div className="rounded-2xl border border-indigo-500/30 bg-slate-900/90 backdrop-blur-xl p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Verification Summary
              <span className="text-xs font-normal text-slate-400">
                ({report.output_type.replace(/_/g, " ").toUpperCase()})
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Independent evidence retrieved from source chunks. Lack of evidence is not treated as contradiction.
            </p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 transition"
          >
            Dismiss
          </button>
        )}
      </div>

      {/* Raw Operational Counts Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <button
          onClick={() => setSelectedVerdictFilter("all")}
          className={`p-3.5 rounded-xl border text-left transition ${
            selectedVerdictFilter === "all"
              ? "bg-slate-800 border-indigo-500/50 shadow-md"
              : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40"
          }`}
        >
          <div className="text-xs text-slate-400 font-medium">Analyzed</div>
          <div className="text-xl font-black text-white mt-1">{report.total_claims}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Total claims</div>
        </button>

        <button
          onClick={() => setSelectedVerdictFilter("supported")}
          className={`p-3.5 rounded-xl border text-left transition ${
            selectedVerdictFilter === "supported"
              ? "bg-emerald-950/40 border-emerald-500/60 shadow-md"
              : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40"
          }`}
        >
          <div className="text-xs text-emerald-400 font-medium flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Supported
          </div>
          <div className="text-xl font-black text-emerald-300 mt-1">{report.supported_claims}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Source-supported</div>
        </button>

        <button
          onClick={() => setSelectedVerdictFilter("contradicted")}
          className={`p-3.5 rounded-xl border text-left transition ${
            selectedVerdictFilter === "contradicted"
              ? "bg-rose-950/40 border-rose-500/60 shadow-md"
              : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40"
          }`}
        >
          <div className="text-xs text-rose-400 font-medium flex items-center gap-1">
            <XCircle className="w-3 h-3" /> Contradicted
          </div>
          <div className="text-xl font-black text-rose-300 mt-1">{report.contradicted_claims}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Conflict detected</div>
        </button>

        <button
          onClick={() => setSelectedVerdictFilter("partially_supported")}
          className={`p-3.5 rounded-xl border text-left transition ${
            selectedVerdictFilter === "partially_supported"
              ? "bg-amber-950/40 border-amber-500/60 shadow-md"
              : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40"
          }`}
        >
          <div className="text-xs text-amber-400 font-medium flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> Partial
          </div>
          <div className="text-xl font-black text-amber-300 mt-1">{report.partially_supported_claims}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Subset supported</div>
        </button>

        <button
          onClick={() => setSelectedVerdictFilter("insufficient_evidence")}
          className={`p-3.5 rounded-xl border text-left transition ${
            selectedVerdictFilter === "insufficient_evidence"
              ? "bg-slate-800 border-slate-500/60 shadow-md"
              : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40"
          }`}
        >
          <div className="text-xs text-slate-400 font-medium flex items-center gap-1">
            <HelpCircle className="w-3 h-3" /> Insufficient
          </div>
          <div className="text-xl font-black text-slate-300 mt-1">{report.insufficient_evidence_claims}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Lack of evidence</div>
        </button>
      </div>

      {/* Claim-by-Claim Inspection List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span>Claim Breakdown ({filteredClaims.length})</span>
          <span className="text-[11px] font-normal text-slate-500 lowercase">
            showing {selectedVerdictFilter}
          </span>
        </div>

        {filteredClaims.length === 0 ? (
          <div className="text-center py-8 rounded-xl bg-slate-950/40 border border-slate-800 text-slate-500 text-xs">
            No claims match the selected filter.
          </div>
        ) : (
          filteredClaims.map((cr, idx) => {
            const isExpanded = expandedClaimIds.has(cr.claim.claim_id);
            return (
              <div
                key={cr.claim.claim_id || idx}
                className="rounded-xl border border-slate-800 bg-slate-950/50 hover:border-slate-700/80 transition overflow-hidden"
              >
                {/* Claim Header Row */}
                <div
                  onClick={() => toggleClaimExpand(cr.claim.claim_id)}
                  className="p-4 cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 select-none"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {getVerdictBadge(cr.verdict)}
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
                        {cr.claim.context_source_field}
                      </span>
                      <span className="text-[10px] uppercase font-semibold text-slate-500">
                        {cr.claim.claim_type}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-slate-200 leading-relaxed">
                      {cr.claim.statement}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-center">
                    {cr.confidence !== null && cr.confidence !== undefined && (
                      <span className="text-xs text-slate-400">
                        Confidence: {(cr.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                    <button className="p-1 rounded text-slate-400 hover:text-white">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Expandable Explanation & Evidence */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-2 border-t border-slate-800/80 bg-slate-900/40 space-y-3 text-xs">
                    {/* Explanation */}
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/60 text-slate-300 leading-relaxed">
                      <span className="font-semibold text-indigo-400">Judge Explanation: </span>
                      {cr.explanation}
                    </div>

                    {/* Independently Retrieved Evidence Matches */}
                    <div>
                      <div className="text-[11px] font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-indigo-400" />
                        Independently Retrieved Source Evidence ({cr.evidence.length})
                      </div>

                      {cr.evidence.length === 0 ? (
                        <div className="text-slate-500 italic p-2 bg-slate-950/30 rounded border border-slate-800/40">
                          No independent evidence chunk met the retrieval threshold.
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {cr.evidence.map((ev, eIdx) => (
                            <div
                              key={ev.chunk_id || eIdx}
                              className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1.5"
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400 border-b border-slate-800/60 pb-1.5">
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold text-slate-300">
                                    Chunk #{eIdx + 1}
                                  </span>
                                  {ev.section_title && (
                                    <span className="text-indigo-400 font-medium">
                                      § {ev.section_title}
                                    </span>
                                  )}
                                  {ev.page_number && (
                                    <span className="text-slate-500">
                                      Page {ev.page_number}
                                    </span>
                                  )}
                                  {ev.formatted_timestamp && (
                                    <span className="text-amber-400 flex items-center gap-0.5">
                                      <Clock className="w-3 h-3" />
                                      {ev.formatted_timestamp}
                                    </span>
                                  )}
                                </div>
                                <span className="font-mono text-emerald-400">
                                  Cosine Sim: {(ev.similarity_score * 100).toFixed(1)}%
                                </span>
                              </div>

                              <p className="text-xs text-slate-300 font-serif leading-relaxed italic">
                                &quot;{ev.chunk_content}&quot;
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Operational Disclaimer Footer */}
      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-2.5 text-[11px] text-slate-400">
        <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Operational Verification Notice: </span>
          This report presents operational claim-level retrieval telemetry against source chunks. Formal factual consistency and benchmark precision/recall evaluations are reserved for Milestone 7.
        </div>
      </div>
    </div>
  );
}
