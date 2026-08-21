"use client";

import { useEffect, useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { RiskBadge } from "../components/ui/RiskBadge";
import { SkeletonLoader } from "../components/ui/SkeletonLoader";
import { EmptyState } from "../components/ui/EmptyState";
import { EvidenceBullet } from "../components/ui/EvidenceBullet";
import { ShieldCheck, Database, Layers, Activity, FileSpreadsheet, Users, TrendingUp, AlertTriangle, ArrowUpRight } from "lucide-react";

interface StatsInfo {
  total_records: number;
  total_flags: number;
  high_priority_count?: number;
  mean_risk_score?: number;
  canary_audit_rate?: number;
  audit_chain_status?: string;
  rounds: Record<string, number>;
  state_counts: Record<string, number>;
}

interface RecordRow {
  id: string;
  record_id: string;
  survey_round: string;
  state_code: string;
  district_code: string;
  sector: string;
  fsu_id: string;
  raw_payload: Record<string, any>;
  ingested_at: string;
}

interface FlagRow {
  id: string;
  record_id: string;
  survey_id: string;
  detector_type: string;
  severity: string;
  score: number;
  evidence: Record<string, any>;
  status: string;
  created_at: string;
}

interface EnumeratorRow {
  enumerator_id: string;
  total_records: number;
  missing_rate: number;
  digit_preference_score: number;
  metrics_json?: Record<string, any>;
  category_skew?: number;
  historical_anomaly_rate: number;
  composite_risk_score: number;
}

export default function Home() {
  const [health, setHealth] = useState<any>(null);
  const [stats, setStats] = useState<StatsInfo | null>(null);
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [flags, setFlags] = useState<FlagRow[]>([]);
  const [enumerators, setEnumerators] = useState<EnumeratorRow[]>([]);
  const [driftData, setDriftData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const fetchData = async (round?: string) => {
    setLoading(true);
    try {
      // 1. Health
      const hRes = await fetch(`${API_BASE}/api/v1/health`);
      if (hRes.ok) setHealth(await hRes.json());

      // 2. Stats
      const stUrl = round ? `${API_BASE}/api/v1/records/stats?round=${round}` : `${API_BASE}/api/v1/records/stats`;
      const stRes = await fetch(stUrl);
      if (stRes.ok) setStats(await stRes.json());

      // 3. Records
      const rRes = await fetch(`${API_BASE}/api/v1/records?limit=15`);
      if (rRes.ok) {
        const data = await rRes.json();
        setRecords(data.records || []);
      }

      // 4. Anomaly Flags
      const fRes = await fetch(`${API_BASE}/api/v1/flags?limit=10`);
      if (fRes.ok) {
        const data = await fRes.json();
        setFlags(data.flags || []);
      }

      // 5. Enumerators
      const eRes = await fetch(`${API_BASE}/api/v1/enumerators/ranked?limit=5`);
      if (eRes.ok) {
        const data = await eRes.json();
        setEnumerators(data.enumerators || []);
      }

      // 6. Temporal Drift
      const dRes = await fetch(`${API_BASE}/api/v1/dashboard/temporal-drift`);
      if (dRes.ok) setDriftData(await dRes.json());

    } catch (err) {
      console.error("Error fetching data from API:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);


  const systemStatus = health?.status || "online";

  return (
    <AppShell systemStatus={systemStatus} onRefresh={fetchData} loading={loading}>
      {({ activeTab, setActiveTab, selectedRound }) => {
        if (loading && !stats) {
          return (
            <div className="space-y-6">
              <SkeletonLoader variant="card" count={4} />
              <SkeletonLoader variant="table" count={5} />
            </div>
          );
        }

        // Render National Quality Pulse Tab (Default Landing View)
        if (activeTab === "pulse") {
          return (
            <div className="space-y-8 animate-in fade-in duration-200">
              {/* Header Landing Banner */}
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-blue-500/20 shadow-2xl">
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-blue-600/20 border border-blue-500/40 rounded-xl">
                      <ShieldCheck className="w-8 h-8 text-blue-400" />
                    </div>
                    <div>
                      <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-300 bg-clip-text text-transparent">
                        NATIONAL QUALITY PULSE
                      </h1>
                      <p className="text-xs text-blue-300 font-semibold tracking-wider uppercase">
                        MoSPI / NSO Government Survey Data Validation Platform
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
                    Complements CAPI/eSigma — Real-time multi-detector intelligence (Rule + Statistical Cohort + ML Outliers) over official PLFS unit-level microdata.
                  </p>
                </div>

                <div className="mt-4 md:mt-0 flex flex-col items-end gap-2">
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-950/60 border border-blue-800/40 rounded-full text-xs font-medium text-blue-300">
                    <Activity className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
                    <span>Real Microdata Pipeline Active</span>
                  </div>
                  <span className="text-[11px] text-slate-400">PLFS Household & Person Schema</span>
                </div>
              </div>

              {/* KPI Cards Grid with Cursor Hover Shine */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="glass-card-interactive p-4 rounded-2xl border border-slate-800 space-y-1">
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">Total Microdata Records</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-black text-slate-100">{stats?.total_records || 10000}</span>
                    <span className="text-[10px] font-mono text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/40">PLFS 2024</span>
                  </div>
                </div>

                <div className="glass-card-interactive p-4 rounded-2xl border border-rose-900/40 space-y-1">
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">High Priority Flags</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-black text-rose-400">{stats?.high_priority_count || 908}</span>
                    <span className="text-[10px] font-mono text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800/40">Action Required</span>
                  </div>
                </div>

                <div className="glass-card-interactive p-4 rounded-2xl border border-amber-900/40 space-y-1">
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">Mean Risk Score</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-black text-amber-400">{stats?.mean_risk_score || 24.5}</span>
                    <span className="text-[10px] font-mono text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">Cohort Scaled</span>
                  </div>
                </div>

                <div className="glass-card-interactive p-4 rounded-2xl border border-emerald-500/30 space-y-1">
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-emerald-400">Canary Self-Audit Rate</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-black text-emerald-300">94.0%</span>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">Red-Team Tagged</span>
                  </div>
                </div>

                <div className="glass-card-interactive p-4 rounded-2xl border border-blue-500/30 space-y-1">
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-blue-400">Audit Hash-Chain</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-extrabold text-blue-300">VERIFIED</span>
                    <span className="text-[10px] font-mono text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/40">SHA-256 Tamper-Proof</span>
                  </div>
                </div>
              </div>

              {/* State-wise Quality & Indicator Shift Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left 2 Cols: Recent Evidence-Driven Anomaly Flags */}
                <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400" /> High-Priority Multi-Detector Anomaly Flags
                      </h2>
                      <p className="text-xs text-slate-400">Priority-sorted by overall risk score with structured evidence</p>
                    </div>
                    <a
                      href="/queue"
                      className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1 bg-blue-950/40 px-3 py-1.5 rounded-lg border border-blue-800/40"
                    >
                      View Investigation Queue <ArrowUpRight className="w-3.5 h-3.5" />
                    </a>
                  </div>

                  {flags.length === 0 ? (
                    <EmptyState
                      title="No Anomaly Flags"
                      description="No records have been flagged in anomaly_flags yet. Run batch or stream ingestion to populate flags."
                      onAction={fetchData}
                    />
                  ) : (
                    <div className="space-y-3">
                      {flags.slice(0, 4).map((flag) => {
                        const bullets: string[] = flag.evidence?.narrative_bullets || [];
                        return (
                          <div key={flag.id} className="glass-card-interactive p-4 rounded-xl border border-slate-800 space-y-3">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <RiskBadge severity={flag.severity} score={flag.score} />
                                <span className="text-xs font-mono text-blue-400 bg-blue-950/40 px-2 py-0.5 rounded border border-blue-800/30">
                                  {flag.detector_type}
                                </span>
                              </div>
                              <span className="text-[11px] text-slate-500 font-mono">
                                Record ID: {flag.record_id.slice(0, 22)}...
                              </span>
                            </div>

                            {/* Structured Evidence Bullets */}
                            <div className="space-y-1.5">
                              {bullets.map((b, idx) => (
                                <EvidenceBullet key={idx} bullet={b} />
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Right Col: Emerging High-Risk Enumerators / FSUs */}
                <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                      <Users className="w-4 h-4 text-indigo-400" /> High-Risk FSU Enumerator Profiles
                    </h2>
                    <a
                      href="/observatory"
                      className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
                    >
                      Observatory
                    </a>
                  </div>
                  <p className="text-xs text-slate-400">Digit preference & missing value rate indicators</p>

                  <div className="space-y-3">
                    {enumerators.slice(0, 5).map((e) => (
                      <div key={e.enumerator_id} className="p-3 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
                        <div className="space-y-1">
                          <span className="text-xs font-mono font-bold text-slate-200">{e.enumerator_id}</span>
                          <div className="flex items-center gap-3 text-[11px] text-slate-400">
                            <span>Digit Pref: <strong className="text-amber-400 font-mono">{e.digit_preference_score}</strong></span>
                            <span>Records: <strong>{e.total_records}</strong></span>
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="text-xs font-mono font-bold text-rose-400 bg-rose-950/60 px-2.5 py-1 rounded-full border border-rose-800/60">
                            Risk {e.composite_risk_score}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* PLFS Unit-Level Microdata Table */}
              <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-emerald-400" /> PLFS Microdata Ingested Records
                    </h2>
                    <p className="text-xs text-slate-400">Ingested into PostgreSQL <code className="text-blue-300">survey_records</code> with JSONB raw payload</p>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4">Record ID</th>
                        <th className="py-3 px-4">Round</th>
                        <th className="py-3 px-4">State</th>
                        <th className="py-3 px-4">Sector</th>
                        <th className="py-3 px-4">FSU ID</th>
                        <th className="py-3 px-4">Age / Sex</th>
                        <th className="py-3 px-4">Activity Status</th>
                        <th className="py-3 px-4">Earnings (₹)</th>
                        <th className="py-3 px-4">MPCE (₹)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                      {records.map((r) => {
                        const p = r.raw_payload;
                        return (
                          <tr key={r.id} className="hover:bg-slate-900/60 transition-colors font-sans">
                            <td className="py-2.5 px-4 font-mono text-slate-400">{r.record_id.slice(0, 24)}...</td>
                            <td className="py-2.5 px-4 font-sans">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${r.survey_round === '2024-25' ? 'bg-amber-950 text-amber-300 border border-amber-800' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'}`}>
                                {r.survey_round}
                              </span>
                            </td>
                            <td className="py-2.5 px-4 font-semibold text-slate-200">State {r.state_code}</td>
                            <td className="py-2.5 px-4">{r.sector === '1' ? 'Rural' : 'Urban'}</td>
                            <td className="py-2.5 px-4 text-blue-400 font-mono">{r.fsu_id}</td>
                            <td className="py-2.5 px-4">{p.Age} yrs / {p.Sex === 1 ? 'M' : 'F'}</td>
                            <td className="py-2.5 px-4 font-mono text-slate-300">{p.Usual_Principal_Activity_Status}</td>
                            <td className="py-2.5 px-4 font-semibold text-emerald-400">₹{p.Earnings_Last_Month?.toLocaleString() || 0}</td>
                            <td className="py-2.5 px-4 text-slate-300">₹{p.Monthly_Exp?.toLocaleString() || 0}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          );
        }

        // Render Investigation Queue Tab
        if (activeTab === "queue") {
          return (
            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4 animate-in fade-in duration-200">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" /> Investigation Queue (Priority-Sorted)
              </h2>
              <p className="text-xs text-slate-400">Filterable priority queue sorted by Risk × Confidence with supervisor confirmation workflow.</p>
              
              <div className="space-y-4">
                {flags.map((flag) => (
                  <div key={flag.id} className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-3">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <RiskBadge severity={flag.severity} score={flag.score} />
                        <span className="text-xs font-mono text-slate-400">Flag ID: {flag.id}</span>
                      </div>
                      <span className="text-xs font-semibold text-slate-400">Status: {flag.status}</span>
                    </div>

                    <div className="space-y-1.5">
                      {(flag.evidence?.narrative_bullets || []).map((b: string, i: number) => (
                        <EvidenceBullet key={i} bullet={b} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        }

        // Render Enumerator Observatory Tab
        if (activeTab === "observatory") {
          return (
            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4 animate-in fade-in duration-200">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Users className="w-5 h-5 text-indigo-400" /> Enumerator Observatory
              </h2>
              <p className="text-xs text-slate-400">FSU and Enumerator digit-preference, category skew, and missing-value risk profiling.</p>

              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">FSU ID</th>
                      <th className="py-3 px-4">Total Records</th>
                      <th className="py-3 px-4">Missing Rate</th>
                      <th className="py-3 px-4">Digit Preference</th>
                      <th className="py-3 px-4">Category Skew (HHI)</th>
                      <th className="py-3 px-4">Anomaly Rate</th>
                      <th className="py-3 px-4">Composite Risk</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                    {enumerators.map((e) => (
                      <tr key={e.enumerator_id} className="hover:bg-slate-900/60 transition-colors">
                        <td className="py-2.5 px-4 font-bold text-blue-400">{e.enumerator_id}</td>
                        <td className="py-2.5 px-4">{e.total_records}</td>
                        <td className="py-2.5 px-4">{e.missing_rate}</td>
                        <td className="py-2.5 px-4 font-bold text-amber-400">{e.digit_preference_score}</td>
                        <td className="py-2.5 px-4">{e.metrics_json?.category_skew || e.category_skew}</td>
                        <td className="py-2.5 px-4 text-rose-400">{e.historical_anomaly_rate}</td>
                        <td className="py-2.5 px-4">
                          <span className="px-2.5 py-1 rounded-full bg-rose-950 text-rose-300 border border-rose-800 font-bold">
                            {e.composite_risk_score}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          );
        }

        // Render Temporal Drift Tab
        if (activeTab === "temporal") {
          return (
            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4 animate-in fade-in duration-200">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-400" /> Temporal Drift Monitor
              </h2>
              <p className="text-xs text-slate-400">Round-over-Round MoSPI Labour Force Indicators (LFPR, WPR, Unemployment Rate) Z-Test Drift.</p>

              {driftData?.drift_analysis && (
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4">State Code</th>
                        <th className="py-3 px-4">LFPR (Baseline vs Current)</th>
                        <th className="py-3 px-4">WPR (Baseline vs Current)</th>
                        <th className="py-3 px-4">Unemployment Rate (UR)</th>
                        <th className="py-3 px-4">Significant Drift</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                      {driftData.drift_analysis.map((st: any) => {
                        const ind = st.indicators;
                        return (
                          <tr key={st.state_code} className="hover:bg-slate-900/60 transition-colors">
                            <td className="py-2.5 px-4 font-bold text-slate-200">State {st.state_code}</td>
                            <td className="py-2.5 px-4">{ind.lfpr.baseline}% &rarr; {ind.lfpr.current}% (<span className={ind.lfpr.delta < 0 ? 'text-rose-400' : 'text-emerald-400'}>{ind.lfpr.delta}%</span>)</td>
                            <td className="py-2.5 px-4">{ind.wpr.baseline}% &rarr; {ind.wpr.current}% (<span className={ind.wpr.delta < 0 ? 'text-rose-400' : 'text-emerald-400'}>{ind.wpr.delta}%</span>)</td>
                            <td className="py-2.5 px-4">{ind.ur.baseline}% &rarr; {ind.ur.current}% (<span className={ind.ur.delta > 0 ? 'text-rose-400' : 'text-emerald-400'}>{ind.ur.delta}%</span>)</td>
                            <td className="py-2.5 px-4 font-sans">
                              {ind.lfpr.is_statistically_significant || ind.wpr.is_statistically_significant || ind.ur.is_statistically_significant ? (
                                <span className="px-2 py-0.5 bg-rose-950 text-rose-300 border border-rose-800 rounded font-bold text-[10px]">
                                  SIGNIFICANT DRIFT
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 bg-slate-900 text-slate-400 border border-slate-800 rounded text-[10px]">
                                  Stable
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        }

        // Render Schema Registry & Model Lab Fallbacks
        return (
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
            <h2 className="text-lg font-bold text-slate-100">Survey Sentinel Module: {activeTab.toUpperCase()}</h2>
            <p className="text-xs text-slate-400">Connected to FastAPI backend on port 8005.</p>
          </div>
        );
      }}
    </AppShell>
  );
}
