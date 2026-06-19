"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { DpeStats } from "@/lib/api";

const CLASS_COLORS: Record<string, string> = {
  A: "#22c55e",
  B: "#86efac",
  C: "#fbbf24",
  D: "#f97316",
  E: "#ef4444",
  F: "#dc2626",
  G: "#7f1d1d",
};

interface Props {
  stats: DpeStats;
  departement: string;
}

export default function DpeChart({ stats, departement }: Props) {
  const data = Object.entries(stats.distribution)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([label, value]) => ({ label, value }));

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-white font-semibold">
            DPE — Département {departement}
          </h3>
          <p className="text-slate-400 text-sm mt-0.5">Distribution des classes énergétiques</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-red-400">{stats.passoires_pct}%</p>
          <p className="text-xs text-slate-400">Passoires (E/F/G)</p>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 12 }} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
            labelStyle={{ color: "#e2e8f0" }}
            formatter={(v: number) => [v.toLocaleString("fr-FR"), "Logements"]}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.label} fill={CLASS_COLORS[entry.label] ?? "#64748b"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-slate-500 mt-2">
        {stats.passoires_count.toLocaleString("fr-FR")} passoires thermiques sur{" "}
        {stats.total.toLocaleString("fr-FR")} logements diagnostiqués
      </p>
    </div>
  );
}
