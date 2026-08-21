"use client";

import { useEffect, useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { SkeletonLoader } from "../../components/ui/SkeletonLoader";
import { EmptyState } from "../../components/ui/EmptyState";
import { Sliders, Cpu, Award, CheckCircle2, Play, Activity } from "lucide-react";

interface ModelItem {
  id: string;
  model_name: string;
  version: string;
  algorithm: string;
  hyperparameters: Record<string, any>;
  metrics: {
    precision: number;
    recall: number;
    f1_score: number;
    roc_auc: number;
    train_samples: number;
    test_samples: number;
  };
  is_active: boolean;
  trained_at: string;
}

export default function ModelLabPage() {
  const [models, setModels] = useState<ModelItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [training, setTraining] = useState<boolean>(false);

  // Form State
  const [modelName, setModelName] = useState<string>("PLFS_IsolationForest_Custom");
  const [algorithm, setAlgorithm] = useState<string>("ISOLATION_FOREST");
  const [nEstimators, setNEstimators] = useState<number>(100);
  const [contamination, setContamination] = useState<number>(0.05);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const fetchModels = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/models`);
      if (res.ok) {
        setModels(await res.json());
      }
    } catch (err) {
      console.error("Failed to load models:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleTrainSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTraining(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/models/train`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          survey_code: "PLFS_2024",
          model_name: modelName,
          algorithm: algorithm,
          hyperparameters: { n_estimators: nEstimators, contamination: contamination },
          train_round: "2023-24",
          test_round: "2024-25"
        })
      });
      if (res.ok) {
        await fetchModels();
      }
    } catch (err) {
      console.error("Model train failed:", err);
    } finally {
      setTraining(false);
    }
  };

  const handlePromote = async (modelId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/models/${modelId}/promote`, {
        method: "POST"
      });
      if (res.ok) {
        await fetchModels();
      }
    } catch (err) {
      console.error("Model promote failed:", err);
    }
  };

  return (
    <AppShell onRefresh={fetchModels} loading={loading}>
      {() => (
        <div className="space-y-8 animate-in fade-in duration-200">
          {/* Header Banner */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-indigo-500/30">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Sliders className="w-7 h-7 text-indigo-400" />
                <h1 className="text-2xl font-black text-slate-100">
                  Model Lab & Evaluation Harness
                </h1>
              </div>
              <p className="text-xs text-slate-400 max-w-xl">
                Train custom ML models on historical PLFS round microdata (2023-24) and evaluate precision/recall against held-out rounds (2024-25).
              </p>
            </div>
          </div>

          {/* Training Form Card */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-blue-400" /> Train Custom Anomaly Model
            </h2>

            <form onSubmit={handleTrainSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Model Name</label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 text-slate-100 text-xs font-mono rounded-xl px-3 py-2 outline-none focus:border-blue-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Algorithm</label>
                <select
                  value={algorithm}
                  onChange={(e) => setAlgorithm(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 text-slate-100 text-xs font-semibold rounded-xl px-3 py-2 outline-none"
                >
                  <option value="ISOLATION_FOREST">Isolation Forest</option>
                  <option value="LOF">Local Outlier Factor (LOF)</option>
                  <option value="STATISTICAL_ENSEMBLE">Statistical Ensemble</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Contamination ({contamination})</label>
                <input
                  type="range"
                  min="0.01"
                  max="0.20"
                  step="0.01"
                  value={contamination}
                  onChange={(e) => setContamination(Number(e.target.value))}
                  className="w-full cursor-pointer"
                />
              </div>

              <button
                type="submit"
                disabled={training}
                className="flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-950/50 transition-all disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                {training ? "Training Model..." : "Train & Evaluate"}
              </button>
            </form>
          </div>

          {/* Trained Models Registry Table */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-400" /> Trained Model Version Registry
              </h2>
              <span className="text-xs font-mono text-slate-500">Only 1 Champion Model Active per Survey</span>
            </div>

            {loading ? (
              <SkeletonLoader variant="table" count={4} />
            ) : models.length === 0 ? (
              <EmptyState
                title="No Models Trained Yet"
                description="Use the form above to train your first anomaly model against PLFS microdata."
                onAction={fetchModels}
              />
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Model Name</th>
                      <th className="py-3 px-4">Version</th>
                      <th className="py-3 px-4">Algorithm</th>
                      <th className="py-3 px-4">Precision</th>
                      <th className="py-3 px-4">Recall</th>
                      <th className="py-3 px-4">F1 Score</th>
                      <th className="py-3 px-4">ROC AUC</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                    {models.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-900/60 transition-colors">
                        <td className="py-3 px-4 font-bold text-slate-200">{m.model_name}</td>
                        <td className="py-3 px-4 text-blue-400">{m.version}</td>
                        <td className="py-3 px-4">{m.algorithm}</td>
                        <td className="py-3 px-4 text-emerald-400 font-bold">{m.metrics?.precision}</td>
                        <td className="py-3 px-4 text-sky-400 font-bold">{m.metrics?.recall}</td>
                        <td className="py-3 px-4 text-amber-400 font-bold">{m.metrics?.f1_score}</td>
                        <td className="py-3 px-4">{m.metrics?.roc_auc}</td>
                        <td className="py-3 px-4 font-sans">
                          {m.is_active ? (
                            <span className="px-2.5 py-1 bg-amber-950 text-amber-300 border border-amber-800 rounded-full font-bold text-[10px] flex items-center gap-1 w-fit">
                              <Award className="w-3 h-3 text-amber-400" /> ACTIVE CHAMPION
                            </span>
                          ) : (
                            <span className="px-2.5 py-1 bg-slate-900 text-slate-400 border border-slate-800 rounded-full text-[10px]">
                              Inactive Candidate
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 font-sans">
                          {!m.is_active && (
                            <button
                              onClick={() => handlePromote(m.id)}
                              className="px-3 py-1 bg-blue-950 hover:bg-blue-900 text-blue-300 border border-blue-800 rounded-lg text-xs font-semibold transition-all"
                            >
                              Promote Champion
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}
