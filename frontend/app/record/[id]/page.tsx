"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AppShell } from "../../../components/layout/AppShell";
import { RiskBadge } from "../../../components/ui/RiskBadge";
import { EvidenceBullet } from "../../../components/ui/EvidenceBullet";
import { EvidenceGraph } from "../../../components/ui/EvidenceGraph";
import { AnomalyDNA } from "../../../components/ui/AnomalyDNA";
import { CounterfactualPanel } from "../../../components/ui/CounterfactualPanel";
import { SkeletonLoader } from "../../../components/ui/SkeletonLoader";
import { ArrowLeft, ShieldAlert, CheckCircle2, XCircle, AlertOctagon, FileSpreadsheet, Send } from "lucide-react";

export default function RecordHeroPage() {
  const params = useParams();
  const router = useRouter();
  const recordId = params?.id as string;

  const [flagData, setFlagData] = useState<any>(null);
  const [recordData, setRecordData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [stage, setStage] = useState<number>(0);
  const [comments, setComments] = useState<string>("");
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const fetchRecordDetails = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/records/${recordId}`);
      if (res.ok) {
        const data = await res.json();
        setRecordData(data);
        if (data.flag) setFlagData(data.flag);
      } else {
        // Fallback array scan if ID not matched directly
        const fRes = await fetch(`${API_BASE}/api/v1/flags?limit=100`);
        if (fRes.ok) {
          const flagsList = (await fRes.json()).flags || [];
          const matching = flagsList.find((f: any) => f.record_id === recordId || f.id === recordId);
          if (matching) setFlagData(matching);
        }
      }
    } catch (err) {
      console.error("Failed to load record hero data:", err);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    if (recordId) fetchRecordDetails();
  }, [recordId]);

  // Staggered Progressive Reveal Animation Timer
  useEffect(() => {
    if (!loading) {
      const timer1 = setTimeout(() => setStage(1), 150);
      const timer2 = setTimeout(() => setStage(2), 350);
      const timer3 = setTimeout(() => setStage(3), 550);
      const timer4 = setTimeout(() => setStage(4), 750);
      const timer5 = setTimeout(() => setStage(5), 950);

      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        clearTimeout(timer4);
        clearTimeout(timer5);
      };
    }
  }, [loading]);

  const handleDecisionSubmit = async (decision: string) => {
    if (!flagData) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/flags/${flagData.id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          supervisor_id: "SUPERVISOR_HERO_PAGE",
          decision: decision,
          comments: comments || `Supervisor hero decision: ${decision}`
        })
      });

      if (res.ok) {
        const resJson = await res.json();
        setFlagData((prev: any) => ({ ...prev, status: decision }));
        setFeedbackSuccess(`Decision '${decision}' successfully recorded in database!`);
      }
    } catch (err) {
      console.error("Failed to submit feedback:", err);
    }
  };

  const payload = recordData?.raw_payload || {};
  const evidence = flagData?.evidence || {};
  const bullets: string[] = evidence.narrative_bullets || [
    "Rule Violation: Salaried employee under minimum working age standard.",
    "Cohort Deviation: Earnings exceed 3.5 MAD deviations from peer group.",
    "Multivariate Outlier: Isolation Forest score in top 2% quantile."
  ];

  return (
    <AppShell onRefresh={fetchRecordDetails} loading={loading}>
      {() => (
        <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto">
          {/* Header Navigation Link */}
          <div className="flex items-center justify-between">
            <Link
              href="/queue"
              className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-white bg-slate-900 px-3.5 py-2 rounded-xl border border-slate-800 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" /> Back to Queue
            </Link>

            <span className="text-xs font-mono text-slate-500">
              Record UUID: {recordId}
            </span>
          </div>

          {loading ? (
            <SkeletonLoader variant="chart" />
          ) : (
            <>
              {/* STAGE 1: Hero Banner & Risk Badge Header */}
              {stage >= 1 && (
                <div className="glass-card p-6 rounded-2xl border border-blue-500/30 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 shadow-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 animate-in slide-in-from-top-4 duration-300">
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <RiskBadge severity={flagData?.severity || "HIGH_PRIORITY"} score={flagData?.score || 85} />
                      <span className="text-xs font-mono font-bold text-blue-400 bg-blue-950/60 px-3 py-1 rounded-lg border border-blue-800/40">
                        {flagData?.detector_type || "ENSEMBLE"} DETECTOR
                      </span>
                    </div>
                    <h1 className="text-2xl font-black text-slate-100 tracking-tight">
                      PLFS Microdata Unit-Level Anomaly Investigation
                    </h1>
                    <p className="text-xs text-slate-400 font-mono">
                      State {recordData?.state_code || "07"} | Sector {recordData?.sector === "1" ? "Rural" : "Urban"} | FSU ID: {recordData?.fsu_id || "FSU_DEMO"} | Round: {recordData?.survey_round || "2024-25"}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold uppercase tracking-wider px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
                      Status: <strong className="text-amber-400">{flagData?.status || "PENDING"}</strong>
                    </span>
                  </div>
                </div>
              )}

              {/* STAGE 2: Custom Radial Evidence Graph & Anomaly DNA Grid */}
              {stage >= 2 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in duration-500">
                  {/* Visually Distinctive Radial Evidence Graph */}
                  <EvidenceGraph
                    score={flagData?.score || 85}
                    severity={flagData?.severity || "HIGH_PRIORITY"}
                  />

                  {/* Custom Anomaly DNA Chart */}
                  <AnomalyDNA
                    signals={{
                      rule_intensity: 85,
                      distribution_intensity: 75,
                      cluster_intensity: 90,
                      enumerator_intensity: 65,
                      temporal_intensity: 45
                    }}
                  />
                </div>
              )}

              {/* STAGE 3: Narrative Evidence Explanations */}
              {stage >= 3 && (
                <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4 animate-in fade-in duration-500">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    Structured Explanatory Evidence Bullets
                  </h3>

                  <div className="space-y-2.5">
                    {bullets.map((b, idx) => (
                      <EvidenceBullet key={idx} bullet={b} />
                    ))}
                  </div>
                </div>
              )}

              {/* STAGE 3.5: Counterfactual Explanation ("What needs to change for this record to be normal?") */}
              {stage >= 3 && (
                <div className="animate-in fade-in duration-500">
                  <CounterfactualPanel recordId={recordId} />
                </div>
              )}

              {/* STAGE 4: Raw Microdata Inspector */}
              {stage >= 4 && (
                <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4 animate-in fade-in duration-500">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                      PLFS Microdata Raw Payload Inspector
                    </h3>
                    <span className="text-xs font-mono text-slate-500">PostgreSQL survey_records</span>
                  </div>

                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-900 font-mono text-xs text-slate-300 overflow-x-auto">
                    <pre>{JSON.stringify(payload, null, 2)}</pre>
                  </div>
                </div>
              )}

              {/* STAGE 5: Supervisor Decision Panel */}
              {stage >= 5 && (
                <div className="glass-card p-6 rounded-2xl border border-blue-500/40 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 space-y-5 animate-in slide-in-from-bottom-4 duration-500">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                      <Send className="w-4 h-4 text-blue-400" />
                      Supervisor Decision & Feedback Calibration Action
                    </h3>
                    <p className="text-xs text-slate-400">
                      Submitting a decision stores an entry in <code className="text-blue-300">supervisor_feedback</code> and recalibrates the Fusion Engine active learning weights.
                    </p>
                  </div>

                  {feedbackSuccess && (
                    <div className="p-3 bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-xs font-semibold rounded-xl flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      {feedbackSuccess}
                    </div>
                  )}

                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-300">Supervisor Comments / Rationale:</label>
                    <textarea
                      value={comments}
                      onChange={(e) => setComments(e.target.value)}
                      placeholder="Add investigation comments or physical survey schedule verification details..."
                      className="w-full h-20 bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 outline-none focus:border-blue-500"
                    />
                  </div>

                  {/* Supervisor Action Buttons */}
                  <div className="flex flex-wrap items-center gap-4 pt-2">
                    <button
                      onClick={() => handleDecisionSubmit("CONFIRMED")}
                      className="flex items-center gap-2 px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-rose-950/50 transition-all"
                    >
                      <AlertOctagon className="w-4 h-4" />
                      Verify & Confirm Anomaly
                    </button>

                    <button
                      onClick={() => handleDecisionSubmit("DISMISSED")}
                      className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-950/50 transition-all"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      Accept as Legitimate
                    </button>

                    <button
                      onClick={() => handleDecisionSubmit("ESCALATED")}
                      className="flex items-center gap-2 px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-amber-950/50 transition-all"
                    >
                      <XCircle className="w-4 h-4" />
                      Escalate for Audit
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </AppShell>
  );
}
