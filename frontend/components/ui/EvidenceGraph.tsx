"use client";

import React from "react";
import { ShieldAlert, AlertTriangle, Cpu, Users, TrendingUp } from "lucide-react";

interface EvidenceGraphProps {
  score?: number;
  severity?: string;
  weights?: {
    w_rule?: number;
    w_stat?: number;
    w_ml?: number;
    w_fsu?: number;
    w_drift?: number;
  };
}

export const EvidenceGraph: React.FC<EvidenceGraphProps> = ({
  score = 85.0,
  severity = "HIGH_PRIORITY",
  weights = { w_rule: 0.35, w_stat: 0.35, w_ml: 0.30, w_fsu: 0.25, w_drift: 0.20 }
}) => {
  const isHigh = severity === "HIGH_PRIORITY" || score >= 75;

  // Center node color
  const centerGlow = isHigh ? "rgba(244, 63, 94, 0.4)" : "rgba(245, 158, 11, 0.4)";
  const centerColor = isHigh ? "#f43f5e" : "#f59e0b";

  // Satellite nodes definition (angle in degrees)
  const satellites = [
    { id: "rule", label: "Rule Engine", weight: weights.w_rule || 0.35, angle: -90, icon: ShieldAlert, color: "#f43f5e" },
    { id: "stat", label: "Cohort Z-Score", weight: weights.w_stat || 0.35, angle: -18, icon: TrendingUp, color: "#38bdf8" },
    { id: "ml", label: "ML Isolation Forest", weight: weights.w_ml || 0.30, angle: 54, icon: Cpu, color: "#818cf8" },
    { id: "fsu", label: "FSU Digit Pref", weight: weights.w_fsu || 0.25, angle: 126, icon: Users, color: "#fbbf24" },
    { id: "drift", label: "Temporal Shift", weight: weights.w_drift || 0.20, angle: 198, icon: AlertTriangle, color: "#34d399" }
  ];

  const radius = 130;
  const cx = 200;
  const cy = 200;

  return (
    <div className="glass-card p-6 rounded-2xl border border-slate-800 flex flex-col items-center justify-center relative overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <div className="w-full flex items-center justify-between border-b border-slate-800/80 pb-3 mb-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
          Evidence Radar Graph (Feature Weight Network)
        </h3>
        <span className="text-[11px] font-mono text-slate-500">Multi-Signal Radial Fusion</span>
      </div>

      <svg width="400" height="400" className="w-full max-w-[400px] h-auto drop-shadow-2xl">
        <defs>
          {/* Central Glow Filter */}
          <filter id="glow-center" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="12" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* Laser Gradients */}
          {satellites.map(sat => (
            <linearGradient key={`grad-${sat.id}`} id={`laser-${sat.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={centerColor} stopOpacity="0.8" />
              <stop offset="100%" stopColor={sat.color} stopOpacity="0.3" />
            </linearGradient>
          ))}
        </defs>

        {/* Concentric Background Orbits */}
        <circle cx={cx} cy={cy} r="60" fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
        <circle cx={cx} cy={cy} r={radius} fill="none" stroke="#334155" strokeWidth="1.5" strokeDasharray="4 4" />

        {/* Laser Connecting Edges */}
        {satellites.map(sat => {
          const rad = (sat.angle * Math.PI) / 180;
          const sx = cx + radius * Math.cos(rad);
          const sy = cy + radius * Math.sin(rad);
          const strokeW = Math.max(1.5, sat.weight * 6);

          return (
            <g key={`edge-${sat.id}`}>
              <line
                x1={cx}
                y1={cy}
                x2={sx}
                y2={sy}
                stroke={`url(#laser-${sat.id})`}
                strokeWidth={strokeW}
                strokeDasharray="6 3"
                className="animate-pulse"
              />
              {/* Midpoint Weight Badge */}
              <rect
                x={(cx + sx) / 2 - 14}
                y={(cy + sy) / 2 - 9}
                width="28"
                height="18"
                rx="4"
                fill="#0f172a"
                stroke="#334155"
                strokeWidth="1"
              />
              <text
                x={(cx + sx) / 2}
                y={(cy + sy) / 2 + 3}
                fill="#94a3b8"
                fontSize="9"
                fontFamily="monospace"
                fontWeight="bold"
                textAnchor="middle"
              >
                {Math.round(sat.weight * 100)}%
              </text>
            </g>
          );
        })}

        {/* Satellite Nodes */}
        {satellites.map(sat => {
          const rad = (sat.angle * Math.PI) / 180;
          const sx = cx + radius * Math.cos(rad);
          const sy = cy + radius * Math.sin(rad);

          return (
            <g key={`node-${sat.id}`} className="group cursor-pointer">
              <circle
                cx={sx}
                cy={sy}
                r="22"
                fill="#0f172a"
                stroke={sat.color}
                strokeWidth="2"
                className="transition-all duration-300 group-hover:r-26 shadow-lg"
              />
              <circle cx={sx} cy={sy} r="26" fill={sat.color} opacity="0.1" />
              <text
                x={sx}
                y={sy + (sy > cy ? 38 : -30)}
                fill="#e2e8f0"
                fontSize="10"
                fontWeight="bold"
                textAnchor="middle"
              >
                {sat.label}
              </text>
            </g>
          );
        })}

        {/* Center Node (Overall Risk Score) */}
        <circle cx={cx} cy={cy} r="42" fill={centerGlow} filter="url(#glow-center)" />
        <circle cx={cx} cy={cy} r="36" fill="#090d16" stroke={centerColor} strokeWidth="3" />

        <text x={cx} y={cy - 6} fill="#94a3b8" fontSize="9" textAnchor="middle" fontWeight="extrabold" letterSpacing="1">
          RISK SCORE
        </text>
        <text x={cx} y={cy + 14} fill={centerColor} fontSize="20" fontFamily="monospace" fontWeight="black" textAnchor="middle">
          {score}
        </text>
      </svg>
    </div>
  );
};
