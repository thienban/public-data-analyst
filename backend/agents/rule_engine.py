"""
Rule-based strategic market analysis engine.
Implements the 3-axis analytical runbook:
  1. Competitive Audit & Data Cleaning
  2. Advanced Data Crossing & Correlation
  3. Actionable Business Insights
"""

from __future__ import annotations
from datetime import datetime
from backend.models.company import FRAGILITY_THRESHOLDS, NAF_LABELS


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EFFECTIF_LABELS: dict[str, str] = {
    "00": "0 salarié",
    "01": "1-2 sal.",
    "02": "3-5 sal.",
    "03": "6-9 sal.",
    "11": "10-19 sal.",
    "12": "20-49 sal.",
    "21": "50-99 sal.",
    "22": "100-199 sal.",
    "NN": "—",
}

LEGAL_RISK: dict[str, tuple[str, str]] = {
    # (risk_level, explanation)
    "5710": ("FAIBLE", "SAS — capital variable, structure souple"),
    "5720": ("FAIBLE", "SASU — unipersonnel, responsabilité limitée"),
    "5499": ("MOYEN", "SARL — gestion classique PME"),
    "5498": ("MOYEN", "EURL — unipersonnel, risque solo"),
    "1000": ("ÉLEVÉ", "Entrepreneur individuel — pas de séparation patrimoniale"),
    "2110": ("ÉLEVÉ", "SNC — responsabilité indéfinie et solidaire"),
}

MATURITY_SEGMENTS = [
    ("Startup (<3 ans)", lambda a: a < 3),
    ("Croissance (3-7 ans)", lambda a: 3 <= a < 7),
    ("Établie (7-15 ans)", lambda a: 7 <= a < 15),
    ("Senior (15+ ans)", lambda a: a >= 15),
]


# ---------------------------------------------------------------------------
# Axis 1 — Data Cleaning & Competitive Audit
# ---------------------------------------------------------------------------

def clean_companies(companies: list[dict]) -> list[dict]:
    """
    Deduplicate by SIREN, remove inactive / invalid entries.
    Returns a sorted, clean list.
    """
    seen_sirens: set[str] = set()
    cleaned: list[dict] = []
    for c in companies:
        siren = c.get("siren") or ""
        if not siren or siren in seen_sirens:
            continue
        if c.get("etat_administratif", "A") != "A":
            continue
        seen_sirens.add(siren)
        cleaned.append(c)
    # Sort: most established first, then by name
    cleaned.sort(key=lambda c: (c.get("date_creation") or "9999", c.get("nom_complet") or ""))
    return cleaned


def _age(date_creation: str | None) -> int | None:
    if not date_creation:
        return None
    try:
        return datetime.now().year - int(date_creation[:4])
    except ValueError:
        return None


def _maturity_label(date_creation: str | None) -> str:
    age = _age(date_creation)
    if age is None:
        return "Inconnue"
    for label, pred in MATURITY_SEGMENTS:
        if pred(age):
            return label
    return "Inconnue"


def _is_fragile(company: dict) -> bool:
    naf = company.get("naf_code", "")
    capital = company.get("capital_social")
    threshold = FRAGILITY_THRESHOLDS.get(naf, 0)
    if threshold and capital is not None and capital < threshold:
        return True
    if company.get("bodacc_alerts", 0) > 0:
        return True
    return False


def _legal_risk_label(nature_juridique: str | None) -> tuple[str, str]:
    if not nature_juridique:
        return ("—", "Non renseigné")
    return LEGAL_RISK.get(nature_juridique, ("—", "Structure non catégorisée"))


def segment_companies(companies: list[dict]) -> dict:
    """
    Segment companies by:
    - NAF code breakdown
    - Maturity bucket
    - Headcount tranche
    - Legal structure risk
    """
    naf_map: dict[str, list[dict]] = {}
    maturity_map: dict[str, int] = {k: 0 for k, _ in MATURITY_SEGMENTS}
    maturity_map["Inconnue"] = 0
    effectif_map: dict[str, int] = {}
    legal_risk_map: dict[str, int] = {"FAIBLE": 0, "MOYEN": 0, "ÉLEVÉ": 0, "—": 0}

    for c in companies:
        naf = c.get("naf_code") or "—"
        naf_map.setdefault(naf, []).append(c)

        bucket = _maturity_label(c.get("date_creation"))
        maturity_map[bucket] = maturity_map.get(bucket, 0) + 1

        eff = c.get("tranche_effectif") or "NN"
        effectif_map[eff] = effectif_map.get(eff, 0) + 1

        risk, _ = _legal_risk_label(c.get("nature_juridique"))
        legal_risk_map[risk] = legal_risk_map.get(risk, 0) + 1

    return {
        "by_naf": naf_map,
        "by_maturity": maturity_map,
        "by_effectif": effectif_map,
        "by_legal_risk": legal_risk_map,
    }


# ---------------------------------------------------------------------------
# Axis 2 — Data Crossing & Correlation
# ---------------------------------------------------------------------------

def correlation_analysis(
    companies: list[dict],
    dpe_stats: dict,
    dvf_stats: dict,
    insee_profiles: list[dict],
) -> dict:
    """
    Compute key density ratios and correlation scores.
    Returns a dict of market indicators.
    """
    total_companies = len(companies)
    passoires = dpe_stats.get("passoires_count", 0)
    transactions = dvf_stats.get("total_transactions", 0)
    maisons = dvf_stats.get("maisons", 0)
    total_menages = sum(p.get("menages_estimes", 0) for p in insee_profiles)
    total_potentiel = sum(p.get("potentiel_renovation_annuel", 0) for p in insee_profiles)

    renovateurs = sum(
        1 for c in companies if c.get("naf_code") in ("43.39Z", "41.20A")
    )
    architectes = sum(1 for c in companies if c.get("naf_code") == "71.11Z")

    # Density ratios
    passoires_per_renovateur = round(passoires / renovateurs, 0) if renovateurs else None
    maisons_per_renovateur = round(maisons / renovateurs, 0) if renovateurs else None
    potentiel_per_renovateur = round(total_potentiel / renovateurs, 0) if renovateurs else None

    # Market saturation (0=undersupplied, 100=saturated)
    # Benchmark: 1 renovateur per 500 passoires = well-covered
    saturation = min(100, int(renovateurs / max(passoires, 1) * 50000)) if passoires else None

    # Risk concentration
    fragile = [c for c in companies if _is_fragile(c)]
    fragile_pct = round(len(fragile) / total_companies * 100, 1) if total_companies else 0

    # Maturity risk (too many startups in heavy construction)
    startup_renovateurs = sum(
        1 for c in companies
        if c.get("naf_code") in ("43.39Z", "41.20A") and (_age(c.get("date_creation")) or 99) < 3
    )

    return {
        "total_companies": total_companies,
        "renovateurs": renovateurs,
        "architectes": architectes,
        "passoires": passoires,
        "maisons": maisons,
        "total_menages": total_menages,
        "total_potentiel": total_potentiel,
        "passoires_per_renovateur": passoires_per_renovateur,
        "maisons_per_renovateur": maisons_per_renovateur,
        "potentiel_per_renovateur": potentiel_per_renovateur,
        "saturation_score": saturation,
        "fragile_count": len(fragile),
        "fragile_pct": fragile_pct,
        "startup_renovateurs": startup_renovateurs,
        "fragile_list": fragile[:5],
    }


def _gap_signal(passoires_per_reno: float | None) -> tuple[str, str]:
    if passoires_per_reno is None:
        return ("INDÉTERMINÉ", "Données insuffisantes")
    if passoires_per_reno > 2000:
        return ("CRITIQUE", "Déficit sévère d'acteurs face à la demande")
    if passoires_per_reno > 1000:
        return ("FORT", "Marché sous-couvert — opportunité de positionnement immédiate")
    if passoires_per_reno > 500:
        return ("MODÉRÉ", "Marché partiellement couvert — croissance possible")
    return ("FAIBLE", "Marché mature — différenciation nécessaire")


# ---------------------------------------------------------------------------
# Axis 3 — Actionable Business Insights
# ---------------------------------------------------------------------------

def _opportunity_score(corr: dict, passoires_pct: float) -> int:
    score = 0
    # DPE weight (40)
    score += min(40, int(passoires_pct * 0.8))
    # DVF weight (30)
    score += min(30, int(corr["maisons"] / 5))
    # Market gap weight (30)
    ppr = corr.get("passoires_per_renovateur") or 0
    score += min(30, int(ppr / 100))
    return min(100, score)


def _insee_prospecting_zones(insee_profiles: list[dict]) -> list[dict]:
    zones = []
    for profile in insee_profiles:
        for c in profile.get("top_communes", [])[:4]:
            zones.append({
                "commune": c["nom"],
                "code_insee": c["code_insee"],
                "departement": profile["departement"],
                "population": c["population"],
                "menages": c["menages_estimes"],
                "potentiel_annuel": int(c["menages_estimes"] * 0.012),
            })
    zones.sort(key=lambda z: -z["potentiel_annuel"])
    return zones[:8]


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------

def generate_report(
    companies: list[dict],
    dpe_stats: dict,
    dvf_stats: dict,
    query: str,
    departements: list[str],
    naf_codes: list[str],
    insee_profiles: list[dict] | None = None,
) -> str:
    insee_profiles = insee_profiles or []
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    dept_str = " · ".join(departements)
    naf_str = " · ".join(naf_codes)

    # --- AXIS 1: Clean + Segment ---
    companies = clean_companies(companies)
    segments = segment_companies(companies)
    total = len(companies)

    # --- AXIS 2: Correlate ---
    passoires_pct = dpe_stats.get("passoires_pct", 0)
    dpe_total = dpe_stats.get("total", 0)
    corr = correlation_analysis(companies, dpe_stats, dvf_stats, insee_profiles)
    gap_level, gap_desc = _gap_signal(corr.get("passoires_per_renovateur"))

    # --- AXIS 3: Score ---
    opp_score = _opportunity_score(corr, passoires_pct)
    prospecting_zones = _insee_prospecting_zones(insee_profiles)

    L: list[str] = []

    # ---- HEADER ----
    L += [
        f"# Rapport d'Analyse de Marché — {dept_str}",
        f"",
        f"**Généré le {now}** | NAF : `{naf_str}` | Périmètre : `{dept_str}`",
        f"",
        "---",
        "",
    ]

    # ---- EXECUTIVE SUMMARY ----
    L += [
        "## Synthèse Exécutive",
        "",
        f"| Indicateur | Valeur | Signal |",
        f"|---|---|---|",
        f"| Acteurs SIRENE actifs | **{total}** | Après déduplication et nettoyage |",
        f"| Rénovateurs (43.39Z + 41.20A) | **{corr['renovateurs']}** | Offreurs directs |",
        f"| Passoires thermiques (DPE E/F/G) | **{corr['passoires']:,}** | Demande potentielle |".replace(",", " "),
        f"| Ratio passoires / rénovateur | **{corr['passoires_per_renovateur'] or '—'}** | Gap de marché |",
        f"| Score opportunité global | **{opp_score}/100** | Synthèse multicritère |",
        f"| Niveau de gap | **{gap_level}** | {gap_desc} |",
        f"| Entreprises fragiles | **{corr['fragile_count']} ({corr['fragile_pct']}%)** | Capital / BODACC |",
        "",
    ]

    # ====================================================================
    # AXE 1 — COMPETITIVE AUDIT & DATA CLEANING
    # ====================================================================
    L += [
        "---",
        "",
        "## Axe 1 — Audit Concurrentiel & Nettoyage des Données",
        "",
        f"> Base nettoyée : **{total}** entreprises actives (doublons supprimés, inactifs exclus).",
        "",
    ]

    # NAF breakdown
    L += [
        "### 1.1 Répartition par Code NAF",
        "",
        "| Code NAF | Secteur | Nb acteurs | Part | Signal marché |",
        "|---|---|---|---|---|",
    ]
    naf_signals = {
        "43.39Z": "Cœur de cible rénovation TCE",
        "41.20A": "Contractant général — maître d'œuvre",
        "71.11Z": "Prescripteur — levier partenariat",
        "43.21A": "Spécialiste électricité — sous-traitant potentiel",
        "43.22A": "Spécialiste plomberie/CVC — sous-traitant potentiel",
        "62.01Z": "Digital — hors cible directe",
        "62.02A": "Conseil IT — hors cible directe",
    }
    for naf, items in sorted(segments["by_naf"].items(), key=lambda x: -len(x[1])):
        pct = round(len(items) / total * 100, 1) if total else 0
        label = NAF_LABELS.get(naf, naf)
        signal = naf_signals.get(naf, "—")
        L.append(f"| `{naf}` | {label} | **{len(items)}** | {pct}% | {signal} |")
    L.append("")

    # Maturity segmentation
    L += [
        "### 1.2 Segmentation par Maturité",
        "",
        "| Segment | Nb | % | Profil de risque |",
        "|---|---|---|---|",
    ]
    maturity_risk = {
        "Startup (<3 ans)": "🔴 Vérifier décennale, kbis, expérience chantier",
        "Croissance (3-7 ans)": "🟡 Surveiller trésorerie et montée en charge",
        "Établie (7-15 ans)": "🟢 Profil fiable — backbone du marché local",
        "Senior (15+ ans)": "🟢 Expérimenté — potentiel partenariat stratégique",
        "Inconnue": "⚪ Date de création non renseignée",
    }
    for seg, count in segments["by_maturity"].items():
        if count == 0:
            continue
        pct = round(count / total * 100, 1) if total else 0
        L.append(f"| {seg} | {count} | {pct}% | {maturity_risk.get(seg, '—')} |")
    L.append("")

    # Headcount segmentation
    L += [
        "### 1.3 Segmentation par Capacité Opérationnelle (Effectif)",
        "",
        "| Tranche | Nb acteurs | Profil opérationnel |",
        "|---|---|---|",
    ]
    eff_profiles = {
        "00": "Micro — exécution solo, limité grands chantiers",
        "01": "Artisan — 1 équipe, chantiers résidentiels",
        "02": "TPE — capacité multi-chantiers limitée",
        "03": "TPE+ — peut absorber des lots importants",
        "11": "PME — structure commerciale organisée",
        "12": "PME+ — capacité contractant général potentiel",
        "21": "ETI — contractant général établi",
        "22": "Grande PME — concurrence directe majeure",
    }
    for eff, count in sorted(segments["by_effectif"].items(), key=lambda x: -x[1]):
        if count == 0:
            continue
        label = EFFECTIF_LABELS.get(eff, eff)
        profile = eff_profiles.get(eff, "—")
        L.append(f"| {label} | {count} | {profile} |")
    L.append("")

    # Legal structure risk
    L += [
        "### 1.4 Risque Structurel par Forme Juridique",
        "",
        "| Niveau de risque | Nb acteurs | Interprétation |",
        "|---|---|---|",
    ]
    legal_interp = {
        "FAIBLE": "Structure solide — séparation patrimoine / responsabilité limitée",
        "MOYEN": "Structure standard PME — surveiller capital et bilans",
        "ÉLEVÉ": "Risque élevé — responsabilité illimitée ou structure solo non capitalisée",
        "—": "Forme juridique non identifiée",
    }
    for risk, count in segments["by_legal_risk"].items():
        if count == 0:
            continue
        L.append(f"| **{risk}** | {count} | {legal_interp.get(risk, '—')} |")
    L.append("")

    # Fragility alerts
    if corr["fragile_list"]:
        L += [
            "### 1.5 Alertes Fragilité Structurelle",
            "",
            "| Entreprise | SIREN | NAF | Capital déclaré | Seuil attendu | Alerte |",
            "|---|---|---|---|---|---|",
        ]
        for c in corr["fragile_list"]:
            naf = c.get("naf_code", "—")
            capital = c.get("capital_social")
            threshold = FRAGILITY_THRESHOLDS.get(naf, 0)
            cap_str = f"{capital:,} €".replace(",", " ") if capital is not None else "—"
            thr_str = f"{threshold:,} €".replace(",", " ") if threshold else "—"
            alert = "Capital insuffisant" if (threshold and capital and capital < threshold) else "Alerte BODACC"
            L.append(
                f"| {c.get('nom_complet','—')[:35]} | `{c.get('siren','—')}` "
                f"| `{naf}` | {cap_str} | {thr_str} | 🚨 {alert} |"
            )
        L += [
            "",
            "> **⚠️ Obligation légale** : Avant toute sélection sous-traitant — "
            "attestation décennale, RCD, kbis < 3 mois, régularité Urssaf (attestation de vigilance), BODACC.",
            "",
        ]

    # ====================================================================
    # AXE 2 — DATA CROSSING & CORRELATION
    # ====================================================================
    L += [
        "---",
        "",
        "## Axe 2 — Croisement de Données & Corrélations Avancées",
        "",
    ]

    # Density correlation matrix
    L += [
        "### 2.1 Matrice de Densité — Offre vs Demande",
        "",
        "| Indicateur | Valeur | Benchmark national | Interprétation |",
        "|---|---|---|---|",
        f"| Passoires thermiques / rénovateur | **{corr['passoires_per_renovateur'] or '—'}** | ~500 (équilibre) | {gap_desc} |",
        f"| Ventes maisons / rénovateur | **{corr['maisons_per_renovateur'] or '—'}** | ~10-20 | Pipeline chantiers 3-12 mois |",
        f"| Potentiel annuel / rénovateur | **{corr['potentiel_per_renovateur'] or '—'} chantiers** | — | Capacité théorique à absorber |",
        f"| Taux de saturation marché | **{corr['saturation_score'] or '—'}/100** | 50 = équilibre | <30 = sous-couvert |",
        "",
    ]

    # DPE vs company density
    L += [
        "### 2.2 Corrélation DPE × Densité d'Acteurs",
        "",
        f"- **{corr['passoires']:,}** passoires thermiques (E/F/G) identifiées sur {dpe_total:,} logements diagnostiqués".replace(",", " "),
        f"- **{passoires_pct}%** du parc = cible directe pour rénovation énergétique globale (ITE, VMC, PAC, menuiseries)",
        f"- Seulement **{corr['renovateurs']}** rénovateurs/contractants actifs sur le périmètre",
    ]
    if corr["passoires_per_renovateur"] and corr["passoires_per_renovateur"] > 500:
        L.append(
            f"- **Conclusion** : Ratio de {int(corr['passoires_per_renovateur'])} passoires par acteur = "
            f"marché structurellement sous-servi. Chaque rénovateur ne peut traiter qu'une fraction de la demande."
        )
    L.append("")

    # DVF correlation
    dvf_ind = dvf_stats.get("indicateur_renovation", "FAIBLE")
    L += [
        "### 2.3 Corrélation DVF × Pipeline Chantiers",
        "",
        f"- **{corr['maisons']}** ventes de maisons sur 6 mois = pipeline direct de rénovations post-achat",
        f"- **{corr['total_companies'] and corr['maisons_per_renovateur'] or '—'}** ventes maison par rénovateur disponible",
        f"- Indicateur demande : **{dvf_ind}**",
    ]
    if dvf_ind == "FORT":
        L.append(
            "- **Signal fort** : Volume de transactions immobilières élevé. "
            "Les acquéreurs de maisons anciennes déclenchent statistiquement des travaux dans les 6-18 mois post-achat."
        )
    L.append("")

    # Legal risk vs NAF cross
    high_risk_reno = sum(
        1 for c in companies
        if c.get("naf_code") in ("43.39Z", "41.20A")
        and _legal_risk_label(c.get("nature_juridique"))[0] == "ÉLEVÉ"
    )
    startup_count = segments["by_maturity"].get("Startup (<3 ans)", 0)
    L += [
        "### 2.4 Risque Systémique — Croisement Juridique × Maturité",
        "",
        f"- **{high_risk_reno}** rénovateurs/contractants à structure juridique risquée (EI, SNC)",
        f"- **{corr['startup_renovateurs']}** rénovateurs de moins de 3 ans (risque de défaillance élevé)",
        f"- **{startup_count}** startups tous secteurs confondus",
    ]
    if high_risk_reno > corr["renovateurs"] * 0.2:
        L.append(
            "- **⚠️ Alerte concentration** : Part élevée d'acteurs à risque structurel dans le secteur rénovation "
            "→ fragilité de la chaîne de sous-traitance locale."
        )
    L.append("")

    # INSEE market sizing
    if insee_profiles:
        total_pop = sum(p.get("population", 0) for p in insee_profiles)
        total_menages = corr["total_menages"]
        total_pot = corr["total_potentiel"]
        L += [
            "### 2.5 Sizing INSEE — Taille Réelle du Marché Adressable",
            "",
            f"| Métrique | Valeur | Base de calcul |",
            f"|---|---|---|",
            f"| Population totale | **{total_pop:,}** hab. | Données INSEE / geo.api.gouv.fr |".replace(",", " "),
            f"| Ménages estimés | **{total_menages:,}** | Population ÷ 2,2 (taille moy. ménage France) |".replace(",", " "),
            f"| Potentiel rénovation/an | **{total_pot:,} chantiers** | 1,2% du parc ménages (taux historique post-mutation) |".replace(",", " "),
            f"| Panier moyen estimé rénovation | ~35 000 € | Rénovation partielle maison (isolation + menuiseries) |",
            f"| **Marché adressable annuel** | **~{int(total_pot * 35_000 / 1_000_000)} M€** | Potentiel × panier moyen |",
            "",
        ]

    # ====================================================================
    # AXE 3 — ACTIONABLE BUSINESS INSIGHTS
    # ====================================================================
    L += [
        "---",
        "",
        "## Axe 3 — Insights Business Actionnables",
        "",
    ]

    # Opportunity score breakdown
    dpe_pts = min(40, int(passoires_pct * 0.8))
    dvf_pts = min(30, int(corr["maisons"] / 5))
    gap_pts = min(30, int((corr.get("passoires_per_renovateur") or 0) / 100))

    L += [
        "### 3.1 Score d'Opportunité de Marché",
        "",
        "```",
        f"Score global : {opp_score}/100  [{gap_level}]",
        f"├─ Potentiel DPE     : {dpe_pts}/40  ({passoires_pct}% de passoires)",
        f"├─ Activité DVF      : {dvf_pts}/30  ({corr['maisons']} ventes maisons/6 mois)",
        f"└─ Gap offre/demande : {gap_pts}/30  ({int(corr.get('passoires_per_renovateur') or 0)} passoires/rénovateur)",
        "```",
        "",
    ]

    # Market gap insights
    L += ["### 3.2 Opportunités de Marché Identifiées", ""]

    insights: list[str] = []

    if gap_level in ("CRITIQUE", "FORT"):
        insights.append(
            f"**Gap contractants généraux** : {corr['passoires_per_renovateur']:.0f} passoires par rénovateur actif "
            f"= fenêtre de positionnement immédiate sur la rénovation énergétique globale (MaPrimeRénov, CEE)."
        )

    if corr["fragile_pct"] > 20:
        insights.append(
            f"**Consolidation de marché** : {corr['fragile_pct']}% des acteurs présentent des fragilités structurelles "
            "→ opportunité de rachat de portefeuille client ou de récupération de chantiers abandonnés."
        )

    if corr["startup_renovateurs"] > 2:
        insights.append(
            f"**Sous-traitance qualifiée** : {corr['startup_renovateurs']} rénovateurs récents (<3 ans) "
            "sans réseau établi = profils à recruter comme sous-traitants avec encadrement qualité."
        )

    if corr["architectes"] > 0:
        insights.append(
            f"**Réseau prescripteurs** : {corr['architectes']} cabinets d'architecture identifiés "
            "= levier de prescription directe pour les marchés rénovation haut de gamme et ERP."
        )

    if dvf_ind == "FORT":
        insights.append(
            "**Prospection post-achat** : Volume DVF élevé = cibler les acheteurs de maisons anciennes "
            "via partenariats agences immobilières / notaires (6-18 mois post-achat = peak travaux)."
        )

    for i, insight in enumerate(insights, 1):
        L.append(f"- **Opportunité {i}** : {insight}")
    L.append("")

    # Prospecting zones
    if prospecting_zones:
        L += [
            "### 3.3 Zones de Prospection Prioritaires (INSEE × DVF)",
            "",
            "| Commune | Dép. | Population | Ménages | Chantiers/an est. | Priorité |",
            "|---|---|---|---|---|---|",
        ]
        for i, z in enumerate(prospecting_zones):
            priority = "🔴 P1" if i < 2 else "🟡 P2" if i < 5 else "🟢 P3"
            L.append(
                f"| {z['commune']} | {z['departement']} | "
                f"{z['population']:,} | {z['menages']:,} | ~{z['potentiel_annuel']} | {priority} |".replace(",", " ")
            )
        L.append("")

    # SIRENE script
    L += [
        "### 3.4 Script de Collecte Ciblée (SIRENE)",
        "",
        "```python",
        "import httpx",
        "",
        "TARGETS = [",
        *[f'    ("{naf}", "{dept}"),' for naf in naf_codes for dept in departements],
        "]",
        "",
        "def search_market(naf_code: str, departement: str, per_page: int = 25):",
        '    url = "https://recherche-entreprises.api.gouv.fr/search"',
        '    r = httpx.get(url, params={"activite_principale": naf_code,',
        '                               "departement": departement,',
        '                               "etat_administratif": "A",',
        '                               "per_page": per_page})',
        "    return r.json().get('results', [])",
        "",
        "results = {(naf, dept): search_market(naf, dept) for naf, dept in TARGETS}",
        "print(f'Total acteurs : {sum(len(v) for v in results.values())}')",
        "```",
        "",
        "### 3.5 Checklist Sélection Sous-traitant",
        "",
        "- [ ] Kbis < 3 mois — Infogreffe",
        "- [ ] Attestation décennale valide (RC + RCD) — vérifier dates et plafonds",
        "- [ ] Absence procédure collective — BODACC (bodacc.fr)",
        "- [ ] Régularité Urssaf — attestation de vigilance (urssaf.fr)",
        "- [ ] Capital social adapté au volume du chantier (cf. seuils NAF)",
        "- [ ] Références chantiers similaires documentées (> 2 ans d'expérience secteur)",
        "- [ ] Assurance multirisque professionnelle à jour",
        "",
        "---",
        "",
        f"*Sources : SIRENE (DINUM) · ADEME DPE · DVF Etalab · INSEE / geo.api.gouv.fr*",
    ]

    return "\n".join(L)
