"use client";

import { DvfStats } from "@/lib/api";
import { TrendingUp, Home, Building2 } from "lucide-react";

const INDICATOR_CONFIG = {
  FORT: { color: "text-red-400", bg: "bg-red-950/40 border-red-800", label: "Fort potentiel" },
  MODERE: { color: "text-amber-400", bg: "bg-amber-950/40 border-amber-800", label: "Potentiel modéré" },
  FAIBLE: { color: "text-slate-400", bg: "bg-slate-800/40 border-slate-700", label: "Faible activité" },
};

interface Props {
  stats: DvfStats;
  departement: string;
}

export default function DvfCard({ stats, departement }: Props) {
  const cfg = INDICATOR_CONFIG[stats.indicateur_renovation];

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-white font-semibold">
            DVF — Département {departement}
          </h3>
          <p className="text-slate-400 text-sm mt-0.5">
            Transactions immobilières — {stats.periode}
          </p>
        </div>
        <TrendingUp className="w-5 h-5 text-brand-500" />
      </div>

      <div className={`rounded-lg border px-4 py-3 mb-4 ${cfg.bg}`}>
        <p className={`text-sm font-semibold ${cfg.color}`}>
          Indicateur rénovation : {cfg.label}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{stats.total_transactions}</p>
          <p className="text-xs text-slate-400 mt-0.5">Total ventes</p>
        </div>
        <div className="text-center">
          <div className="flex justify-center mb-1">
            <Home className="w-4 h-4 text-brand-500" />
          </div>
          <p className="text-2xl font-bold text-white">{stats.maisons}</p>
          <p className="text-xs text-slate-400 mt-0.5">Maisons</p>
        </div>
        <div className="text-center">
          <div className="flex justify-center mb-1">
            <Building2 className="w-4 h-4 text-slate-400" />
          </div>
          <p className="text-2xl font-bold text-white">{stats.appartements}</p>
          <p className="text-xs text-slate-400 mt-0.5">Appartements</p>
        </div>
      </div>

      <p className="text-xs text-slate-500 mt-3 border-t border-slate-700 pt-3">
        Une vente de maison = indicateur fort de rénovation imminente (cuisine, salle de bain, isolation)
      </p>
    </div>
  );
}
