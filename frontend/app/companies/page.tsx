"use client";

import { useState } from "react";
import { searchCompanies, CompanySearchResult } from "@/lib/api";
import CompanyTable from "@/components/CompanyTable";
import { Search, AlertTriangle } from "lucide-react";

const NAF_OPTIONS = [
  { value: "43.39Z", label: "43.39Z — Rénovation TCE" },
  { value: "41.20A", label: "41.20A — Contractant général" },
  { value: "71.11Z", label: "71.11Z — Architecture" },
  { value: "43.21A", label: "43.21A — Électricité" },
  { value: "43.22A", label: "43.22A — Plomberie / Gaz" },
  { value: "62.01Z", label: "62.01Z — Programmation IT" },
  { value: "62.02A", label: "62.02A — Conseil IT" },
];

const DEPT_OPTIONS = [
  { value: "91", label: "91 — Essonne" },
  { value: "92", label: "92 — Hauts-de-Seine" },
  { value: "75", label: "75 — Paris" },
  { value: "93", label: "93 — Seine-Saint-Denis" },
  { value: "94", label: "94 — Val-de-Marne" },
];

export default function CompaniesPage() {
  const [selectedNaf, setSelectedNaf] = useState<string[]>(["43.39Z", "41.20A"]);
  const [selectedDepts, setSelectedDepts] = useState<string[]>(["91", "92"]);
  const [result, setResult] = useState<CompanySearchResult | null>(null);
  const [loading, setLoading] = useState(false);

  function toggleNaf(v: string) {
    setSelectedNaf((s) => s.includes(v) ? s.filter((x) => x !== v) : [...s, v]);
  }
  function toggleDept(v: string) {
    setSelectedDepts((s) => s.includes(v) ? s.filter((x) => x !== v) : [...s, v]);
  }

  async function handleSearch() {
    if (!selectedNaf.length || !selectedDepts.length) return;
    setLoading(true);
    try {
      const r = await searchCompanies(selectedNaf, selectedDepts);
      setResult(r);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Audit Entreprises</h1>
        <p className="text-slate-400 mt-1">
          Recherche via API SIRENE — filtres NAF + département
        </p>
      </div>

      {/* Filters */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-5 space-y-4">
        <div>
          <p className="text-sm font-medium text-slate-300 mb-2">Codes NAF</p>
          <div className="flex flex-wrap gap-2">
            {NAF_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => toggleNaf(value)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  selectedNaf.includes(value)
                    ? "bg-brand-600 border-brand-500 text-white"
                    : "bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-500"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-slate-300 mb-2">Départements</p>
          <div className="flex flex-wrap gap-2">
            {DEPT_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => toggleDept(value)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  selectedDepts.includes(value)
                    ? "bg-brand-600 border-brand-500 text-white"
                    : "bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-500"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleSearch}
          disabled={loading || !selectedNaf.length || !selectedDepts.length}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Search className="w-4 h-4" />
          {loading ? "Recherche..." : "Rechercher"}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-white font-semibold">
              {result.total} entreprises trouvées
            </p>
            {result.fragile_count > 0 && (
              <div className="flex items-center gap-2 bg-red-950/40 border border-red-800 rounded-lg px-3 py-1.5">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <span className="text-red-400 text-sm font-medium">
                  {result.fragile_count} entreprise(s) fragile(s) détectée(s)
                </span>
              </div>
            )}
          </div>
          <CompanyTable companies={result.companies} />

          <div className="bg-amber-950/30 border border-amber-800/50 rounded-lg p-4">
            <p className="text-amber-300 text-sm font-medium mb-1">
              ⚠️ Rappel obligations légales (sous-traitants)
            </p>
            <p className="text-amber-200/70 text-xs">
              Avant toute sélection, vérifier : attestation décennale valide, attestation RCD,
              état BODACC (procédures collectives), kbis &lt; 3 mois, et régularité Urssaf.
              Les entreprises signalées &quot;Fragile&quot; nécessitent un contrôle renforcé.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
