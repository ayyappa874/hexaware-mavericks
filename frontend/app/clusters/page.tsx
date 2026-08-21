"use client";

import { useEffect, useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { SkeletonLoader } from "../../components/ui/SkeletonLoader";
import { EmptyState } from "../../components/ui/EmptyState";
import { Layers, AlertTriangle, ArrowRight, ShieldAlert, Cpu } from "lucide-react";

interface ClusterItem {
  cluster_name: string;
  record_count: number;
  avg_risk_score: number;
  primary_detector: string;
  sample_evidence: string;
  records: Array<{ id: string; record_id: string; score: number; severity: string }>;
}

export default function AnomalyClustersPage() {
  const [clusters, setClusters] = useState<ClusterItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const fetchClusters = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/clusters`);
      if (res.ok) {
        const data = await res.json();
        setClusters(data.clusters || []);
      }
    } catch (err) {
      console.error("Failed to load anomaly clusters:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClusters();
  }, []);

  return (
    <AppShell onRefresh={fetchClusters} loading={loading}>
      {() => (
        <div className="space-y-8 animate-in fade-in duration-200">
          {/* Header Banner */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-blue-500/30">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Layers className="w-7 h-7 text-blue-400" />
                <h1 className="text-2xl font-black text-slate-100">
                  Semantic Anomaly Clusters
                </h1>
              </div>
              <p className="text-xs text-slate-400 max-w-xl">
                Grouping microdata anomaly flags into root cause patterns (district wage skew, FSU digit preference, logical rule violations) instead of flat record lists.
              </p>
            </div>
          </div>

          {/* Clusters Grid */}
          {loading ? (
            <SkeletonLoader variant="card" count={3} />
          ) : clusters.length === 0 ? (
            <EmptyState
              title="No Anomaly Clusters"
              description="No anomaly clusters available."
              onAction={fetchClusters}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {clusters.map((c, idx) => (
                <div key={idx} className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4 hover:border-blue-500/40 transition-all">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/40">
                        {c.primary_detector} Cluster
                      </span>
                      <h2 className="text-base font-bold text-slate-100 mt-1">{c.cluster_name}</h2>
                    </div>

                    <span className="px-3 py-1 bg-slate-900 border border-slate-700 rounded-full font-mono text-xs font-bold text-slate-200">
                      {c.record_count} Records
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 bg-slate-950/60 p-3 rounded-xl border border-slate-800 font-mono">
                    <strong className="text-amber-400 font-sans">Root Evidence Pattern:</strong> {c.sample_evidence}
                  </p>

                  <div className="flex justify-between items-center pt-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400 font-semibold">Avg Risk:</span>
                      <span className={`px-2.5 py-0.5 rounded-full font-mono font-bold text-xs ${
                        c.avg_risk_score >= 70 ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-amber-950 text-amber-300 border border-amber-800'
                      }`}>
                        {c.avg_risk_score} / 100
                      </span>
                    </div>

                    <a
                      href={`/queue?cluster=${encodeURIComponent(c.cluster_name)}`}
                      className="text-xs font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      Investigate Cluster <ArrowRight className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
