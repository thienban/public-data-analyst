"use client";

import { Company } from "@/lib/api";
import { AlertTriangle, ShieldCheck } from "lucide-react";

interface Props {
  companies: Company[];
}

const EFFECTIF_LABELS: Record<string, string> = {
  "00": "0",
  "01": "1-2",
  "02": "3-5",
  "03": "6-9",
  "11": "10-19",
  "12": "20-49",
  "21": "50-99",
  "22": "100-199",
  NN: "—",
};

export default function CompanyTable({ companies }: Props) {
  if (!companies.length) {
    return <p className="text-slate-400 text-sm">Aucune entreprise trouvée.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-800 text-slate-300">
            <th className="px-4 py-3 text-left">Entreprise</th>
            <th className="px-4 py-3 text-left">SIREN</th>
            <th className="px-4 py-3 text-left">NAF</th>
            <th className="px-4 py-3 text-left">Ville</th>
            <th className="px-4 py-3 text-left">Création</th>
            <th className="px-4 py-3 text-left">Effectif</th>
            <th className="px-4 py-3 text-left">Capital</th>
            <th className="px-4 py-3 text-left">Maturité</th>
            <th className="px-4 py-3 text-left">Statut</th>
          </tr>
        </thead>
        <tbody>
          {companies.map((c) => (
            <tr
              key={c.id}
              className={`border-t border-slate-700 hover:bg-slate-800/40 transition-colors ${
                c.is_fragile ? "bg-red-950/20" : ""
              }`}
            >
              <td className="px-4 py-2.5 font-medium text-white max-w-[200px] truncate">
                {c.nom_complet ?? "—"}
              </td>
              <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">
                {c.siren}
              </td>
              <td className="px-4 py-2.5">
                <span className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded text-xs font-mono">
                  {c.naf_code}
                </span>
              </td>
              <td className="px-4 py-2.5 text-slate-300">{c.ville ?? "—"}</td>
              <td className="px-4 py-2.5 text-slate-400 text-xs">
                {c.date_creation ? c.date_creation.slice(0, 4) : "—"}
              </td>
              <td className="px-4 py-2.5 text-slate-400 text-xs">
                {EFFECTIF_LABELS[c.tranche_effectif ?? "NN"] ?? c.tranche_effectif ?? "—"}
              </td>
              <td className="px-4 py-2.5 text-slate-300 text-xs">
                {c.capital_social != null
                  ? `${c.capital_social.toLocaleString("fr-FR")} €`
                  : "—"}
              </td>
              <td className="px-4 py-2.5 text-xs">
                <span className="text-slate-400">{c.maturity_label}</span>
              </td>
              <td className="px-4 py-2.5">
                {c.is_fragile ? (
                  <span className="flex items-center gap-1 text-red-400 text-xs font-medium">
                    <AlertTriangle className="w-3 h-3" />
                    Fragile
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-emerald-400 text-xs">
                    <ShieldCheck className="w-3 h-3" />
                    OK
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
