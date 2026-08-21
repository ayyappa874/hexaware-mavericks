"use client";

import React, { useEffect, useState } from "react";
import { Search, Database, Users, MapPin, Sliders, X } from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectAction: (action: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose, onSelectAction }) => {
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else onSelectAction("toggle");
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, onSelectAction]);

  if (!isOpen) return null;

  const commands = [
    { id: "nav-pulse", label: "Jump to National Quality Pulse Dashboard", category: "Navigation", icon: Database },
    { id: "nav-queue", label: "Open Investigation Queue (Priority Sorted)", category: "Navigation", icon: Search },
    { id: "nav-enums", label: "View Enumerator Risk Observatory", category: "Navigation", icon: Users },
    { id: "nav-models", label: "Open Model Lab & Champion Promotion", category: "Navigation", icon: Sliders },
    { id: "nav-drift", label: "View Temporal Drift Dashboard (LFPR/WPR/UR)", category: "Navigation", icon: MapPin },
    { id: "search-delhi", label: "Filter State 07 (Delhi) Microdata", category: "State Filter", icon: MapPin },
    { id: "search-up", label: "Filter State 09 (Uttar Pradesh) Microdata", category: "State Filter", icon: MapPin },
    { id: "search-mh", label: "Filter State 27 (Maharashtra) Microdata", category: "State Filter", icon: MapPin },
  ];

  const filtered = commands.filter(c =>
    c.label.toLowerCase().includes(query.toLowerCase()) ||
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-xl glass-card rounded-2xl border border-slate-700 shadow-2xl overflow-hidden flex flex-col">
        {/* Search Input */}
        <div className="flex items-center px-4 py-3.5 border-b border-slate-800 gap-3">
          <Search className="w-4 h-4 text-blue-400 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, state code, or jump to section... (Press Esc to close)"
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none font-medium"
            autoFocus
          />
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-md text-slate-400">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 divide-y divide-slate-800/40">
          {filtered.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">
              No commands or state queries found matching &quot;{query}&quot;.
            </div>
          ) : (
            filtered.map((cmd) => {
              const IconComponent = cmd.icon;
              return (
                <button
                  key={cmd.id}
                  onClick={() => {
                    onSelectAction(cmd.id);
                    onClose();
                  }}
                  className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-blue-600/20 text-left transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 group-hover:text-blue-400 group-hover:border-blue-500/40">
                      <IconComponent className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-200 group-hover:text-white">{cmd.label}</p>
                      <span className="text-[10px] text-slate-500">{cmd.category}</span>
                    </div>
                  </div>
                  <kbd className="text-[10px] font-mono bg-slate-900 border border-slate-800 text-slate-400 px-2 py-0.5 rounded">
                    Enter
                  </kbd>
                </button>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
          <span>Tip: Use <kbd className="font-mono text-slate-400 px-1 bg-slate-800 rounded">Cmd+K</kbd> anywhere</span>
          <span>Survey Sentinel CLI</span>
        </div>
      </div>
    </div>
  );
};
