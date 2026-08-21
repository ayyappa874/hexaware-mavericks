"use client";

import React, { useState } from "react";
import { ShieldCheck, LayoutDashboard, Play, Search, Users, Sliders, TrendingUp, Layers, WifiOff, ChevronLeft, ChevronRight } from "lucide-react";

interface SidebarProps {
  activeTab?: string;
  setActiveTab?: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { id: "pulse", label: "National Quality Pulse", icon: LayoutDashboard, href: "/" },
    { id: "demo", label: "Live Stream Replay", icon: Play, href: "/demo", isLive: true },
    { id: "queue", label: "Investigation Queue", icon: Search, href: "/queue" },
    { id: "offline", label: "Offline Field Simulator", icon: WifiOff, href: "/offline" },
    { id: "clusters", label: "Semantic Clusters", icon: Layers, href: "/clusters" },
    { id: "observatory", label: "Enumerator Observatory", icon: Users, href: "/observatory" },
    { id: "model_lab", label: "Model Lab", icon: Sliders, href: "/models" },
    { id: "temporal", label: "Temporal Drift Monitor", icon: TrendingUp, href: "/temporal" },
    { id: "registry", label: "Schema Registry", icon: Layers, href: "/registry" },
  ];


  return (
    <aside className={`glass-card h-screen sticky top-0 border-r border-slate-800/80 transition-all duration-300 flex flex-col justify-between z-30 ${collapsed ? "w-20" : "w-64"}`}>
      <div className="p-4 space-y-6">
        {/* Brand Logo & Title */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl border border-blue-400/30 shadow-lg shrink-0">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            {!collapsed && (
              <div>
                <h1 className="font-extrabold text-base tracking-tight bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-300 bg-clip-text text-transparent">
                  SENTINEL
                </h1>
                <p className="text-[10px] text-blue-300/80 font-mono tracking-widest uppercase">MoSPI Layer</p>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5 pt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (setActiveTab) setActiveTab(item.id);
                  if (typeof window !== "undefined") window.location.href = item.href;
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl font-medium text-xs transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-blue-600/30 to-indigo-600/20 text-blue-300 border border-blue-500/40 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 shrink-0 ${item.isLive ? "text-amber-400 animate-pulse" : isActive ? "text-blue-400" : "text-slate-400"}`} />
                  {!collapsed && <span>{item.label}</span>}
                </div>

                {!collapsed && item.isLive && (
                  <span className="px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wider bg-rose-950 text-rose-300 border border-rose-800 rounded font-mono animate-pulse">
                    LIVE
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Profile Badge */}
      {!collapsed && (
        <div className="p-4 m-3 glass-card rounded-xl border border-slate-800/80 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-xs text-white">
            GOI
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-bold text-slate-200 truncate">MoSPI Supervisor</p>
            <p className="text-[10px] text-slate-400 truncate">Admin Role</p>
          </div>
        </div>
      )}
    </aside>
  );
};
