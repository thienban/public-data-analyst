const BASE = "/api";

export interface Company {
  id: string;
  siren: string;
  nom_complet: string | null;
  naf_code: string | null;
  naf_libelle: string | null;
  date_creation: string | null;
  tranche_effectif: string | null;
  nature_juridique: string | null;
  capital_social: number | null;
  departement: string | null;
  ville: string | null;
  etat_administratif: string;
  fragility_score: number;
  is_fragile: boolean;
  maturity_label: string;
}

export interface CompanySearchResult {
  total: number;
  fragile_count: number;
  companies: Company[];
}

export interface DpeStats {
  total: number;
  passoires_count: number;
  passoires_pct: number;
  distribution: Record<string, number>;
}

export interface DvfStats {
  total_transactions: number;
  maisons: number;
  appartements: number;
  periode: string;
  indicateur_renovation: "FORT" | "MODERE" | "FAIBLE";
}

export interface Report {
  id: string;
  query: string;
  companies_count: number;
  created_at: string;
}

export async function searchCompanies(
  nafCodes: string[],
  departements: string[]
): Promise<CompanySearchResult> {
  const params = new URLSearchParams();
  nafCodes.forEach((c) => params.append("naf_codes", c));
  departements.forEach((d) => params.append("departements", d));
  const res = await fetch(`${BASE}/companies/search?${params}`);
  if (!res.ok) throw new Error("Erreur recherche entreprises");
  return res.json();
}

export async function getDpeStats(departement: string): Promise<DpeStats> {
  const res = await fetch(`${BASE}/dpe/stats/${departement}`);
  if (!res.ok) throw new Error("Erreur DPE");
  return res.json();
}

export async function getDvfStats(
  departement: string,
  monthsBack = 6
): Promise<DvfStats> {
  const res = await fetch(
    `${BASE}/dvf/stats/${departement}?months_back=${monthsBack}`
  );
  if (!res.ok) throw new Error("Erreur DVF");
  return res.json();
}

export interface InseeProfile {
  departement: string;
  nom: string;
  population: number;
  menages_estimes: number;
  potentiel_renovation_annuel: number;
  top_communes: {
    nom: string;
    code_insee: string;
    population: number;
    menages_estimes: number;
  }[];
}

export async function getInseeProfile(departement: string): Promise<InseeProfile> {
  const res = await fetch(`${BASE}/insee/profile/${departement}`);
  if (!res.ok) throw new Error("Erreur INSEE");
  return res.json();
}

export async function listReports(): Promise<Report[]> {
  const res = await fetch(`${BASE}/analysis/reports`);
  if (!res.ok) throw new Error("Erreur rapports");
  return res.json();
}

export interface SSEChunk {
  type: "start" | "thinking" | "tool_call" | "tool_result" | "text" | "done";
  text?: string;
  tool?: string;
  input?: Record<string, unknown>;
  message?: string;
}

export async function* streamAnalysis(
  query: string,
  departements: string[],
  nafCodes: string[]
): AsyncGenerator<SSEChunk> {
  const res = await fetch(`${BASE}/analysis/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, departements, naf_codes: nafCodes }),
  });

  if (!res.body) throw new Error("Pas de stream");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          yield JSON.parse(line.slice(6)) as SSEChunk;
        } catch {
          // skip malformed chunks
        }
      }
    }
  }
}
