"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchSystemHealth } from "@/lib/api";
import { SystemHealthResponse } from "@/types/health";
import { Activity, Database, Server, RefreshCw, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";

export const SystemStatusCard: React.FC = () => {
  const [healthData, setHealthData] = useState<SystemHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSystemHealth();
      setHealthData(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to connect to backend service");
      }
      setHealthData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 15000); // refresh every 15s
    return () => clearInterval(interval);
  }, [loadStatus]);

  return (
    <div className="w-full max-w-4xl bg-slate-900/80 backdrop-blur border border-slate-800 rounded-xl p-6 shadow-2xl">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-4 mb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400 animate-pulse" />
            <h2 className="text-lg font-semibold text-slate-100">Live Infrastructure Telemetry</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time diagnostics for Backend API, PostgreSQL (pgvector), and Redis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-slate-500">Updated: {lastUpdated}</span>
          )}
          <button
            onClick={loadStatus}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 rounded-lg transition-colors border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-rose-950/50 border border-rose-800/80 rounded-lg flex items-start gap-3">
          <XCircle className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <p className="font-semibold text-rose-200">Backend Connection Error</p>
            <p className="text-rose-300/80 text-xs mt-0.5">{error}</p>
            <p className="text-slate-400 text-xs mt-2">
              Ensure the FastAPI backend is running at <code className="text-slate-300">http://localhost:8000</code> or within Docker network.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Backend API Service */}
        <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-sky-400" />
              <span className="text-sm font-medium text-slate-200">FastAPI Backend</span>
            </div>
            {healthData ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
                <CheckCircle2 className="w-3 h-3" /> Online
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-950 text-rose-400 border border-rose-800">
                <XCircle className="w-3 h-3" /> Offline
              </span>
            )}
          </div>
          <div className="text-xs text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Environment:</span>
              <span className="text-slate-200 font-mono">{healthData?.environment || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span>Version:</span>
              <span className="text-slate-200 font-mono">{healthData?.version || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span>Endpoints:</span>
              <span className="text-slate-200 font-mono">/api/v1/health</span>
            </div>
          </div>
        </div>

        {/* PostgreSQL Database + pgvector */}
        <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              <span className="text-sm font-medium text-slate-200">PostgreSQL (pgvector)</span>
            </div>
            {healthData?.database.connected ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
                <CheckCircle2 className="w-3 h-3" /> Ready
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-950 text-amber-400 border border-amber-800">
                <AlertTriangle className="w-3 h-3" /> {healthData ? "Unreachable" : "Unknown"}
              </span>
            )}
          </div>
          <div className="text-xs text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Latency:</span>
              <span className="text-slate-200 font-mono">
                {healthData?.database.latency_ms !== undefined ? `${healthData.database.latency_ms} ms` : "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>pgvector Ext:</span>
              <span className={`font-mono ${healthData?.database.pgvector_installed ? "text-emerald-400" : "text-amber-400"}`}>
                {healthData?.database.pgvector_installed
                  ? `Installed (v${healthData.database.pgvector_version || "enabled"})`
                  : "Not Detected"}
              </span>
            </div>
            {healthData?.database.error && (
              <div className="text-rose-400 text-[11px] truncate pt-1">
                Err: {healthData.database.error}
              </div>
            )}
          </div>
        </div>

        {/* Redis Cache */}
        <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-red-400" />
              <span className="text-sm font-medium text-slate-200">Redis Cache</span>
            </div>
            {healthData?.redis.connected ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
                <CheckCircle2 className="w-3 h-3" /> Ready
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-950 text-amber-400 border border-amber-800">
                <AlertTriangle className="w-3 h-3" /> {healthData ? "Unreachable" : "Unknown"}
              </span>
            )}
          </div>
          <div className="text-xs text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Latency:</span>
              <span className="text-slate-200 font-mono">
                {healthData?.redis.latency_ms !== undefined ? `${healthData.redis.latency_ms} ms` : "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Role:</span>
              <span className="text-slate-200">Cache / Worker Queue</span>
            </div>
            {healthData?.redis.error && (
              <div className="text-rose-400 text-[11px] truncate pt-1">
                Err: {healthData.redis.error}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
