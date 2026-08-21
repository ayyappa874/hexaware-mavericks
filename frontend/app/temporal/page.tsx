"use client";

import { useEffect, useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { SkeletonLoader } from "../../components/ui/SkeletonLoader";
import { EmptyState } from "../../components/ui/EmptyState";
import { TrendingUp, AlertTriangle, Filter, Layers } from "lucide-react";

export default function TemporalDriftPage() {
  const [driftData, setDriftData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [stateCode, setStateCode] = useState<string>("");

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const generateMockTemporalDrift = () => ({
    survey_round_current: "2024-25",
    survey_round_baseline: "2023-24",
    indicators: {
      lfpr_overall: 57.9,
      wpr_overall: 54.2,
      ur_overall: 3.2,
      lfpr_baseline: 56.4,
      wpr_baseline: 53.1,
      ur_baseline: 3.1
    },
    temporal_drift_alerts: [
      {
        state_code: "27",
        district_code: "005",
        indicator_name: "Unemployment Rate (UR)",
        current_value: 6.8,
        baseline_value: 3.1,
        z_score: 3.42,
        p_value: 0.0006,
        is_significant: true,
        causal_hypotheses: [
          "Regional economic shift or seasonal distress in District 005",
          "Enumerator preference clustering in FSU 27005"
        ]
      },
      {
        state_code: "19",
        district_code: "003",
        indicator_name: "Worker Population Ratio (WPR)",
        current_value: 48.2,
        baseline_value: 54.6,
        z_score: -2.85,
        p_value: 0.0044,
        is_significant: true,
        causal_hypotheses: [
          "Demographic activity status misclassification",
          "Under-reporting of female informal workers"
        ]
      }
    ]
  });

  const fetchDriftData = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/api/v1/dashboard/temporal-drift`;
      if (stateCode) url += `?state_code=${stateCode}`;
      const res = await fetch(url);
      if (res.ok) {
        setDriftData(await res.json());
        setLoading(false);
        return;
      }
    } catch (err) {
      console.warn("Backend API unreachable on Vercel, using in-browser mock temporal drift:", err);
    }

    setDriftData(generateMockTemporalDrift());
    setLoading(false);
  };

  useEffect(() => {
    fetchDriftData();
  }, [stateCode]);

  return (
    <AppShell onRefresh={fetchDriftData} loading={loading}>
      {() => (
        <div className="space-y-8 animate-in fade-in duration-200">
          {/* Header Banner */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-emerald-500/30">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-7 h-7 text-emerald-400" />
                <h1 className="text-2xl font-black text-slate-100">
                  Temporal Round Drift Monitor
                </h1>
              </div>
              <p className="text-xs text-slate-400 max-w-xl">
                Computes weighted official MoSPI PLFS aggregate indicators (LFPR, WPR, Unemployment Rate) per State and flags statistically significant shifts round-over-round.
              </p>
            </div>

            <div className="mt-4 md:mt-0 flex items-center gap-3">
              <select
                value={stateCode}
                onChange={(e) => setStateCode(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-slate-100 text-xs font-semibold rounded-xl px-3 py-2 outline-none"
              >
                <option value="">All States</option>
                <option value="07">State 07 (Delhi)</option>
                <option value="09">State 09 (Uttar Pradesh)</option>
                <option value="27">State 27 (Maharashtra)</option>
                <option value="19">State 19 (West Bengal)</option>
                <option value="33">State 33 (Tamil Nadu)</option>
                <option value="32">State 32 (Kerala)</option>
              </select>
            </div>
          </div>

          {/* Drift Analysis Table */}
          {loading ? (
            <SkeletonLoader variant="table" count={5} />
          ) : !driftData?.drift_analysis ? (
            <EmptyState
              title="No Temporal Drift Data"
              description="Unable to compute round-over-round indicator comparison."
              onAction={fetchDriftData}
            />
          ) : (
            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Round-over-Round Comparison ({driftData.baseline_round} vs {driftData.current_round})
                </span>
                <span className="text-[11px] text-slate-500 font-mono">Statistical Significance Z-Test Threshold (|Z| &ge; 2.0)</span>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">State Code</th>
                      <th className="py-3 px-4">LFPR (% 15+ Pop in Labour Force)</th>
                      <th className="py-3 px-4">WPR (% 15+ Pop Employed)</th>
                      <th className="py-3 px-4">Unemployment Rate (UR %)</th>
                      <th className="py-3 px-4">Drift Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                    {driftData.drift_analysis.map((st: any) => {
                      const ind = st.indicators;
                      const hasSig = ind.lfpr.is_statistically_significant || ind.wpr.is_statistically_significant || ind.ur.is_statistically_significant;

                      return (
                        <tr key={st.state_code} className="hover:bg-slate-900/60 transition-colors">
                          <td className="py-3 px-4 font-bold text-slate-200">State {st.state_code}</td>
                          <td className="py-3 px-4">
                            {ind.lfpr.baseline}% &rarr; <strong className="text-slate-100">{ind.lfpr.current}%</strong> (
                            <span className={ind.lfpr.delta < 0 ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                              {ind.lfpr.delta > 0 ? '+' : ''}{ind.lfpr.delta}%
                            </span>, Z={ind.lfpr.z_score})
                          </td>
                          <td className="py-3 px-4">
                            {ind.wpr.baseline}% &rarr; <strong className="text-slate-100">{ind.wpr.current}%</strong> (
                            <span className={ind.wpr.delta < 0 ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                              {ind.wpr.delta > 0 ? '+' : ''}{ind.wpr.delta}%
                            </span>, Z={ind.wpr.z_score})
                          </td>
                          <td className="py-3 px-4">
                            {ind.ur.baseline}% &rarr; <strong className="text-slate-100">{ind.ur.current}%</strong> (
                            <span className={ind.ur.delta > 0 ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                              {ind.ur.delta > 0 ? '+' : ''}{ind.ur.delta}%
                            </span>, Z={ind.ur.z_score})
                          </td>
                          <td className="py-3 px-4 font-sans">
                            {hasSig ? (
                              <span className="px-2.5 py-1 bg-rose-950 text-rose-300 border border-rose-800 rounded font-bold text-[10px] flex items-center gap-1 w-fit animate-pulse">
                                <AlertTriangle className="w-3 h-3 text-rose-400" /> SIGNIFICANT DRIFT
                              </span>
                            ) : (
                              <span className="px-2.5 py-1 bg-slate-900 text-slate-400 border border-slate-800 rounded-full text-[10px]">
                                Stable Baseline
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
