"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { RiskBadge } from "../../components/ui/RiskBadge";
import { EvidenceBullet } from "../../components/ui/EvidenceBullet";
import { SkeletonLoader } from "../../components/ui/SkeletonLoader";
import { EmptyState } from "../../components/ui/EmptyState";
import { Search, Filter, ShieldAlert, CheckCircle, ArrowRight, CornerDownLeft } from "lucide-react";

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

export default function InvestigationQueuePage() {
  const [flags, setFlags] = useState<FlagRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [activeTabMode, setActiveTabMode] = useState<"priority" | "active_learning">("priority");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const generateMockFlags = (): FlagRow[] => {
    const detectors = ["RuleEngine", "StatisticalEngine", "MLEngine", "BenfordEngine"];
    const severities = ["HIGH_PRIORITY", "REVIEW", "MONITOR"];
    const bulletsList = [
      ["RULE_MIN_AGE_SALARIED: Person age 11 reported as regular salaried worker.", "Earnings ₹85,000 exceed peer cohort mean by +3.8σ."],
      ["Isolation Forest flagged high-dimensional multivariate outlier in Age vs Wages.", "Local Outlier Factor (LOF) score 2.41 density deviation."],
      ["Benford's Law Chi-Square test failed (p < 0.001) for FSU_27005_102.", "FDR-corrected leading digit 0 over-represented by 48%."],
      ["RULE_STUDENT_HIGH_EARNINGS: Inactive student status code reported ₹45,000 monthly income."],
      ["Two-sample Z-Test detected significant Unemployment Rate shift (Z = +2.84, p < 0.01)."]
    ];

    return Array.from({ length: 15 }).map((_, i) => {
      const score = 95 - i * 5;
      const sev = score >= 75 ? "HIGH_PRIORITY" : score >= 50 ? "REVIEW" : "MONITOR";
      return {
        id: `FLAG_DEMO_${100 + i}`,
        record_id: `f12b8e9f-ca7a-41b9-b778-88582324ecbf`,
        survey_id: "PLFS_2024",
        detector_type: detectors[i % detectors.length],
        severity: sev,
        score: score,
        evidence: {
          risk_score: score,
          severity: sev,
          narrative_bullets: bulletsList[i % bulletsList.length],
          rule_score: Math.min(100, score + 5),
          stat_score: Math.max(10, score - 10),
          ml_score: score
        },
        status: "PENDING",
        created_at: new Date().toISOString()
      };
    });
  };

  const fetchQueue = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/api/v1/flags?limit=50`;
      if (severityFilter) url += `&severity=${severityFilter}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setFlags(data.flags || []);
        setSelectedIndex(0);
        setLoading(false);
        return;
      }
    } catch (err) {
      console.warn("Backend API unreachable on Vercel, using in-browser mock queue:", err);
    }

    // Client-side mock flags fallback for Vercel demo
    const mockData = generateMockFlags();
    let filtered = mockData;
    if (severityFilter) filtered = filtered.filter((f) => f.severity === severityFilter);
    if (statusFilter) filtered = filtered.filter((f) => f.status === statusFilter);
    setFlags(filtered);
    setSelectedIndex(0);
    setLoading(false);
  };

  const sortedFlags = [...flags].sort((a, b) => {
    if (activeTabMode === "active_learning") {
      const uA = Math.abs(a.score - 50);
      const uB = Math.abs(b.score - 50);
      return uA - uB;
    }
    return b.score - a.score;
  });

  useEffect(() => {
    fetchQueue();
  }, [severityFilter, statusFilter]);

  // J/K/A/R Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return;

      if (e.key.toLowerCase() === "j") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(flags.length - 1, prev + 1));
      } else if (e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key.toLowerCase() === "a" && flags[selectedIndex]) {
        e.preventDefault();
        handleDecision(flags[selectedIndex].id, "DISMISSED");
      } else if (e.key.toLowerCase() === "r" && flags[selectedIndex]) {
        e.preventDefault();
        handleDecision(flags[selectedIndex].id, "CONFIRMED");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [flags, selectedIndex]);

  const handleDecision = async (flagId: string, decision: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/flags/${flagId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          supervisor_id: "SUPERVISOR_KEYBOARD_HERO",
          decision: decision,
          comments: `Quick shortcut decision (${decision})`
        })
      });

      if (res.ok) {
        setFlags((prev) =>
          prev.map((f) => (f.id === flagId ? { ...f, status: decision } : f))
        );
      }
    } catch (err) {
      console.error("Decision update failed:", err);
    }
  };

  return (
    <AppShell onRefresh={fetchQueue} loading={loading}>
      {() => (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Header Banner */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-slate-800">
            <div>
              <h1 className="text-2xl font-black text-slate-100 flex items-center gap-3">
                <ShieldAlert className="w-7 h-7 text-amber-400" />
                Investigation Queue
              </h1>
              <p className="text-xs text-slate-400 max-w-xl leading-relaxed mt-1">
                Priority-sorted anomaly queue (Risk × Confidence). Use keyboard shortcuts: <kbd className="px-1.5 py-0.5 bg-slate-800 text-slate-200 font-mono rounded">J</kbd> down, <kbd className="px-1.5 py-0.5 bg-slate-800 text-slate-200 font-mono rounded">K</kbd> up, <kbd className="px-1.5 py-0.5 bg-slate-800 text-slate-200 font-mono rounded">A</kbd> accept legitimate, <kbd className="px-1.5 py-0.5 bg-slate-800 text-slate-200 font-mono rounded">R</kbd> escalate.
              </p>
            </div>

            {/* Filter controls */}
            <div className="flex items-center gap-3 mt-4 md:mt-0">
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2 outline-none"
              >
                <option value="">All Severities</option>
                <option value="REVIEW">Review (High Risk)</option>
                <option value="MONITOR">Monitor (Medium Risk)</option>
                <option value="NORMAL">Normal (Low Risk)</option>
                <option value="HIGH_PRIORITY">High Priority</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2 outline-none"
              >
                <option value="">All Statuses</option>
                <option value="PENDING">Pending Review</option>
                <option value="CONFIRMED">Confirmed Anomaly</option>
                <option value="DISMISSED">Dismissed False Alarm</option>
              </select>
            </div>
          </div>

          {/* Queue List */}
          {loading && flags.length === 0 ? (
            <SkeletonLoader variant="table" count={5} />
          ) : flags.length === 0 ? (
            <EmptyState
              title="No Pending Anomaly Flags"
              description="No anomaly flags found matching the selected filter criteria."
              onAction={fetchQueue}
            />
          ) : (
            <div className="space-y-3">
              {flags.map((flag, index) => {
                const isSelected = index === selectedIndex;
                const bullets: string[] = flag.evidence?.narrative_bullets || [];

                return (
                  <div
                    key={flag.id}
                    onClick={() => setSelectedIndex(index)}
                    className={`glass-card p-5 rounded-2xl border transition-all cursor-pointer space-y-3.5 ${
                      isSelected
                        ? "border-blue-500/80 bg-blue-950/20 shadow-xl shadow-blue-950/40 ring-1 ring-blue-500/50"
                        : "border-slate-800/80 bg-slate-950/50 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        {isSelected && (
                          <span className="w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping" />
                        )}
                        <RiskBadge severity={flag.severity} score={flag.score} />
                        <span className="text-xs font-mono font-bold text-blue-400 bg-blue-950/60 px-2.5 py-1 rounded-md border border-blue-800/40">
                          {flag.detector_type}
                        </span>
                        <span className="text-xs font-mono text-slate-400">Record: {flag.record_id}</span>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className={`text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${
                          flag.status === 'CONFIRMED' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                          flag.status === 'DISMISSED' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
                          'bg-amber-950 text-amber-300 border border-amber-800'
                        }`}>
                          {flag.status}
                        </span>

                        <Link
                          href={`/record/${flag.record_id}`}
                          className="flex items-center gap-1 text-xs font-bold text-blue-400 hover:text-blue-300 bg-blue-950/60 px-3 py-1.5 rounded-lg border border-blue-800/40"
                        >
                          Hero Investigation <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>

                    {/* Narrative Evidence Preview */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {bullets.slice(0, 2).map((b, i) => (
                        <EvidenceBullet key={i} bullet={b} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
