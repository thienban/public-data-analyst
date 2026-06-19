"""
INSEE open data client — no API key required.
Sources:
  - geo.api.gouv.fr        : department metadata (INSEE codes, population)
  - data.gouv.fr / INSEE   : company creation/closure statistics by NAF + dept
  - api.insee.fr/geo       : commune lookup (no auth needed for geo endpoints)
"""

import httpx

GEO_API = "https://geo.api.gouv.fr"
DATAGOUV = "https://www.data.gouv.fr/api/1"

# INSEE publishes monthly company creation stats as open CSV on data.gouv.fr
# Dataset: "Créations d'entreprises par secteur d'activité et département"
CREATIONS_DATASET_ID = "58e53811c751df03df38f42d"


async def get_departement_info(code: str) -> dict:
    """
    Return department name, region, and population from geo.api.gouv.fr (INSEE source).
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GEO_API}/departements/{code}",
            params={"fields": "nom,code,codeRegion,population"},
        )
        if resp.status_code != 200:
            return {"code": code, "nom": f"Département {code}", "population": None}
        return resp.json()


async def get_communes(departement: str) -> list[dict]:
    """
    Return all communes in a department with INSEE code and population.
    Useful for market sizing (number of households per commune).
    """
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{GEO_API}/departements/{departement}/communes",
            params={"fields": "nom,code,population", "format": "json"},
        )
        if resp.status_code != 200:
            return []
        return resp.json()


async def get_top_communes_by_population(departement: str, top_n: int = 10) -> list[dict]:
    """
    Return the N most populated communes in a department.
    Key for targeting renovation prospecting zones.
    """
    communes = await get_communes(departement)
    sorted_communes = sorted(
        [c for c in communes if c.get("population")],
        key=lambda c: c["population"],
        reverse=True,
    )
    return sorted_communes[:top_n]


async def get_company_creation_stats(departement: str) -> dict:
    """
    Fetch company creation statistics for a department from the INSEE dataset on data.gouv.fr.
    Falls back to structured empty response on error.
    """
    # Search for the INSEE creations dataset
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{DATAGOUV}/datasets/",
            params={
                "q": f"créations entreprises département {departement} INSEE",
                "organization": "5e784a01f26357c5d3dab41c",  # INSEE org on data.gouv.fr
                "page_size": 5,
            },
        )

    if resp.status_code != 200:
        return _empty_creation_stats(departement)

    datasets = resp.json().get("data", [])
    if not datasets:
        return _empty_creation_stats(departement)

    # Return metadata about available datasets
    return {
        "departement": departement,
        "datasets_disponibles": [
            {
                "titre": ds.get("title"),
                "url": ds.get("page"),
                "derniere_mise_a_jour": ds.get("last_modified", "")[:10],
            }
            for ds in datasets[:3]
        ],
    }


async def get_departement_market_profile(departement: str) -> dict:
    """
    Compose a full market profile for a department:
    - Population total
    - Top communes (prospecting zones)
    - Estimated number of households (population / 2.2 avg household size)
    """
    info = await get_departement_info(departement)
    top_communes = await get_top_communes_by_population(departement, top_n=8)

    population = info.get("population") or 0
    estimated_households = int(population / 2.2) if population else 0

    # Renovation market sizing:
    # France avg: ~12% of housing stock changes hands every 10 years
    # → ~1.2% per year that are candidates for renovation post-achat
    potential_renovation_per_year = int(estimated_households * 0.012)

    return {
        "departement": departement,
        "nom": info.get("nom", f"Département {departement}"),
        "population": population,
        "menages_estimes": estimated_households,
        "potentiel_renovation_annuel": potential_renovation_per_year,
        "top_communes": [
            {
                "nom": c["nom"],
                "code_insee": c["code"],
                "population": c.get("population", 0),
                "menages_estimes": int(c.get("population", 0) / 2.2),
            }
            for c in top_communes
        ],
    }


def _empty_creation_stats(departement: str) -> dict:
    return {
        "departement": departement,
        "datasets_disponibles": [],
        "note": "Données INSEE de créations non disponibles pour ce département",
    }
