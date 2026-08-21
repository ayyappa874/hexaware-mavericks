import React from "react";
import { AlertTriangle, AlertCircle, ShieldAlert, CheckCircle2 } from "lucide-react";

interface RiskBadgeProps {
  severity?: string;
  score?: number;
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ severity = "NORMAL", score, showScore = true }) => {
  const sevUpper = (severity || "NORMAL").toUpperCase();

  let badgeStyle = "bg-emerald-950/70 text-emerald-300 border-emerald-800/60";
  let Icon = CheckCircle2;
  let label = "NORMAL";

  if (sevUpper === "MONITOR") {
    badgeStyle = "bg-sky-950/70 text-sky-300 border-sky-800/60";
    Icon = AlertCircle;
    label = "MONITOR";
  } else if (sevUpper === "REVIEW" || sevUpper === "MEDIUM" || sevUpper === "HIGH") {
    badgeStyle = "bg-amber-950/70 text-amber-300 border-amber-800/60";
    Icon = AlertTriangle;
    label = "REVIEW";
  } else if (sevUpper === "HIGH_PRIORITY" || sevUpper === "CRITICAL") {
    badgeStyle = "bg-rose-950/70 text-rose-300 border-rose-800/60 animate-pulse";
    Icon = ShieldAlert;
    label = "HIGH PRIORITY";
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-bold rounded-full border shadow-sm ${badgeStyle}`}>
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span>{label}</span>
      {showScore && score !== undefined && (
        <span className="ml-1 pl-1.5 border-l border-current/30 font-mono">
          {score}
        </span>
      )}
    </span>
  );
};
