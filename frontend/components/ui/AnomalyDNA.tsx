"use client";

import React from "react";
import { Dna } from "lucide-react";

interface AnomalyDNASignals {
  rule_intensity?: number;       // 0 to 100
  distribution_intensity?: number; // 0 to 100
  cluster_intensity?: number;      // 0 to 100
  enumerator_intensity?: number;   // 0 to 100
  temporal_intensity?: number;     // 0 to 100
}

interface AnomalyDNAProps {
  signals?: AnomalyDNASignals;
}

export const AnomalyDNA: React.FC<AnomalyDNAProps> = ({
  signals = {
    rule_intensity: 85,
    distribution_intensity: 72,
    cluster_intensity: 90,
    enumerator_intensity: 65,
    temporal_intensity: 40
  }
}) => {
  const bars = [
    { key: "rule", label: "Rule Integrity", score: signals.rule_intensity || 0, color: "from-rose-600 to-rose-400", border: "border-rose-500/40" },
    { key: "distribution", label: "Distribution MAD/IQR", score: signals.distribution_intensity || 0, color: "from-sky-600 to-sky-400", border: "border-sky-500/40" },
    { key: "cluster", label: "Cluster Outlier (ML)", score: signals.cluster_intensity || 0, color: "from-indigo-600 to-indigo-400", border: "border-indigo-500/40" },
    { key: "enumerator", label: "Enumerator Fingerprint", score: signals.enumerator_intensity || 0, color: "from-amber-600 to-amber-400", border: "border-amber-500/40" },
    { key: "temporal", label: "Temporal Round Shift", score: signals.temporal_intensity || 0, color: "from-emerald-600 to-emerald-400", border: "border-emerald-500/40" },
  ];

  return (
    <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Dna className="w-4 h-4 text-indigo-400" />
          Anomaly DNA Profile (Multi-Vector Intensity)
        </h3>
        <span className="text-[11px] font-mono text-slate-500">Detector Vectors</span>
      </div>

      <div className="space-y-3.5">
        {bars.map(bar => (
          <div key={bar.key} className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300">{bar.label}</span>
              <span className="font-mono font-bold text-slate-200">{bar.score}%</span>
            </div>
            
            {/* Custom Horizontal Gradient Bar */}
            <div className="h-3.5 w-full bg-slate-900 rounded-full border border-slate-800/80 overflow-hidden p-0.5 relative">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${bar.color} transition-all duration-700 shadow-md`}
                style={{ width: `${Math.min(100, Math.max(0, bar.score))}%` }}
              />
              {/* Threshold Marker at 60% */}
              <div className="absolute top-0 bottom-0 left-[60%] w-0.5 bg-slate-700/80" title="Review Threshold (60%)" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
