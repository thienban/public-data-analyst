"use client";

import { useEffect, useState } from "react";
import {
  getDpeStats, getDvfStats, searchCompanies, getInseeProfile,
  DpeStats, DvfStats, InseeProfile,
} from "@/lib/api";
import DpeChart from "@/components/DpeChart";
import DvfCard from "@/components/DvfCard";
import InseeCard from "@/components/InseeCard";
import { AlertTriangle, Building2, TrendingUp, Flame } from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const [dpe91, setDpe91] = useState<DpeStats | null>(null);
  const [dpe92, setDpe92] = useState<DpeStats | null>(null);
  const [dvf91, setDvf91] = useState<DvfStats | null>(null);
  const [dvf92, setDvf92] = useState<DvfStats | null>(null);
  const [insee91, setInsee91] = useState<InseeProfile | null>(null);
  const [insee92, setInsee92] = useState<InseeProfile | null>(null);
  const [companyCount, setCompanyCount] = useState(0);
  const [fragileCount, setFragileCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [d91, d92, f91, f92, comps, i91, i92] = await Promise.allSettled([
          getDpeStats("91"),
          getDpeStats("92"),
          getDvfStats("91"),
          getDvfStats("92"),
          searchCompanies(["43.39Z", "41.20A", "71.11Z"], ["91", "92"]),
          getInseeProfile("91"),
          getInseeProfile("92"),
        ]);

        if (d91.status === "fulfilled") setDpe91(d91.value);
        if (d92.status === "fulfilled") setDpe92(d92.value);
        if (f91.status === "fulfilled") setDvf91(f91.value);
        if (f92.status === "fulfilled") setDvf92(f92.value);
        if (i91.status === "fulfilled") setInsee91(i91.value);
        if (i92.status === "fulfilled") setInsee92(i92.value);
        if (comps.status === "fulfilled") {
          setCompanyCount(comps.value.total);
          setFragileCount(comps.value.fragile_count);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const totalPopulation =
    (insee91?.population ?? 0) + (insee92?.population ?? 0);
  const totalPotentiel =
    (insee91?.potentiel_renovation_annuel ?? 0) +
    (insee92?.potentiel_renovation_annuel ?? 0);

  const KPI = [
    {
      label: "Entreprises actives",
      value: loading ? "—" : companyCount,
      sub: "NAF 71.11Z · 41.20A · 43.39Z",
      icon: Building2,
      color: "text-brand-500",
    },
    {
      label: "Entreprises fragiles",
      value: loading ? "—" : fragileCount,
      sub: "Capital insuffisant / BODACC",
      icon: AlertTriangle,
      color: "text-red-400",
    },
    {
      label: "Passoires DPE 91",
      value: loading ? "—" : dpe91 ? `${dpe91.passoires_pct}%` : "—",
      sub: `${dpe91?.passoires_count?.toLocaleString("fr-FR") ?? "?"} logements E/F/G`,
      icon: Flame,
      color: "text-orange-400",
    },
    {
      label: "Potentiel rénovation/an",
      value: loading ? "—" : totalPotentiel > 0 ? totalPotentiel.toLocaleString("fr-FR") : "—",
      sub: `${totalPopulation > 0 ? (totalPopulation / 1_000_000).toFixed(2) + "M" : "—"} habitants (91+92)`,
      icon: TrendingUp,
      color: "text-emerald-400",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Tableau de bord</h1>
        <p className="text-slate-400 mt-1">
          Intelligence économique — Bâtiment & IT — Départements 91 &amp; 92
        </p>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {KPI.map(({ label, value, sub, icon: Icon, color }) => (
          <div key={label} className="bg-slate-800/50 rounded-xl border border-slate-700 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-slate-400 text-xs uppercase tracking-wider">{label}</p>
                <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
                <p className="text-slate-500 text-xs mt-1">{sub}</p>
              </div>
              <Icon className={`w-5 h-5 ${color} mt-0.5`} />
            </div>
          </div>
        ))}
      </div>

      {/* INSEE profiles */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          Données INSEE — Profil de marché
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {insee91 && <InseeCard profile={insee91} />}
          {insee92 && <InseeCard profile={insee92} />}
          {!insee91 && !insee92 && loading && (
            <p className="text-slate-400 col-span-2">Chargement données INSEE...</p>
          )}
        </div>
      </div>

      {/* DPE charts */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          DPE — Diagnostic de Performance Énergétique
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {dpe91 && <DpeChart stats={dpe91} departement="91" />}
          {dpe92 && <DpeChart stats={dpe92} departement="92" />}
          {!dpe91 && !dpe92 && loading && (
            <p className="text-slate-400 col-span-2">Chargement des données DPE...</p>
          )}
        </div>
      </div>

      {/* DVF cards */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          DVF — Transactions Immobilières
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {dvf91 && <DvfCard stats={dvf91} departement="91" />}
          {dvf92 && <DvfCard stats={dvf92} departement="92" />}
        </div>
      </div>

      {/* CTA */}
      <div className="bg-brand-900/30 border border-brand-600/40 rounded-xl p-6 flex items-center justify-between">
        <div>
          <p className="text-white font-semibold">Lancer une analyse de marché complète</p>
          <p className="text-slate-400 text-sm mt-0.5">
            Croise SIRENE · DPE · DVF · INSEE et produit un rapport stratégique actionnable.
          </p>
        </div>
        <Link
          href="/analysis"
          className="bg-brand-600 hover:bg-brand-500 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
        >
          Analyser le marché →
        </Link>
      </div>
    </div>
  );
}
