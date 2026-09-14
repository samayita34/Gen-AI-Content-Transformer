"use client";

import React, { useState, useEffect } from "react";
import { fetchResearchSummary } from "@/lib/api";
import { ResearchSummaryResponse } from "@/types/research";
import {
  FlaskConical,
  AlertTriangle,
  Info,
  CheckCircle2,
  Layers,
  Clock,
  RefreshCw,
  GitCompare,
  BarChart3,
  Sliders,
} from "lucide-react";

export function ResearchEvaluationDashboard() {
  const [data, setData] = useState<ResearchSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTrack, setActiveTrack] = useState<"track1" | "track2" | "track3">("track1");

  const loadSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchResearchSummary();
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load research evaluation summary";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header & Reload */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-indigo-400" />
            Milestone 7: Quantitative Research Evaluation Framework
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Empirical evaluation isolating generation factual consistency, claim verification classification quality, and operational latency.
          </p>
        </div>

        <button
          onClick={loadSummary}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh Benchmark Data</span>
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto"></div>
          <p className="text-xs text-slate-400">Loading quantitative evaluation telemetry...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <div>
            <div className="font-semibold">Evaluation Data Unavailable</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {/* Empty State when no results exist */}
      {!isLoading && !error && data && !data.is_available && (
        <div className="p-8 text-center rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <BarChart3 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-300">
            {data.message || "No evaluation results available yet."}
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            To generate quantitative research evaluation telemetry, execute the benchmark harness:
          </p>
          <code className="inline-block px-3 py-1.5 rounded bg-slate-950 border border-slate-800 text-xs font-mono text-indigo-400">
            python research/experiments/run_generation_evaluation.py --dry-run
          </code>
        </div>
      )}

      {/* Benchmark Content when available */}
      {!isLoading && data && data.is_available && data.summary && (
        <div className="space-y-6">
          {/* Explicit Development Fixture Disclaimer Banner */}
          {data.is_development_fixture && (
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 text-amber-200 text-xs flex items-start gap-3 shadow-lg">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-bold text-amber-300 uppercase tracking-wider text-[11px]">
                  DEVELOPMENT FIXTURE &mdash; NOT RESEARCH RESULT
                </div>
                <p className="text-amber-200/90 leading-relaxed text-[11px]">
                  {data.fixture_disclaimer ||
                    "This benchmark summary was generated on synthetic development fixtures solely to calibrate schemas, metric algorithms, and statistical pipeline logic. Empirical research claims are reserved for real multi-document corpora."}
                </p>
              </div>
            </div>
          )}

          {/* Research Track Selector Tabs */}
          <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
            <button
              onClick={() => setActiveTrack("track1")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 ${
                activeTrack === "track1"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              <GitCompare className="w-4 h-4" />
              Track 1: Generation Quality (A vs B vs C)
            </button>

            <button
              onClick={() => setActiveTrack("track2")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 ${
                activeTrack === "track2"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              Track 2: Verification Quality (M6 Verifier)
            </button>

            <button
              onClick={() => setActiveTrack("track3")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 ${
                activeTrack === "track3"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              <Clock className="w-4 h-4" />
              Track 3: Operational Latency (A / B / C / D)
            </button>
          </div>

          {/* TRACK 1 VIEW */}
          {activeTrack === "track1" && (
            <div className="space-y-5">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 space-y-1.5">
                <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-indigo-400" />
                  Track 1 Experimental Design
                </div>
                <p className="text-slate-400 leading-relaxed">
                  Evaluates whether progressive architectural additions improve generation factual consistency:
                  <strong className="text-slate-300"> Method A</strong> (Direct Prompting) &rarr;
                  <strong className="text-slate-300"> Method B</strong> (Basic RAG) &rarr;
                  <strong className="text-slate-300"> Method C</strong> (RAG + Context Normalization).
                  <em className="text-amber-400/90 ml-1">Method D produces identical text to Method C and is evaluated strictly under Track 3.</em>
                </p>
              </div>

              {/* Descriptive Statistics Table */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-800 font-semibold text-xs text-slate-200 uppercase tracking-wider">
                  Descriptive Statistics (FSCR Metric)
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950/80 text-slate-400 font-mono text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-2.5">Method</th>
                        <th className="px-4 py-2.5">Architecture</th>
                        <th className="px-4 py-2.5 text-center">Sample (N)</th>
                        <th className="px-4 py-2.5 text-center">Mean FSCR</th>
                        <th className="px-4 py-2.5 text-center">Median FSCR</th>
                        <th className="px-4 py-2.5 text-center">Std Dev</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80 text-slate-300 font-mono">
                      {Object.entries(data.summary.track_1_generation_quality.descriptive_statistics).map(
                        ([method, stats]) => (
                          <tr key={method} className="hover:bg-slate-800/40">
                            <td className="px-4 py-2.5 font-bold text-indigo-400">{method}</td>
                            <td className="px-4 py-2.5 text-slate-400 font-sans">
                              {method === "METHOD_A" && "Direct LLM Prompting"}
                              {method === "METHOD_B" && "Basic RAG (pgvector)"}
                              {method === "METHOD_C" && "RAG + Structured Context Normalization"}
                              {method === "METHOD_D" && "RAG + Normalization + Verification"}
                            </td>
                            <td className="px-4 py-2.5 text-center">{stats.n}</td>
                            <td className="px-4 py-2.5 text-center text-slate-200">{stats.mean.toFixed(3)}</td>
                            <td className="px-4 py-2.5 text-center">{stats.median.toFixed(3)}</td>
                            <td className="px-4 py-2.5 text-center text-slate-400">{stats.std.toFixed(3)}</td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Ablation Deltas */}
              {data.summary.track_1_generation_quality.ablation_deltas.length > 0 && (
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
                  <div className="font-semibold text-xs text-slate-200 uppercase tracking-wider">
                    Ablation Step Transitions
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {data.summary.track_1_generation_quality.ablation_deltas.map((ab, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                        <div className="text-xs font-bold text-indigo-400">{ab.comparison}</div>
                        <div className="text-[11px] text-slate-400 flex items-center justify-between">
                          <span>Mean Delta ({ab.metric}):</span>
                          <span className="font-mono text-slate-200">{ab.mean_delta > 0 ? `+${ab.mean_delta.toFixed(3)}` : ab.mean_delta.toFixed(3)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TRACK 2 VIEW */}
          {activeTrack === "track2" && (
            <div className="space-y-5">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 space-y-1.5">
                <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-indigo-400" />
                  Track 2 Experimental Design
                </div>
                <p className="text-slate-400 leading-relaxed">
                  Evaluates the Milestone 6 claim-level verifier against labeled ground-truth claims across 4 discrete verdicts:
                  <strong className="text-emerald-400"> Supported</strong>,
                  <strong className="text-rose-400"> Contradicted</strong>,
                  <strong className="text-amber-400"> Partially Supported</strong>, and
                  <strong className="text-slate-400"> Insufficient Evidence</strong>.
                </p>
              </div>

              {/* Macro-F1 Metric Card */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="text-xs text-slate-400">4-Class Macro F1-Score</div>
                  <div className="text-2xl font-black text-indigo-400 font-mono">
                    {data.summary.track_2_verification_quality.macro_f1.toFixed(3)}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="text-xs text-slate-400">Binary Grouping F1</div>
                  <div className="text-2xl font-black text-emerald-400 font-mono">
                    {data.summary.track_2_verification_quality.binary_grouping.f1_score.toFixed(3)}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="text-xs text-slate-400">Benchmark Labeled Claims</div>
                  <div className="text-2xl font-black text-slate-200 font-mono">
                    {data.summary.track_2_verification_quality.binary_grouping.support}
                  </div>
                </div>
              </div>

              {/* Classification Report Table */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-800 font-semibold text-xs text-slate-200 uppercase tracking-wider">
                  Per-Class Classification Report
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950/80 text-slate-400 font-mono text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-2.5">Verdict Class</th>
                        <th className="px-4 py-2.5 text-center">Precision</th>
                        <th className="px-4 py-2.5 text-center">Recall</th>
                        <th className="px-4 py-2.5 text-center">F1-Score</th>
                        <th className="px-4 py-2.5 text-center">Support (N)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80 text-slate-300 font-mono">
                      {Object.entries(data.summary.track_2_verification_quality.classification_report).map(
                        ([verdict, rep]) => (
                          <tr key={verdict} className="hover:bg-slate-800/40">
                            <td className="px-4 py-2.5 font-bold uppercase text-slate-200">{verdict}</td>
                            <td className="px-4 py-2.5 text-center">{rep.precision.toFixed(3)}</td>
                            <td className="px-4 py-2.5 text-center">{rep.recall.toFixed(3)}</td>
                            <td className="px-4 py-2.5 text-center text-indigo-400 font-semibold">{rep.f1_score.toFixed(3)}</td>
                            <td className="px-4 py-2.5 text-center text-slate-400">{rep.support}</td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TRACK 3 VIEW */}
          {activeTrack === "track3" && (
            <div className="space-y-5">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 space-y-1.5">
                <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-indigo-400" />
                  Track 3 Operational Telemetry
                </div>
                <p className="text-slate-400 leading-relaxed">
                  Measures total system execution latency across all 4 experimental conditions, including retrieval, context normalization, generation, and claim-level verification overhead.
                </p>
              </div>

              {/* Latency Table */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-800 font-semibold text-xs text-slate-200 uppercase tracking-wider">
                  Total End-to-End Latency by Condition
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950/80 text-slate-400 font-mono text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-2.5">Method</th>
                        <th className="px-4 py-2.5">Pipeline Stages</th>
                        <th className="px-4 py-2.5 text-center">Mean Latency (ms)</th>
                        <th className="px-4 py-2.5 text-center">Median Latency (ms)</th>
                        <th className="px-4 py-2.5 text-center">Std Dev (ms)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80 text-slate-300 font-mono">
                      {Object.entries(data.summary.track_3_operational_latency.latency_by_method).map(
                        ([method, stats]) => (
                          <tr key={method} className="hover:bg-slate-800/40">
                            <td className="px-4 py-2.5 font-bold text-indigo-400">{method}</td>
                            <td className="px-4 py-2.5 text-slate-400 font-sans">
                              {method === "METHOD_A" && "Generation Only"}
                              {method === "METHOD_B" && "Dense Retrieval + Generation"}
                              {method === "METHOD_C" && "Retrieval + Normalization + Generation"}
                              {method === "METHOD_D" && "Retrieval + Normalization + Generation + Verification"}
                            </td>
                            <td className="px-4 py-2.5 text-center text-slate-200">{stats.mean.toFixed(1)}ms</td>
                            <td className="px-4 py-2.5 text-center">{stats.median.toFixed(1)}ms</td>
                            <td className="px-4 py-2.5 text-center text-slate-400">{stats.std.toFixed(1)}ms</td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Metadata Footer */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-500 flex flex-wrap items-center justify-between gap-2 font-mono">
            <span>Benchmark Version: {data.summary.benchmark_metadata.dataset_version}</span>
            <span>Total Evaluated Runs: {data.summary.benchmark_metadata.total_runs}</span>
            <span>Generated: {new Date(data.summary.benchmark_metadata.generated_at).toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  );
}
