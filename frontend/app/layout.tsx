import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { BarChart2, Building2, Zap, FileText } from "lucide-react";

export const metadata: Metadata = {
  title: "Public Data Analyst — Intelligence Économique",
  description: "Analyse stratégique Bâtiment & IT via APIs publiques françaises",
};

const NAV = [
  { href: "/", label: "Tableau de bord", icon: BarChart2 },
  { href: "/companies", label: "Entreprises", icon: Building2 },
  { href: "/analysis", label: "Analyse IA", icon: Zap },
  { href: "/reports", label: "Rapports", icon: FileText },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="min-h-screen flex">
        {/* Sidebar */}
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
          <div className="p-5 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
                <BarChart2 className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm leading-tight">
                  Public Data Analyst
                </p>
                <p className="text-slate-500 text-xs">Intelligence Économique</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 p-3 space-y-0.5">
            {NAV.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors text-sm"
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            ))}
          </nav>

          <div className="p-4 border-t border-slate-800">
            <div className="text-xs text-slate-600 space-y-1">
              <p>Sources : SIRENE · ADEME · DVF</p>
              <p>Périmètre : 91 · 92</p>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto bg-slate-950">
          <div className="max-w-6xl mx-auto p-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
