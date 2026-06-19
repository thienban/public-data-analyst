"use client";

import { useState } from "react";
import AnalysisStream from "@/components/AnalysisStream";

const NAF_OPTIONS = [
  { value: "43.39Z", label: "43.39Z — Rénovation TCE" },
  { value: "41.20A", label: "41.20A — Contractant général" },
  { value: "71.11Z", label: "71.11Z — Architecture" },
  { value: "62.02A", label: "62.02A — Conseil IT" },
];

const DEPT_OPTIONS = [
  { value: "91", label: "91 — Essonne" },
  { value: "92", label: "92 — Hauts-de-Seine" },
  { value: "75", label: "75 — Paris" },
  { value: "93", label: "93 — Seine-St-Denis" },
];

export default function AnalysisPage() {
  const [nafCodes, setNafCodes] = useState<string[]>(["43.39Z", "41.20A"]);
  const [departements, setDepartements] = useState<string[]>(["91", "92"]);

  const toggle = (list: string[], setList: (v: string[]) => void, v: string) =>
    setList(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Analyse IA</h1>
        <p className="text-slate-400 mt-1">
          Agent Claude — Intelligence économique temps réel via APIs françaises
        </p>
      </div>

      {/* Scope selectors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
          <p className="text-sm font-medium text-slate-300 mb-3">Codes NAF analysés</p>
          <div className="flex flex-wrap gap-2">
            {NAF_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => toggle(nafCodes, setNafCodes, value)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  nafCodes.includes(value)
                    ? "bg-brand-600 border-brand-500 text-white"
                    : "bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-500"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
          <p className="text-sm font-medium text-slate-300 mb-3">Périmètre géographique</p>
          <div className="flex flex-wrap gap-2">
            {DEPT_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => toggle(departements, setDepartements, value)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  departements.includes(value)
                    ? "bg-brand-600 border-brand-500 text-white"
                    : "bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-500"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <AnalysisStream departements={departements} nafCodes={nafCodes} />
    </div>
  );
}
