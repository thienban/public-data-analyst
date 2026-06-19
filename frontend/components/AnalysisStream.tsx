"use client";

import { useState, useRef } from "react";
import { streamAnalysis, SSEChunk } from "@/lib/api";
import { Loader2, Zap, Wrench, CheckCircle } from "lucide-react";

interface Props {
  departements: string[];
  nafCodes: string[];
}

function renderMarkdown(md: string): string {
  return md
    .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold text-white mt-5 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-xl font-semibold text-white mt-6 mb-2 border-b border-slate-700 pb-1">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-white mt-6 mb-3">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="bg-slate-800 text-emerald-400 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 text-slate-300">• $1</li>')
    .replace(/(<li.*<\/li>\n?)+/g, (m) => `<ul class="my-2 space-y-1">${m}</ul>`)
    .replace(/\n\n/g, '</p><p class="mb-3 text-slate-300">')
    .replace(/^/, '<p class="mb-3 text-slate-300">')
    .replace(/$/, "</p>")
    .replace(
      /\|(.+)\|\n\|[-| :]+\|\n((?:\|.+\|\n?)*)/g,
      (_, header, rows) => {
        const ths = header.split("|").filter(Boolean).map((h: string) =>
          `<th class="bg-slate-700 text-white px-3 py-2 text-left text-sm">${h.trim()}</th>`
        ).join("");
        const trs = rows.trim().split("\n").map((row: string) => {
          const tds = row.split("|").filter(Boolean).map((d: string) =>
            `<td class="border border-slate-700 px-3 py-1.5 text-slate-300 text-sm">${d.trim()}</td>`
          ).join("");
          return `<tr>${tds}</tr>`;
        }).join("");
        return `<div class="overflow-x-auto my-4"><table class="w-full border-collapse"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table></div>`;
      }
    );
}

export default function AnalysisStream({ departements, nafCodes }: Props) {
  const [query, setQuery] = useState("");
  const [events, setEvents] = useState<SSEChunk[]>([]);
  const [finalText, setFinalText] = useState("");
  const [running, setRunning] = useState(false);
  const abortRef = useRef(false);

  async function handleRun() {
    if (!query.trim() || running) return;
    setEvents([]);
    setFinalText("");
    setRunning(true);
    abortRef.current = false;

    try {
      for await (const chunk of streamAnalysis(query, departements, nafCodes)) {
        if (abortRef.current) break;
        if (chunk.type === "text") {
          setFinalText((t) => t + (chunk.text ?? ""));
        } else {
          setEvents((e) => [...e, chunk]);
        }
      }
    } finally {
      setRunning(false);
    }
  }

  const toolCalls = events.filter((e) => e.type === "tool_call");

  return (
    <div className="space-y-5">
      {/* Query input */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-5">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Requête d&apos;analyse
        </label>
        <textarea
          className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-500 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          rows={3}
          placeholder="Ex: Analyse la concurrence des contractants généraux en Essonne. Identifie les opportunités de marché face aux passoires thermiques..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="flex items-center justify-between mt-3">
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
            {running ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            {running ? "Analyse en cours..." : "Lancer l'analyse"}
          </button>
        </div>
      </div>

      {/* Tool call trace */}
      {toolCalls.length > 0 && (
        <div className="space-y-1.5">
          {toolCalls.map((e, i) => (
            <div
              key={i}
              className="flex items-center gap-3 bg-slate-800/30 border border-slate-700 rounded-lg px-4 py-2 text-sm"
            >
              <Wrench className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span className="text-amber-400 font-mono">{e.tool}</span>
              <span className="text-slate-500 text-xs truncate">
                {JSON.stringify(e.input)}
              </span>
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0 ml-auto" />
            </div>
          ))}
        </div>
      )}

      {/* Final report */}
      {finalText && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-700">
            <Zap className="w-4 h-4 text-brand-500" />
            <span className="text-sm font-medium text-slate-300">
              Rapport d&apos;analyse de marché
            </span>
          </div>
          <div
            className="prose-dark"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(finalText) }}
          />
        </div>
      )}
    </div>
  );
}
