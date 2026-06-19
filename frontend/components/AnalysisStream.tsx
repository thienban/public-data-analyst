"use client";

import { useState } from "react";
import { streamAnalysis, SSEChunk } from "@/lib/api";
import { Loader2, BarChart2, CheckCircle2, Clock, FileText } from "lucide-react";

interface Props {
  departements: string[];
  nafCodes: string[];
}

const TOOL_LABELS: Record<string, { label: string; source: string }> = {
  search_companies: { label: "Recherche SIRENE", source: "api.gouv.fr / INSEE" },
  get_dpe_stats:    { label: "Stats DPE passoires", source: "ADEME / data.gouv.fr" },
  get_dvf_stats:    { label: "Transactions DVF", source: "Etalab / DVF" },
  insee_market_profile: { label: "Profil marché INSEE", source: "geo.api.gouv.fr / INSEE" },
  generate_report:  { label: "Génération rapport", source: "Moteur analytique" },
};

type StepStatus = "pending" | "running" | "done";

interface Step {
  tool: string;
  label: string;
  source: string;
  input: Record<string, unknown>;
  status: StepStatus;
}

function renderMarkdown(md: string): string {
  return md
    .replace(/```python([\s\S]*?)```/g,
      '<pre class="bg-slate-900 border border-slate-700 rounded p-4 my-4 overflow-x-auto text-sm"><code class="text-emerald-300 font-mono">$1</code></pre>')
    .replace(/```([\s\S]*?)```/g,
      '<pre class="bg-slate-900 border border-slate-700 rounded p-4 my-4 overflow-x-auto text-sm"><code class="text-emerald-300 font-mono">$1</code></pre>')
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-white mt-6 mb-2 flex items-center gap-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-lg font-semibold text-white mt-8 mb-3 border-b border-slate-700 pb-2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-white mt-4 mb-4">$1</h1>')
    .replace(/^---$/gm, '<hr class="border-slate-700 my-6" />')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/`([^`\n]+)`/g, '<code class="bg-slate-800 text-emerald-400 px-1.5 py-0.5 rounded text-xs font-mono">$1</code>')
    .replace(/^> (.+)$/gm, '<blockquote class="border-l-4 border-amber-500 pl-4 text-amber-200/80 italic my-3 text-sm">$1</blockquote>')
    .replace(/^- (.+)$/gm, '<li class="flex gap-2 text-slate-300 text-sm py-0.5"><span class="text-slate-500 mt-0.5 shrink-0">•</span><span>$1</span></li>')
    .replace(/(<li[\s\S]*?<\/li>\n?)+/g, (m) => `<ul class="my-2 space-y-0.5">${m}</ul>`)
    .replace(/^(\- \[ \] .+)$/gm, (_, line) =>
      `<li class="flex gap-2 text-slate-300 text-sm py-0.5"><span class="text-slate-600 shrink-0">☐</span><span>${line.replace('- [ ] ', '')}</span></li>`)
    .replace(
      /\|(.+)\|\n\|[-| :]+\|\n((?:\|.+\|\n?)*)/g,
      (_, header, rows) => {
        const ths = header.split("|").filter(Boolean).map((h: string) =>
          `<th class="bg-slate-700/80 text-slate-200 px-3 py-2 text-left text-xs font-medium whitespace-nowrap">${h.trim()}</th>`
        ).join("");
        const trs = rows.trim().split("\n").map((row: string, i: number) => {
          const tds = row.split("|").filter(Boolean).map((d: string) =>
            `<td class="border-t border-slate-700/50 px-3 py-2 text-slate-300 text-xs">${d.trim()}</td>`
          ).join("");
          return `<tr class="${i % 2 === 0 ? "" : "bg-slate-800/30"}">${tds}</tr>`;
        }).join("");
        return `<div class="overflow-x-auto my-4 rounded-lg border border-slate-700"><table class="w-full border-collapse"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table></div>`;
      }
    )
    .replace(/\n\n+/g, '</p><p class="mb-3 text-slate-300 text-sm leading-relaxed">')
    .replace(/^(?!<)/, '<p class="mb-3 text-slate-300 text-sm leading-relaxed">')
    + "</p>";
}

export default function AnalysisStream({ departements, nafCodes }: Props) {
  const [query, setQuery] = useState("");
  const [steps, setSteps] = useState<Step[]>([]);
  const [finalText, setFinalText] = useState("");
  const [running, setRunning] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);

  async function handleRun() {
    if (!query.trim() || running) return;
    setSteps([]);
    setFinalText("");
    setRunning(true);
    const t0 = Date.now();
    setStartTime(t0);
    setElapsed(null);

    try {
      for await (const chunk of streamAnalysis(query, departements, nafCodes)) {
        if (chunk.type === "tool_call") {
          const meta = TOOL_LABELS[chunk.tool ?? ""] ?? { label: chunk.tool, source: "API" };
          setSteps((s) => [
            ...s.filter((x) => !(x.tool === chunk.tool && JSON.stringify(x.input) === JSON.stringify(chunk.input))),
            { tool: chunk.tool ?? "", label: meta.label, source: meta.source, input: chunk.input ?? {}, status: "running" },
          ]);
        } else if (chunk.type === "tool_result") {
          setSteps((s) =>
            s.map((x) => x.tool === chunk.tool && x.status === "running" ? { ...x, status: "done" } : x)
          );
        } else if (chunk.type === "text") {
          setFinalText((t) => t + (chunk.text ?? ""));
        }
      }
    } finally {
      setElapsed(Math.round((Date.now() - t0) / 1000));
      setRunning(false);
    }
  }

  return (
    <div className="space-y-5">
      {/* Query input */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-5">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Requête d&apos;analyse de marché
        </label>
        <textarea
          className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-500 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500"
          rows={3}
          placeholder="Ex: Audit concurrence contractants généraux Essonne — croiser passoires thermiques et transactions DVF récentes..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="flex items-center justify-between mt-3 flex-wrap gap-2">
          <div className="flex flex-wrap gap-2">
            {[
              "Audit concurrence 43.39Z dept 91",
              "Passoires thermiques vs contractants 92",
              "Opportunités rénovation Antony Massy",
            ].map((q) => (
              <button
                key={q}
                onClick={() => setQuery(q)}
                className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1 rounded-full transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
          <button
            onClick={handleRun}
            disabled={running || !query.trim()}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart2 className="w-4 h-4" />}
            {running ? "Analyse en cours..." : "Analyser le marché"}
          </button>
        </div>
      </div>

      {/* Data collection progress */}
      {steps.length > 0 && (
        <div className="bg-slate-800/30 rounded-xl border border-slate-700 p-4">
          <p className="text-xs text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5" />
            Collecte des données publiques
          </p>
          <div className="space-y-2">
            {steps.map((step, i) => {
              const dept = (step.input.departement as string) ?? "";
              const naf = (step.input.naf_code as string) ?? "";
              const subtitle = [naf, dept].filter(Boolean).join(" · ");
              return (
                <div key={i} className="flex items-center gap-3">
                  {step.status === "running" ? (
                    <Loader2 className="w-4 h-4 text-amber-400 animate-spin shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-white font-medium">{step.label}</span>
                      {subtitle && (
                        <span className="text-xs text-slate-500 font-mono">{subtitle}</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">{step.source}</p>
                  </div>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      step.status === "done"
                        ? "bg-emerald-950/50 text-emerald-400"
                        : "bg-amber-950/50 text-amber-400"
                    }`}
                  >
                    {step.status === "done" ? "OK" : "..."}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Final report */}
      {finalText && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
          <div className="flex items-center justify-between mb-5 pb-3 border-b border-slate-700">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-500" />
              <span className="text-sm font-medium text-slate-300">
                Rapport d&apos;analyse de marché
              </span>
            </div>
            {elapsed && (
              <span className="text-xs text-slate-500">
                Généré en {elapsed}s · SIRENE · DPE · DVF · INSEE
              </span>
            )}
          </div>
          <div dangerouslySetInnerHTML={{ __html: renderMarkdown(finalText) }} />
        </div>
      )}
    </div>
  );
}
