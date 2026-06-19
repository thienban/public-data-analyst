"use client";

import { useEffect, useState } from "react";
import { listReports, Report } from "@/lib/api";
import { FileText, Clock } from "lucide-react";
import Link from "next/link";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listReports()
      .then(setReports)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Rapports sauvegardés</h1>
        <p className="text-slate-400 mt-1">
          Historique des analyses stratégiques générées par l&apos;agent IA
        </p>
      </div>

      {loading && <p className="text-slate-400">Chargement...</p>}

      {!loading && reports.length === 0 && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-8 text-center">
          <FileText className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">Aucun rapport généré pour l&apos;instant.</p>
          <Link href="/analysis" className="text-brand-500 text-sm mt-2 inline-block hover:underline">
            Lancer votre première analyse →
          </Link>
        </div>
      )}

      <div className="space-y-3">
        {reports.map((r) => (
          <div
            key={r.id}
            className="bg-slate-800/50 rounded-xl border border-slate-700 p-5 flex items-center justify-between"
          >
            <div className="flex items-start gap-3">
              <FileText className="w-5 h-5 text-brand-500 mt-0.5 shrink-0" />
              <div>
                <p className="text-white font-medium">{r.query}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="flex items-center gap-1 text-slate-500 text-xs">
                    <Clock className="w-3 h-3" />
                    {new Date(r.created_at).toLocaleDateString("fr-FR", {
                      day: "2-digit",
                      month: "long",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>
            </div>
            <Link
              href={`/reports/${r.id}`}
              className="text-brand-500 hover:text-brand-400 text-sm font-medium transition-colors"
            >
              Voir →
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
