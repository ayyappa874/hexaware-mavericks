import React from "react";
import { AlertOctagon, TrendingUp, Cpu, CheckCircle } from "lucide-react";

interface EvidenceBulletProps {
  bullet: string;
}

export const EvidenceBullet: React.FC<EvidenceBulletProps> = ({ bullet }) => {
  let Icon = AlertOctagon;
  let iconColor = "text-amber-400 bg-amber-950/40 border-amber-800/40";

  if (bullet.includes("Rule Violation")) {
    Icon = AlertOctagon;
    iconColor = "text-rose-400 bg-rose-950/40 border-rose-800/40";
  } else if (bullet.includes("Cohort Deviation") || bullet.includes("Z-score")) {
    Icon = TrendingUp;
    iconColor = "text-sky-400 bg-sky-950/40 border-sky-800/40";
  } else if (bullet.includes("Multivariate Outlier") || bullet.includes("Isolation Forest") || bullet.includes("ML")) {
    Icon = Cpu;
    iconColor = "text-indigo-400 bg-indigo-950/40 border-indigo-800/40";
  } else if (bullet.includes("High-confidence") || bullet.includes("normal parameters")) {
    Icon = CheckCircle;
    iconColor = "text-emerald-400 bg-emerald-950/40 border-emerald-800/40";
  }

  return (
    <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 text-xs text-slate-200 leading-relaxed">
      <div className={`p-1 rounded-md border shrink-0 mt-0.5 ${iconColor}`}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <span className="font-normal">{bullet}</span>
    </div>
  );
};
