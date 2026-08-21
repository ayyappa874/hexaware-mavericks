"use client";

import { useEffect, useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { SkeletonLoader } from "../../components/ui/SkeletonLoader";
import { EmptyState } from "../../components/ui/EmptyState";
import { Layers, ShieldCheck, Plus, CheckCircle2, AlertOctagon } from "lucide-react";

interface RuleItem {
  id: string;
  rule_code: string;
  name: string;
  category: string;
  severity: string;
  rule_json: Record<string, any>;
  is_active: boolean;
}

export default function SchemaRegistryPage() {
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Form Modal State
  const [showModal, setShowModal] = useState<boolean>(false);
  const [ruleCode, setRuleCode] = useState<string>("RULE_CUSTOM_CHECK");
  const [ruleName, setRuleName] = useState<string>("Custom Validation Rule");
  const [category, setCategory] = useState<string>("range_check");
  const [severity, setSeverity] = useState<string>("HIGH");

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

  const fetchRules = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/rules`);
      if (res.ok) {
        setRules(await res.json());
      }
    } catch (err) {
      console.error("Failed to load rules:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/v1/rules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          survey_code: "PLFS_2024",
          rule_code: ruleCode,
          name: ruleName,
          category: category,
          severity: severity,
          rule_json: {
            field: "Earnings_Last_Month",
            operator: "between",
            min: 0,
            max: 500000,
            error_message: "Custom rule check failed."
          }
        })
      });
      if (res.ok) {
        setShowModal(false);
        await fetchRules();
      }
    } catch (err) {
      console.error("Rule creation failed:", err);
    }
  };

  const layoutFields = [
    { field: "State", bytes: "1-2", type: "STRING", desc: "MoSPI State Code (01 to 37)" },
    { field: "District", bytes: "3-4", type: "STRING", desc: "District Identifier" },
    { field: "Sector", bytes: "5-5", type: "INTEGER", desc: "Sector (1: Rural, 2: Urban)" },
    { field: "FSU", bytes: "6-10", type: "STRING", desc: "First Stage Unit (FSU Code)" },
    { field: "Age", bytes: "15-17", type: "INTEGER", desc: "Person Age in Years (0 to 110)" },
    { field: "Sex", bytes: "18-18", type: "INTEGER", desc: "Sex Code (1: Male, 2: Female, 3: Transgender)" },
    { field: "Usual_Principal_Activity_Status", bytes: "25-26", type: "INTEGER", desc: "Principal Activity Status (11..51 Employed, 81 Unemployed, 91..97 Inactive)" },
    { field: "Earnings_Last_Month", bytes: "40-48", type: "NUMERIC", desc: "Salaried/Self-Employed Last Month Earnings (₹)" },
    { field: "Daily_Wages", bytes: "49-55", type: "NUMERIC", desc: "Casual Labour Daily Wages (₹)" },
    { field: "Monthly_Exp", bytes: "56-64", type: "NUMERIC", desc: "Household Monthly Consumption Expenditure MPCE (₹)" },
    { field: "Multiplier", bytes: "65-72", type: "NUMERIC", desc: "Official MoSPI Sample Estimation Weight Multiplier" },
  ];

  return (
    <AppShell onRefresh={fetchRules} loading={loading}>
      {() => (
        <div className="space-y-8 animate-in fade-in duration-200">
          {/* Header Banner */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-blue-500/30">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Layers className="w-7 h-7 text-blue-400" />
                <h1 className="text-2xl font-black text-slate-100">
                  PLFS Schema Registry & Rule Engine
                </h1>
              </div>
              <p className="text-xs text-slate-400 max-w-xl">
                Registered 19-field MoSPI PLFS microdata layout and active JSON-defined validation rules stored in PostgreSQL.
              </p>
            </div>

            <button
              onClick={() => setShowModal(true)}
              className="mt-4 md:mt-0 flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-950/50 transition-all"
            >
              <Plus className="w-4 h-4" /> Register New Rule
            </button>
          </div>

          {/* Rules List */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" /> Active Configured Validation Rules ({rules.length})
              </h2>
              <span className="text-xs font-mono text-slate-500">Evaluated in Phase 1 Rule Engine</span>
            </div>

            {loading ? (
              <SkeletonLoader variant="table" count={4} />
            ) : rules.length === 0 ? (
              <EmptyState
                title="No Validation Rules Configured"
                description="No validation rules found in database."
                onAction={fetchRules}
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {rules.map((r) => (
                  <div key={r.id} className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-blue-400">{r.rule_code}</span>
                      <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded ${
                        r.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                        r.severity === 'HIGH' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                        'bg-sky-950 text-sky-300 border border-sky-800'
                      }`}>
                        {r.severity}
                      </span>
                    </div>

                    <h3 className="text-xs font-bold text-slate-200">{r.name}</h3>
                    <p className="text-[11px] text-slate-400 font-mono">Category: {r.category}</p>
                    <p className="text-xs text-slate-300 bg-slate-950 p-2 rounded border border-slate-900 font-mono text-[11px]">
                      {r.rule_json?.error_message || JSON.stringify(r.rule_json)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* PLFS Layout Table */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" /> MoSPI PLFS Byte-Layout Specification
            </h2>

            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Field Name</th>
                    <th className="py-3 px-4">Byte Range</th>
                    <th className="py-3 px-4">Data Type</th>
                    <th className="py-3 px-4">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                  {layoutFields.map((f) => (
                    <tr key={f.field} className="hover:bg-slate-900/60 transition-colors">
                      <td className="py-2.5 px-4 font-bold text-blue-400">{f.field}</td>
                      <td className="py-2.5 px-4 text-amber-400">{f.bytes}</td>
                      <td className="py-2.5 px-4">{f.type}</td>
                      <td className="py-2.5 px-4 font-sans text-slate-300">{f.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Create Rule Modal */}
          {showModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4">
              <div className="glass-card p-6 rounded-2xl border border-slate-700 max-w-md w-full space-y-4">
                <h3 className="text-base font-bold text-slate-100">Register New Validation Rule</h3>
                <form onSubmit={handleCreateRule} className="space-y-3">
                  <div>
                    <label className="text-xs text-slate-300">Rule Code</label>
                    <input
                      type="text"
                      value={ruleCode}
                      onChange={(e) => setRuleCode(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-100 p-2 rounded-lg font-mono outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-300">Rule Name</label>
                    <input
                      type="text"
                      value={ruleName}
                      onChange={(e) => setRuleName(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-100 p-2 rounded-lg outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-300">Category</label>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-100 p-2 rounded-lg outline-none"
                    >
                      <option value="range_check">Range Check</option>
                      <option value="logical_consistency">Logical Consistency</option>
                      <option value="referential_integrity">Referential Integrity</option>
                      <option value="existential_integrity">Existential Integrity</option>
                    </select>
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowModal(false)}
                      className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs rounded-lg"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg shadow-md"
                    >
                      Create Rule
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
