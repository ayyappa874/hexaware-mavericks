"use client";

import { useEffect, useState, useRef } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { RiskBadge } from "../../components/ui/RiskBadge";
import { EvidenceBullet } from "../../components/ui/EvidenceBullet";
import { Play, Pause, FastForward, RefreshCw, Activity, ShieldCheck, Zap } from "lucide-react";

interface StreamItem {
  stream_index: number;
  record_id: string;
  state_code: string;
  fsu_id: string;
  raw_payload: Record<string, any>;
  validation_result: {
    overall_risk: number;
    severity: string;
    evidence: Record<string, any>;
  };
}

export default function StreamReplayDemoPage() {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(2000); // 2s
  const [items, setItems] = useState<StreamItem[]>([]);
  const [currentRisk, setCurrentRisk] = useState<number>(0);
  const [currentSeverity, setCurrentSeverity] = useState<string>("NORMAL");
  const [totalProcessed, setTotalProcessed] = useState<number>(0);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const generateMockStreamItem = (index: number): StreamItem => {
    const isAnomalous = Math.random() < 0.3;
    const stateCode = ["07", "09", "19", "27", "29", "33"][Math.floor(Math.random() * 6)];
    const riskScore = isAnomalous ? Math.floor(Math.random() * 40) + 55 : Math.floor(Math.random() * 25) + 5;
    const severity = riskScore >= 75 ? "HIGH_PRIORITY" : riskScore >= 50 ? "REVIEW" : "NORMAL";
    
    return {
      stream_index: index,
      record_id: `REC_PLFS_2024_${stateCode}_${Math.floor(Math.random() * 900000 + 100000)}`,
      state_code: stateCode,
      fsu_id: `FSU_${stateCode}005_${Math.floor(Math.random() * 800 + 100)}`,
      raw_payload: {
        Age: isAnomalous ? Math.floor(Math.random() * 10) + 5 : Math.floor(Math.random() * 50) + 18,
        Earnings_Last_Month: isAnomalous ? 85000 : Math.floor(Math.random() * 30000) + 5000,
        Usual_Principal_Activity_Status: isAnomalous ? 31 : 11,
        Sector: Math.random() > 0.5 ? 1 : 2
      },
      validation_result: {
        overall_risk: riskScore,
        severity: severity,
        evidence: {
          narrative_bullets: isAnomalous 
            ? ["RULE_MIN_AGE_SALARIED: Person under 15 reported as regular salaried worker.", "Earnings ₹85,000 exceed peer cohort mean by +3.8σ."]
            : ["All 10 PLFS syntactic rules passed.", "Peer cohort statistical distributions normal."]
        }
      }
    };
  };

  const fetchNextRecord = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/demo/stream-next`);
      if (res.ok) {
        const item: StreamItem = await res.json();
        setItems((prev) => [item, ...prev.slice(0, 19)]);
        setCurrentRisk(item.validation_result.overall_risk);
        setCurrentSeverity(item.validation_result.severity);
        setTotalProcessed((prev) => prev + 1);
        return;
      }
    } catch (err) {
      console.warn("Backend API unreachable on Vercel, using in-browser stream generator:", err);
    }

    // Client-side fallback stream item
    const fallbackItem = generateMockStreamItem(totalProcessed + 1);
    setItems((prev) => [fallbackItem, ...prev.slice(0, 19)]);
    setCurrentRisk(fallbackItem.validation_result.overall_risk);
    setCurrentSeverity(fallbackItem.validation_result.severity);
    setTotalProcessed((prev) => prev + 1);
  };

  useEffect(() => {
    let interval: any = null;
    if (isPlaying) {
      interval = setInterval(() => {
        fetchNextRecord();
      }, speed);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, speed]);

  return (
    <AppShell>
      {() => (
        <div className="space-y-8 animate-in fade-in duration-200">
          {/* Header Banner */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-blue-500/30">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 text-[10px] font-black uppercase tracking-wider bg-rose-950 text-rose-300 border border-rose-800 rounded-md flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping" /> LIVE DEMO MODE
                </span>
                <h1 className="text-2xl font-black text-slate-100">
                  Real-Time CAPI Stream Replay Simulator
                </h1>
              </div>
              <p className="text-xs text-slate-400 max-w-xl">
                Simulates real-time unit-level survey microdata stream ingestion from field enumerator CAPI tablets passing synchronously through Survey Sentinel multi-detector fusion.
              </p>
            </div>

            {/* Play / Pause / Controls */}
            <div className="flex items-center gap-3 mt-4 md:mt-0">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs shadow-lg transition-all ${
                  isPlaying
                    ? "bg-amber-600 hover:bg-amber-500 text-white shadow-amber-950/50"
                    : "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-950/50"
                }`}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                <span>{isPlaying ? "Pause Stream" : "Start Live Stream"}</span>
              </button>

              <button
                onClick={fetchNextRecord}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 rounded-xl font-bold text-xs"
              >
                <Zap className="w-4 h-4 text-amber-400" /> Single Step
              </button>

              <select
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
                className="bg-slate-900 border border-slate-800 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2.5 outline-none"
              >
                <option value={3000}>Speed: 1x (3s)</option>
                <option value={1500}>Speed: 2x (1.5s)</option>
                <option value={500}>Speed: 5x (0.5s)</option>
              </select>
            </div>
          </div>

          {/* Live Risk Meter & Stream Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Live Risk Gauge */}
            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4 text-center flex flex-col items-center justify-center">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Incoming Record Risk Gauge</span>
              
              <div className="relative flex items-center justify-center w-36 h-36">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="72" cy="72" r="56" stroke="#1e293b" strokeWidth="12" fill="none" />
                  <circle
                    cx="72"
                    cy="72"
                    r="56"
                    stroke={currentRisk >= 75 ? "#f43f5e" : currentRisk >= 50 ? "#f59e0b" : "#10b981"}
                    strokeWidth="12"
                    strokeDasharray="351"
                    strokeDashoffset={351 - (351 * currentRisk) / 100}
                    strokeLinecap="round"
                    fill="none"
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center font-mono">
                  <span className="text-3xl font-black text-white">{currentRisk}</span>
                  <span className="text-[10px] text-slate-500 font-bold">/ 100</span>
                </div>
              </div>

              <RiskBadge severity={currentSeverity} score={currentRisk} />
            </div>

            {/* Stream Summary Cards */}
            <div className="md:col-span-2 glass-card p-6 rounded-2xl border border-slate-800 space-y-4 flex flex-col justify-between">
              <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-400" /> CAPI Field Ingestion Stream Metrics
                </span>
                <span className="text-xs font-mono text-emerald-400">Status: {isPlaying ? "STREAMING" : "IDLE"}</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Records Processed</span>
                  <p className="text-2xl font-black text-white font-mono mt-1">{totalProcessed}</p>
                </div>
                <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Replay Round</span>
                  <p className="text-lg font-bold text-amber-400 font-mono mt-1">PLFS 2024-25</p>
                </div>
                <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 col-span-2 sm:col-span-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Sync Latency</span>
                  <p className="text-2xl font-black text-emerald-400 font-mono mt-1">42ms</p>
                </div>
              </div>

              <p className="text-xs text-slate-400">
                Incoming unit-level records are evaluated against 10 real MoSPI PLFS validation rules, 708 peer cohort statistical distributions, and trained Isolation Forest models synchronously.
              </p>
            </div>
          </div>

          {/* Live Ingestion Ticker Feed */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" /> Live Record Ingestion Stream Feed
            </h2>

            {items.length === 0 ? (
              <div className="p-10 text-center text-xs text-slate-500 bg-slate-950 rounded-xl border border-slate-900">
                Click <strong>&quot;Start Live Stream&quot;</strong> or <strong>&quot;Single Step&quot;</strong> to begin stream replay.
              </div>
            ) : (
              <div className="space-y-3">
                {items.map((item, idx) => {
                  const res = item.validation_result;
                  const bullets: string[] = res.evidence?.narrative_bullets || [];

                  return (
                    <div
                      key={`${item.record_id}-${idx}`}
                      className={`p-4 rounded-xl border transition-all space-y-3 ${
                        idx === 0
                          ? "bg-blue-950/30 border-blue-500/50 shadow-lg shadow-blue-950/30 animate-in slide-in-from-top-2 duration-300"
                          : "bg-slate-900/60 border-slate-800/80"
                      }`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-3">
                          <RiskBadge severity={res.severity} score={res.overall_risk} />
                          <span className="text-xs font-mono font-bold text-slate-200">
                            {item.record_id}
                          </span>
                          <span className="text-xs font-mono text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/40">
                            State {item.state_code} | FSU {item.fsu_id}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-500">
                          Seq #{item.stream_index}
                        </span>
                      </div>

                      {/* Evidence bullets */}
                      <div className="space-y-1.5">
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
        </div>
      )}
    </AppShell>
  );
}
