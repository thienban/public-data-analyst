"use client";

import { InseeProfile } from "@/lib/api";
import { Users, MapPin, Hammer } from "lucide-react";

interface Props {
  profile: InseeProfile;
}

export default function InseeCard({ profile }: Props) {
  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-white font-semibold">
            INSEE — {profile.nom} ({profile.departement})
          </h3>
          <p className="text-slate-400 text-sm mt-0.5">Données démographiques & potentiel marché</p>
        </div>
        <Users className="w-5 h-5 text-indigo-400" />
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-white">
            {profile.population.toLocaleString("fr-FR")}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">Habitants</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-indigo-400">
            {profile.menages_estimes.toLocaleString("fr-FR")}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">Ménages estimés</p>
        </div>
        <div className="text-center">
          <div className="flex justify-center mb-1">
            <Hammer className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-amber-400">
            {profile.potentiel_renovation_annuel.toLocaleString("fr-FR")}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">Chantiers/an est.</p>
        </div>
      </div>

      <div className="border-t border-slate-700 pt-3">
        <p className="text-xs text-slate-400 mb-2 flex items-center gap-1.5">
          <MapPin className="w-3 h-3" />
          Communes prioritaires (prospection)
        </p>
        <div className="space-y-1">
          {profile.top_communes.slice(0, 5).map((c, i) => (
            <div key={c.code_insee} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                    i < 2
                      ? "bg-red-950/50 text-red-400"
                      : i < 4
                      ? "bg-amber-950/50 text-amber-400"
                      : "bg-slate-700 text-slate-400"
                  }`}
                >
                  {i < 2 ? "P1" : i < 4 ? "P2" : "P3"}
                </span>
                <span className="text-sm text-slate-300">{c.nom}</span>
              </div>
              <span className="text-xs text-slate-500">
                {c.population.toLocaleString("fr-FR")} hab.
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
