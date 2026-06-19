"""
Rule-based strategic analysis engine.
Replaces the Claude AI agent — no LLM API required.
Produces the same 3-axis Markdown report from raw API data.
"""

from __future__ import annotations
import json
from datetime import datetime
from backend.models.company import FRAGILITY_THRESHOLDS, NAF_LABELS


EFFECTIF_LABELS: dict[str, str] = {
    "00": "0 salarié",
    "01": "1-2",
    "02": "3-5",
    "03": "6-9",
    "11": "10-19",
    "12": "20-49",
    "21": "50-99",
    "22": "100-199",
    "NN": "—",
}

MATURITY_BUCKETS = {
    "Startup (<3 ans)": 0,
    "Croissance (3-7 ans)": 0,
    "Etablie (7-15 ans)": 0,
    "Senior (15+ ans)": 0,
}


def _maturity(date_creation: str | None) -> str:
    if not date_creation:
        return "Inconnue"
    try:
        year = int(date_creation[:4])
        age = datetime.now().year - year
        if age < 3:
            return "Startup (<3 ans)"
        if age < 7:
            return "Croissance (3-7 ans)"
        if age < 15:
            return "Etablie (7-15 ans)"
        return "Senior (15+ ans)"
    except ValueError:
        return "Inconnue"


def _fragility(company: dict) -> bool:
    naf = company.get("naf_code", "")
    capital = company.get("capital_social")
    threshold = FRAGILITY_THRESHOLDS.get(naf, 0)
    if threshold and capital is not None and capital < threshold:
        return True
    if company.get("bodacc_alerts", 0) > 0:
        return True
    return False


def _renovation_indicator(maisons: int) -> str:
    if maisons > 50:
        return "FORT"
    if maisons > 20:
        return "MODERE"
    return "FAIBLE"


def generate_report(
    companies: list[dict],
    dpe_stats: dict,
    dvf_stats: dict,
    query: str,
    departements: list[str],
    naf_codes: list[str],
    insee_profiles: list[dict] | None = None,
) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    dept_str = " · ".join(departements)
    naf_str = " · ".join(naf_codes)

    # --- Compute aggregates ---
    total = len(companies)
    fragile = [c for c in companies if _fragility(c)]
    fragile_count = len(fragile)

    maturity_count: dict[str, int] = {k: 0 for k in MATURITY_BUCKETS}
    for c in companies:
        bucket = _maturity(c.get("date_creation"))
        if bucket in maturity_count:
            maturity_count[bucket] += 1

    naf_breakdown: dict[str, int] = {}
    for c in companies:
        naf = c.get("naf_code") or "—"
        naf_breakdown[naf] = naf_breakdown.get(naf, 0) + 1

    nature_breakdown: dict[str, int] = {}
    for c in companies:
        nature = c.get("nature_juridique") or "Autre"
        nature_breakdown[nature] = nature_breakdown.get(nature, 0) + 1

    # Top fragile companies
    top_fragile = sorted(fragile, key=lambda c: (c.get("capital_social") or 999_999))[:5]

    # DPE
    passoires_pct = dpe_stats.get("passoires_pct", 0)
    passoires_count = dpe_stats.get("passoires_count", 0)
    dpe_total = dpe_stats.get("total", 0)

    # DVF
    total_transactions = dvf_stats.get("total_transactions", 0)
    maisons = dvf_stats.get("maisons", 0)
    indicateur = _renovation_indicator(maisons)

    # INSEE
    insee_profiles = insee_profiles or []
    total_population = sum(p.get("population") or 0 for p in insee_profiles)
    total_menages = sum(p.get("menages_estimes") or 0 for p in insee_profiles)
    total_potentiel = sum(p.get("potentiel_renovation_annuel") or 0 for p in insee_profiles)

    # Opportunity score (0-100)
    opportunity_score = min(
        100,
        int(
            (passoires_pct * 0.4)
            + (min(maisons, 100) * 0.3)
            + (max(0, 25 - fragile_count) * 0.3 * (total / max(total, 1)))
        ),
    )

    # --- Build Markdown report ---
    lines: list[str] = []

    lines += [
        f"# Rapport d'Analyse Stratégique — {dept_str}",
        f"",
        f"**Généré le {now}** · NAF analysés : `{naf_str}` · Départements : `{dept_str}`",
        f"",
        "---",
        "",
    ]

    # --- AXE 1 : Audit Concurrence ---
    lines += [
        "## Axe 1 — Audit Concurrence & Sourcing",
        "",
        f"**{total}** entreprises actives identifiées sur les codes NAF sélectionnés.",
        "",
        "### Répartition par Code NAF",
        "",
        "| Code NAF | Libellé | Nb entreprises | % |",
        "|---|---|---|---|",
    ]
    for naf, count in sorted(naf_breakdown.items(), key=lambda x: -x[1]):
        label = NAF_LABELS.get(naf, naf)
        pct = round(count / total * 100, 1) if total else 0
        lines.append(f"| `{naf}` | {label} | **{count}** | {pct}% |")

    lines += [
        "",
        "### Maturité des acteurs",
        "",
        "| Segment | Nb | Signal |",
        "|---|---|---|",
    ]
    signals = {
        "Startup (<3 ans)": "Risque élevé — vérifier décennale + Kbis",
        "Croissance (3-7 ans)": "En développement — surveiller trésorerie",
        "Etablie (7-15 ans)": "Acteur fiable — backbone du marché",
        "Senior (15+ ans)": "Expérimenté — potentiel partenariat stratégique",
    }
    for bucket, count in maturity_count.items():
        if count > 0:
            lines.append(f"| {bucket} | {count} | {signals[bucket]} |")

    lines += [""]

    if fragile_count > 0:
        lines += [
            f"### 🚨 Alertes de Fragilité Structurelle ({fragile_count} entreprises)",
            "",
            "| Entreprise | SIREN | NAF | Capital | Problème |",
            "|---|---|---|---|---|",
        ]
        for c in top_fragile:
            naf = c.get("naf_code", "—")
            capital = c.get("capital_social")
            threshold = FRAGILITY_THRESHOLDS.get(naf, 0)
            capital_str = f"{capital:,} €".replace(",", " ") if capital is not None else "—"
            problem = (
                f"Capital < {threshold:,} € seuil {naf}".replace(",", " ")
                if threshold and capital is not None and capital < threshold
                else "Alerte BODACC"
            )
            lines.append(
                f"| {c.get('nom_complet', '—')} | `{c.get('siren', '—')}` "
                f"| `{naf}` | {capital_str} | ⚠️ {problem} |"
            )
        lines += [
            "",
            "> ⚠️ **Rappel obligatoire** : Avant toute sélection comme sous-traitant, "
            "vérifier l'attestation décennale valide, le kbis < 3 mois, la régularité Urssaf "
            "et l'absence de procédure collective sur BODACC.",
            "",
        ]

    # --- INSEE Market Profile ---
    if insee_profiles:
        lines += [
            "## Données INSEE — Profil de Marché",
            "",
            f"Population totale couverte : **{total_population:,}** habitants · "
            f"**{total_menages:,}** ménages estimés".replace(",", " "),
            f"Potentiel rénovation annuel estimé : **{total_potentiel:,}** chantiers/an (1,2% du parc)".replace(",", " "),
            "",
            "### Communes prioritaires (top population par département)",
            "",
        ]
        for profile in insee_profiles:
            dept_code = profile.get("departement", "")
            dept_nom = profile.get("nom", f"Dép. {dept_code}")
            communes = profile.get("top_communes", [])
            if communes:
                lines += [
                    f"**{dept_nom} ({dept_code})**",
                    "",
                    "| Commune | Code INSEE | Population | Ménages est. | Zone cible |",
                    "|---|---|---|---|---|",
                ]
                for i, c in enumerate(communes[:6]):
                    pop = c.get("population") or 0
                    menages = c.get("menages_estimes") or 0
                    priority = "🔴 Priorité 1" if i < 2 else "🟡 Priorité 2" if i < 4 else "🟢 Secondaire"
                    lines.append(
                        f"| {c['nom']} | `{c['code_insee']}` | "
                        f"{pop:,} | {menages:,} | {priority} |".replace(",", " ")
                    )
                lines.append("")
        lines.append("")

    # --- AXE 2 : Segmentation Stratégique ---
    lines += [
        "## Axe 2 — Segmentation Stratégique & Croisement Data",
        "",
        "### Données DPE (Passoires Thermiques)",
        "",
        f"- **{passoires_count:,}** logements classés E/F/G sur {dpe_total:,} diagnostiqués".replace(",", " "),
        f"- **{passoires_pct}%** du parc = passoires thermiques",
    ]

    if passoires_pct > 30:
        lines.append(
            "- **Signal fort** : Part de passoires élevée = fort potentiel de rénovation énergétique globale (ITE, VMC, pompes à chaleur)"
        )
    elif passoires_pct > 15:
        lines.append(
            "- **Signal modéré** : Potentiel de rénovation ciblée (isolation combles, chaudière gaz → PAC)"
        )
    else:
        lines.append("- Signal faible : Parc relativement récent ou déjà rénové")

    lines += [
        "",
        "### Données DVF (Marché Immobilier)",
        "",
        f"- **{total_transactions}** transactions immobilières sur les 6 derniers mois",
        f"- **{maisons}** ventes de maisons (indicateur rénovation direct)",
        f"- Indicateur demande rénovation : **{indicateur}**",
    ]

    if indicateur == "FORT":
        lines.append(
            "- **Opportunité immédiate** : Volume de ventes maisons élevé = pipeline de chantiers rénovation à 3-12 mois"
        )
    elif indicateur == "MODERE":
        lines.append(
            "- **Opportunité en développement** : Activité immobilière soutenue — prospection active recommandée"
        )

    # Cross-analysis
    lines += [
        "",
        "### Analyse Croisée",
        "",
    ]

    contractants = naf_breakdown.get("41.20A", 0)
    renovateurs = naf_breakdown.get("43.39Z", 0)

    if passoires_count > 1000 and (contractants + renovateurs) < 20:
        lines.append(
            f"- **Déficit critique** : {passoires_count:,} passoires thermiques identifiées mais seulement "
            f"{contractants + renovateurs} contractants/rénovateurs actifs → **gap de marché majeur**".replace(",", " ")
        )
    elif passoires_count > 500 and (contractants + renovateurs) < 50:
        lines.append(
            f"- **Sous-couverture du marché** : Ratio passoires/acteurs défavorable — "
            f"opportunité de positionnement sur la rénovation énergétique globale"
        )

    lines += [""]

    # --- AXE 3 : Recommandations ---
    lines += [
        "## Axe 3 — Recommandations Business & Data",
        "",
        "### Opportunités de marché identifiées",
        "",
    ]

    if indicateur == "FORT" and passoires_pct > 20:
        lines.append(
            "- **Priorité 1** : Cibler les propriétaires de maisons achetées ces 6 derniers mois "
            "(croisement DVF × DPE) — probabilité de chantier rénovation > 60%"
        )

    if fragile_count > total * 0.2:
        lines.append(
            f"- **Priorité 2** : {fragile_count}/{total} concurrents présentent des fragilités structurelles "
            "→ **parts de marché à saisir** dans les 12-18 mois"
        )

    startup_count = maturity_count.get("Startup (<3 ans)", 0)
    if startup_count > 3:
        lines.append(
            f"- **Opportunité partenariat** : {startup_count} startups identifiées "
            "— potentiel de sous-traitance ou acquisition de portefeuille client"
        )

    lines += [
        "",
        "### Score d'opportunité de marché",
        "",
        f"```",
        f"Score global : {opportunity_score}/100",
        f"├─ Potentiel DPE    : {min(100, int(passoires_pct * 0.4))}/40  (passoires {passoires_pct}%)",
        f"├─ Activité DVF     : {min(30, int(min(maisons, 100) * 0.3))}/30  ({maisons} ventes maisons)",
        f"└─ Solidité marché  : {min(30, max(0, 25 - fragile_count))}/30  ({fragile_count} acteurs fragiles)",
        f"```",
        "",
        "### Script Python — Requête ciblée SIRENE",
        "",
        "```python",
        "import httpx",
        "",
        "def search_market(naf_code: str, departement: str):",
        '    url = "https://recherche-entreprises.api.gouv.fr/search"',
        "    params = {",
        '        "activite_principale": naf_code,',
        '        "departement": departement,',
        '        "etat_administratif": "A",',
        '        "per_page": 25,',
        "    }",
        "    r = httpx.get(url, params=params)",
        "    return r.json().get('results', [])",
        "",
        f"# Axe Antony / Massy / Palaiseau",
        f"acteurs = search_market('43.39Z', '91')",
        f"print(f'{{len(acteurs)}} rénovateurs TCE actifs en Essonne')",
        "```",
        "",
        "### Checklist Sous-traitant (règles métier)",
        "",
        "- [ ] Kbis < 3 mois — vérifier sur Infogreffe",
        "- [ ] Attestation décennale valide (RC Décennale + RCD)",
        "- [ ] Absence de procédure collective sur BODACC",
        "- [ ] Régularité Urssaf (attestation de vigilance)",
        "- [ ] Capital social adapté au volume de chantier",
        "- [ ] Références chantiers similaires (> 2 ans d'antériorité)",
        "",
        "---",
        "",
        f"*Rapport généré automatiquement — Sources : SIRENE (DINUM) · ADEME DPE · DVF (Etalab)*",
    ]

    return "\n".join(lines)
