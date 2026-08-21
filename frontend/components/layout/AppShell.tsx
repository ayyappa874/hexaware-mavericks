"use client";

import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";
import { CommandPalette } from "../ui/CommandPalette";

interface AppShellProps {
  children: (props: {
    activeTab: string;
    setActiveTab: (t: string) => void;
    selectedRound: string;
    setSelectedRound: (r: string) => void;
  }) => React.ReactNode;
  systemStatus?: string;
  onRefresh?: () => void;
  loading?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  systemStatus = "online",
  onRefresh = () => {},
  loading = false
}) => {
  const [activeTab, setActiveTab] = useState("pulse");
  const [selectedRound, setSelectedRound] = useState("");
  const [isCmdOpen, setIsCmdOpen] = useState(false);

  const handleSelectAction = (actionId: string) => {
    if (actionId === "nav-pulse") setActiveTab("pulse");
    if (actionId === "nav-queue") setActiveTab("queue");
    if (actionId === "nav-enums") setActiveTab("observatory");
    if (actionId === "nav-models") setActiveTab("model_lab");
    if (actionId === "nav-drift") setActiveTab("temporal");
    if (actionId === "toggle") setIsCmdOpen(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex selection:bg-blue-500 selection:text-white">
      {/* Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <TopNav
          systemStatus={systemStatus}
          selectedRound={selectedRound}
          setSelectedRound={setSelectedRound}
          onRefresh={onRefresh}
          onOpenCommandPalette={() => setIsCmdOpen(true)}
          loading={loading}
        />

        {/* Dynamic Main Body */}
        <main className="flex-1 p-6 md:p-10 space-y-8 overflow-y-auto">
          {children({ activeTab, setActiveTab, selectedRound, setSelectedRound })}
        </main>
      </div>

      {/* Cmd+K Command Palette */}
      <CommandPalette
        isOpen={isCmdOpen}
        onClose={() => setIsCmdOpen(false)}
        onSelectAction={handleSelectAction}
      />
    </div>
  );
};
