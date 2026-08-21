import React from "react";
import { FolderSearch, RefreshCw } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ElementType;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "No Survey Records Found",
  description = "The requested view or filter parameters returned zero records from PostgreSQL `survey_records`.",
  actionText = "Reload Microdata",
  onAction,
  icon: Icon = FolderSearch
}) => {
  return (
    <div className="glass-card p-10 rounded-2xl border border-slate-800 text-center flex flex-col items-center justify-center space-y-4 max-w-lg mx-auto my-8">
      <div className="p-4 bg-blue-950/40 border border-blue-800/40 rounded-2xl text-blue-400">
        <Icon className="w-10 h-10" />
      </div>

      <div className="space-y-1.5">
        <h3 className="text-base font-bold text-slate-100">{title}</h3>
        <p className="text-xs text-slate-400 max-w-sm leading-relaxed">{description}</p>
      </div>

      {onAction && (
        <button
          onClick={onAction}
          className="flex items-center gap-2 text-xs font-semibold px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-all shadow-md shadow-blue-900/30"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {actionText}
        </button>
      )}
    </div>
  );
};
