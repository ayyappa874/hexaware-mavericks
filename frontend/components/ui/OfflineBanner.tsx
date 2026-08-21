"use client";

import React, { useEffect, useState } from "react";
import { WifiOff, Wifi, RefreshCw, Smartphone, Bell } from "lucide-react";
import { OfflineSyncManager } from "../../lib/offlineSync";

export const OfflineBanner: React.FC = () => {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [alertChannel, setAlertChannel] = useState<"app" | "sms" | "both">("both");

  const checkStatus = () => {
    if (typeof window !== "undefined") {
      setIsOnline(navigator.onLine);
      const queue = OfflineSyncManager.getQueue();
      setPendingCount(queue.length);
    }
  };

  useEffect(() => {
    checkStatus();
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const handleOnline = async () => {
    setIsOnline(true);
    await triggerSync();
  };

  const handleOffline = () => {
    setIsOnline(false);
  };

  const triggerSync = async () => {
    setSyncing(true);
    try {
      await OfflineSyncManager.flushQueue();
      checkStatus();
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Alert Channel Selector */}
      <div className="hidden lg:flex items-center gap-1 bg-slate-900/90 border border-slate-800 rounded-xl px-2 py-1 text-[11px]">
        <Bell className="w-3 h-3 text-amber-400" />
        <span className="text-slate-400">Alerts:</span>
        <select
          value={alertChannel}
          onChange={(e) => setAlertChannel(e.target.value as any)}
          className="bg-transparent text-slate-200 font-bold outline-none text-[11px]"
        >
          <option value="both" className="bg-slate-900">App + SMS</option>
          <option value="app" className="bg-slate-900">App Only</option>
          <option value="sms" className="bg-slate-900">SMS Only</option>
        </select>
      </div>

      {/* Network Status Badge */}
      {!isOnline ? (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-rose-950/90 text-rose-300 border border-rose-800 rounded-xl text-xs font-bold shadow-lg shadow-rose-950/50 animate-pulse">
          <WifiOff className="w-3.5 h-3.5 text-rose-400" />
          <span>OFFLINE (In-Browser Wasm)</span>
          {pendingCount > 0 && (
            <span className="px-1.5 py-0.5 bg-rose-900 text-white rounded font-mono text-[10px]">
              {pendingCount} Pending
            </span>
          )}
        </div>
      ) : pendingCount > 0 ? (
        <button
          onClick={triggerSync}
          disabled={syncing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-950/90 hover:bg-amber-900 text-amber-300 border border-amber-800 rounded-xl text-xs font-bold transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-amber-400 ${syncing ? "animate-spin" : ""}`} />
          <span>Sync {pendingCount} Offline Actions</span>
        </button>
      ) : (
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/80 text-emerald-400 border border-slate-800 rounded-xl text-[11px] font-semibold">
          <Wifi className="w-3 h-3 text-emerald-400" />
          <span>Online</span>
        </div>
      )}
    </div>
  );
};
