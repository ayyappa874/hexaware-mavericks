import React from "react";

interface SkeletonLoaderProps {
  variant?: "card" | "table" | "text" | "chart";
  count?: number;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ variant = "card", count = 1 }) => {
  const items = Array.from({ length: count });

  if (variant === "table") {
    return (
      <div className="w-full space-y-3 animate-pulse">
        <div className="h-10 bg-slate-900/90 rounded-lg border border-slate-800" />
        {items.map((_, i) => (
          <div key={i} className="h-12 bg-slate-900/40 rounded-lg border border-slate-800/60 flex items-center justify-between px-4">
            <div className="h-4 w-1/4 bg-slate-800 rounded" />
            <div className="h-4 w-1/6 bg-slate-800 rounded" />
            <div className="h-4 w-1/5 bg-slate-800 rounded" />
            <div className="h-4 w-1/6 bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "chart") {
    return (
      <div className="w-full h-64 bg-slate-900/50 rounded-2xl border border-slate-800/80 p-6 flex flex-col justify-between animate-pulse">
        <div className="h-5 w-1/3 bg-slate-800 rounded" />
        <div className="flex items-end gap-3 h-40 pt-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex-1 bg-slate-800/60 rounded-t-md" style={{ height: `${20 + ((i * 15) % 80)}%` }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
      {items.map((_, i) => (
        <div key={i} className="glass-card p-5 rounded-xl border border-slate-800/80 space-y-3">
          <div className="flex justify-between items-center">
            <div className="h-3 w-1/2 bg-slate-800 rounded" />
            <div className="h-5 w-5 bg-slate-800 rounded-full" />
          </div>
          <div className="h-8 w-3/4 bg-slate-800/80 rounded" />
          <div className="h-3 w-2/3 bg-slate-800/50 rounded" />
        </div>
      ))}
    </div>
  );
};
