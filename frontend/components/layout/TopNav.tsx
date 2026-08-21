"use client";

import React from "react";
import { Server, Search, RefreshCw, Command, Download } from "lucide-react";
import { OfflineBanner } from "../ui/OfflineBanner";

interface TopNavProps {
  systemStatus?: string;
  selectedRound?: string;
  setSelectedRound?: (r: string) => void;
  onRefresh?: () => void;
  onOpenCommandPalette?: () => void;
  loading?: boolean;
}

export const TopNav: React.FC<TopNavProps> = ({
  systemStatus,
  selectedRound,
  setSelectedRound,
  onRefresh,
  onOpenCommandPalette,
  loading
}) => {
  return (
    <header className="sticky top-0 z-20 glass-card border-b border-slate-800/80 px-6 py-3.5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      {/* Tender positioning badge */}
      <div className="flex items-center gap-3">
        <span className="px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider bg-blue-950/70 text-blue-300 border border-blue-800/60 rounded-md">
          MoSPI Tender Spec Compliant
        </span>
        <span className="text-xs text-slate-400 font-medium">
          PLFS Unit-Level Microdata Engine
        </span>
      </div>

      {/* Action items & controls */}
      <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end">
        {/* Cmd+K trigger */}
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-2 bg-slate-900/90 hover:bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-xl text-xs font-medium transition-all shadow-sm"
        >
          <Search className="w-3.5 h-3.5 text-blue-400" />
          <span>Quick Search...</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 text-[10px] font-mono bg-slate-800 border border-slate-700 px-1.5 py-0.5 rounded text-slate-300 ml-2">
            <Command className="w-2.5 h-2.5" /> K
          </kbd>
        </button>

        {/* Live Demo Mode Button */}
        <a
          href="/demo"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800/80 rounded-xl text-xs font-bold transition-all shadow-sm shadow-rose-950/50"
        >
          <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping shrink-0" />
          <span>LIVE DEMO</span>
        </a>

        {/* Offline Mode & Sync Controls */}
        <OfflineBanner />

        {/* Round Selector */}
        <select
          value={selectedRound}
          onChange={(e) => setSelectedRound(e.target.value)}
          className="bg-slate-900 border border-slate-800 text-slate-200 text-xs font-semibold rounded-xl px-3 py-1.5 outline-none focus:border-blue-500 transition-all cursor-pointer"
        >
          <option value="">All Rounds</option>
          <option value="2023-24">2023-24 Baseline</option>
          <option value="2024-25">2024-25 Stream (Replay)</option>
        </select>

        {/* Executive PDF/Excel Export */}
        <div className="relative group">
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-950/80 hover:bg-blue-900 text-blue-300 border border-blue-800/80 rounded-xl text-xs font-bold transition-all">
            <Download className="w-3.5 h-3.5 text-blue-400" />
            <span>Export Report</span>
          </button>

          <div className="absolute right-0 mt-1 w-44 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-1.5 hidden group-hover:block z-50 animate-in fade-in">
            <a
              href="http://localhost:8005/api/v1/reports/export?format=pdf"
              target="_blank"
              rel="noreferrer"
              className="block px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 rounded-lg font-medium"
            >
              📄 Executive PDF Report
            </a>
            <a
              href="http://localhost:8005/api/v1/reports/export?format=excel"
              target="_blank"
              rel="noreferrer"
              className="block px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 rounded-lg font-medium"
            >
              📊 Excel Workbook (.xlsx)
            </a>
          </div>
        </div>

        {/* System Health */}
        <div className="flex items-center gap-2 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
          <Server className={`w-3.5 h-3.5 ${systemStatus === "online" ? "text-emerald-400 animate-pulse" : "text-amber-400"}`} />
          <span className="text-slate-400 font-medium hidden sm:inline">API:</span>
          <span className={`font-bold ${systemStatus === "online" ? "text-emerald-400" : "text-amber-400"}`}>
            {systemStatus}
          </span>
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          className="p-2 text-slate-400 hover:text-blue-400 bg-slate-900 border border-slate-800 rounded-xl transition-colors"
          title="Refresh Backend Data"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>
    </header>
  );
};
