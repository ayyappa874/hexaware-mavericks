"use client";

import React, { useEffect, useState } from "react";
import { Sliders, ArrowRight, CheckCircle2, TrendingDown, RefreshCw } from "lucide-react";

interface Recommendation {
  field: string;
  current_value: any;
  target_value: any;
  change_type: string;
  delta: string;
  rationale: string;
}

interface CounterfactualData {
  status: string;
  record_id: string;
  original_risk_score: number;
  projected_counterfactual_risk_score: number;
  risk_reduction: number;
  recommendations: Recommendation[];
}

interface CounterfactualPanelProps {
  recordId: string;
}

export const CounterfactualPanel: React.FC<CounterfactualPanelProps> = ({ recordId }) => {
  const [data, setData] = useState<CounterfactualData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const fetchCounterfactuals = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/records/${recordId}/counterfactual`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch (err) {
      console.error("Counterfactual fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (recordId) fetchCounterfactuals();
  }, [recordId]);

  if (loading) {
    return (
      <div className="glass-card p-6 rounded-2xl border border-slate-800 animate-pulse space-y-3">
        <div className="h-4 w-1/3 bg-slate-800 rounded" />
        <div className="h-16 bg-slate-900 rounded-xl" />
      </div>
    );
  }

  if (!data || !data.recommendations) return null;

  return (
    <div className="glass-card p-6 rounded-2xl border border-blue-500/30 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-100 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-blue-400" />
            Counterfactual Explanation (&quot;What needs to change for this record to be normal?&quot;)
          </h3>
          <p className="text-xs text-slate-400">Prescriptive minimal feature perturbations for 100% compliance</p>
        </div>

        {/* Projected Risk Reduction Pill */}
        <div className="flex items-center gap-3 bg-slate-900 px-4 py-2 rounded-xl border border-slate-800">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 block font-semibold uppercase">Risk Score Reduction</span>
            <span className="text-xs font-mono font-bold text-rose-400">{data.original_risk_score}</span>
            <span className="text-xs font-mono text-slate-400"> &rarr; </span>
            <span className="text-xs font-mono font-bold text-emerald-400">{data.projected_counterfactual_risk_score}</span>
          </div>
          <div className="p-2 bg-emerald-950/60 border border-emerald-800/60 text-emerald-400 rounded-lg">
            <TrendingDown className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Recommendations Cards */}
      <div className="space-y-3">
        {data.recommendations.map((rec, i) => (
          <div key={i} className="p-4 bg-slate-900/90 rounded-xl border border-slate-800 space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-mono font-bold text-blue-400 bg-blue-950/60 px-2.5 py-1 rounded border border-blue-800/40">
                Field: {rec.field}
              </span>
              <span className="text-[11px] font-mono text-rose-400 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-800/30">
                {rec.delta}
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs font-mono py-1">
              <span className="text-slate-400 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
                Original: <strong className="text-slate-200">{rec.current_value}</strong>
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-blue-400 shrink-0" />
              <span className="text-emerald-400 bg-emerald-950/40 px-2.5 py-1 rounded border border-emerald-800/60">
                Required Target: <strong className="text-emerald-300">{rec.target_value}</strong>
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed font-sans pt-1">
              <strong className="text-slate-300">Rationale:</strong> {rec.rationale}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
