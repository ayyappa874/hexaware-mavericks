"use client";

import React, { useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { RiskBadge } from "../../components/ui/RiskBadge";
import { EvidenceBullet } from "../../components/ui/EvidenceBullet";
import { OfflineInferenceEngine, OfflineValidationResult } from "../../lib/offlineInference";
import { OfflineSyncManager } from "../../lib/offlineSync";
import { WifiOff, Cpu, RefreshCw, Smartphone, Download, CheckCircle2, ShieldAlert, Zap, Terminal } from "lucide-react";

export default function OfflineLabPage() {
  const [testPayload, setTestPayload] = useState({
    Age: 24,
    Sex: 1,
    General_Edu: 8,
    Usual_Principal_Activity_Status: 91,
    Earnings_Last_Month: 45000,
    Daily_Wages: 0
  });

  const [offlineResult, setOfflineResult] = useState<OfflineValidationResult | null>(null);
  const [pendingQueue, setPendingQueue] = useState(OfflineSyncManager.getQueue());
  const [syncedMsg, setSyncedMsg] = useState<string | null>(null);
  const [simulatedP2P, setSimulatedP2P] = useState<boolean>(false);

  const handleRunOfflineInference = () => {
    const res = OfflineInferenceEngine.validateOffline(testPayload, "OFFLINE_TEST_REC_001");
    setOfflineResult(res);
  };

  const handleEnqueueOfflineAction = () => {
    OfflineSyncManager.enqueueAction({
      flag_id: "FLAG_OFFLINE_" + Math.random().toString(36).substring(2, 7),
      supervisor_id: "OFFLINE_FIELD_SUPERVISOR_01",
      decision: "CONFIRMED",
      comments: "Validated offline in village FSU 2901"
    });
    setPendingQueue(OfflineSyncManager.getQueue());
  };

  const handleFlushSyncQueue = async () => {
    const res = await OfflineSyncManager.flushQueue();
    setSyncedMsg(`Successfully synced ${res.synced} offline actions to backend audit log!`);
    setPendingQueue(OfflineSyncManager.getQueue());
  };

  return (
    <AppShell>
      {() => (
        <div className="space-y-8 animate-in fade-in duration-200">
          {/* Header Banner */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-amber-500/30">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 bg-amber-950/80 text-amber-400 border border-amber-800/80 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider">
                  0ms Client-Side Wasm
                </span>
                <span className="text-xs text-slate-400">Zero Internet / Remote Village Mode</span>
              </div>
              <h1 className="text-3xl font-black text-slate-100 flex items-center gap-3 mt-2">
                <WifiOff className="w-8 h-8 text-amber-400" />
                Offline Engine & Field Simulator
              </h1>
              <p className="text-xs text-slate-400 max-w-2xl leading-relaxed mt-1">
                Field supervisors operating in remote FSUs without cellular towers use our client-side WebAssembly inference engine, IndexedDB offline action queue, and local Wi-Fi Hotspot P2P tablet pairing adapter.
              </p>
            </div>

            <div className="mt-4 md:mt-0 flex items-center gap-3">
              <a
                href="/scripts/offline_validator_cli.py"
                download
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-xl text-xs font-bold transition-all"
              >
                <Download className="w-4 h-4 text-amber-400" /> Download USB Laptop CLI
              </a>
            </div>
          </div>

          {/* Grid Layout: 2 Columns */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Column 1: In-Browser WebAssembly Decision Engine */}
            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                <div className="flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-sky-400" />
                  <h2 className="text-base font-bold text-slate-100">1. In-Browser Decision Engine Playground</h2>
                </div>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                  0ms Latency
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400">Person Age</label>
                  <input
                    type="number"
                    value={testPayload.Age}
                    onChange={(e) => setTestPayload({ ...testPayload, Age: Number(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-800 text-slate-100 text-xs px-3 py-2 rounded-xl mt-1 outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400">Activity Status Code</label>
                  <input
                    type="number"
                    value={testPayload.Usual_Principal_Activity_Status}
                    onChange={(e) => setTestPayload({ ...testPayload, Usual_Principal_Activity_Status: Number(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-800 text-slate-100 text-xs px-3 py-2 rounded-xl mt-1 outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400">General Education</label>
                  <input
                    type="number"
                    value={testPayload.General_Edu}
                    onChange={(e) => setTestPayload({ ...testPayload, General_Edu: Number(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-800 text-slate-100 text-xs px-3 py-2 rounded-xl mt-1 outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400">Earnings Last Month (₹)</label>
                  <input
                    type="number"
                    value={testPayload.Earnings_Last_Month}
                    onChange={(e) => setTestPayload({ ...testPayload, Earnings_Last_Month: Number(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-800 text-slate-100 text-xs px-3 py-2 rounded-xl mt-1 outline-none font-mono"
                  />
                </div>
              </div>

              <button
                onClick={handleRunOfflineInference}
                className="w-full py-3 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-black text-xs rounded-xl transition-all shadow-lg flex items-center justify-center gap-2"
              >
                <Zap className="w-4 h-4" /> Run 0ms In-Browser Wasm Validation
              </button>

              {/* Validation Output */}
              {offlineResult && (
                <div className="p-4 bg-slate-900/90 rounded-xl border border-slate-800 space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between">
                    <RiskBadge severity={offlineResult.severity} score={offlineResult.overall_risk} />
                    <span className="text-[11px] font-mono text-slate-400">
                      Rule: {offlineResult.rule_score} | Stat: {offlineResult.stat_score} | ML: {offlineResult.ml_score}
                    </span>
                  </div>

                  <div className="space-y-1.5 pt-2">
                    {offlineResult.evidence_bullets.map((b, i) => (
                      <EvidenceBullet key={i} bullet={b} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Column 2: Offline Queue & P2P Hotspot Adapter */}
            <div className="space-y-6">
              {/* IndexedDB Action Queue */}
              <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-5 h-5 text-amber-400" />
                    <h2 className="text-base font-bold text-slate-100">2. IndexedDB Offline Action Queue</h2>
                  </div>
                  <span className="text-xs font-mono text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
                    {pendingQueue.length} Pending
                  </span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  Supervisor decisions logged offline are cached in IndexedDB/LocalStorage. They automatically sync to the SHA-256 Audit Trail upon reconnect.
                </p>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleEnqueueOfflineAction}
                    className="flex-1 py-2.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-xl text-xs font-bold transition-all"
                  >
                    + Enqueue Mock Decision
                  </button>
                  <button
                    onClick={handleFlushSyncQueue}
                    disabled={pendingQueue.length === 0}
                    className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl text-xs font-extrabold transition-all flex items-center justify-center gap-1.5"
                  >
                    <RefreshCw className="w-3.5 h-3.5" /> Flush Sync Queue
                  </button>
                </div>

                {syncedMsg && (
                  <div className="p-3 bg-emerald-950/80 border border-emerald-800/80 text-emerald-300 rounded-xl text-xs flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{syncedMsg}</span>
                  </div>
                )}
              </div>

              {/* P2P Local Wi-Fi Hotspot Adapter */}
              <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-5 h-5 text-indigo-400" />
                    <h2 className="text-base font-bold text-slate-100">3. Local Wi-Fi Hotspot P2P Adapter</h2>
                  </div>
                  <span className="text-xs font-mono text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
                    POST /api/v1/p2p/ingest
                  </span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  CAPI field tablets pair directly over a local Wi-Fi Hotspot created by the supervisor's laptop in remote villages without cellular towers.
                </p>

                <button
                  onClick={() => setSimulatedP2P(true)}
                  className="w-full py-2.5 bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 border border-indigo-800/80 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2"
                >
                  <Smartphone className="w-4 h-4 text-indigo-400" /> Simulate CAPI Tablet Hotspot P2P Stream
                </button>

                {simulatedP2P && (
                  <div className="p-3 bg-indigo-950/90 border border-indigo-800 text-indigo-200 rounded-xl text-xs space-y-1 font-mono">
                    <div className="text-indigo-400 font-bold">CONNECTED: CAPI_TABLET_FIELD_07</div>
                    <div>Mode: LOCAL_HOTSPOT_P2P</div>
                    <div>Status: INGESTED_P2P (1 Record Received, 0ms Latency)</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
