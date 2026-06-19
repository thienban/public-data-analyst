import httpx
import uuid
from typing import Any
from backend.config import settings
from backend.models.company import Company, FRAGILITY_THRESHOLDS


BASE_URL = settings.sirene_base_url


def _parse_company(hit: dict[str, Any]) -> Company:
    matching = hit.get("matching_etablissements", [{}])
    etab = matching[0] if matching else {}

    siren = hit.get("siren", "")
    naf_code = hit.get("activite_principale", "")
    capital = hit.get("capital_social")

    # Compute fragility score
    fragility = 0
    threshold = FRAGILITY_THRESHOLDS.get(naf_code, 0)
    if threshold and capital is not None and capital < threshold:
        fragility += 2
    if capital is not None and capital < 1000:
        fragility += 3

    return Company(
        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, siren)),
        siren=siren,
        nom_complet=hit.get("nom_complet"),
        naf_code=naf_code,
        naf_libelle=hit.get("libelle_activite_principale"),
        date_creation=hit.get("date_creation"),
        tranche_effectif=hit.get("tranche_effectif_salarie"),
        nature_juridique=hit.get("nature_juridique"),
        capital_social=capital,
        departement=etab.get("departement"),
        ville=etab.get("libelle_commune"),
        etat_administratif=hit.get("etat_administratif", "A"),
        fragility_score=fragility,
    )


async def search_companies(
    naf_code: str,
    departement: str,
    page: int = 1,
    per_page: int = 25,
) -> list[Company]:
    params = {
        "activite_principale": naf_code,
        "departement": departement,
        "etat_administratif": "A",
        "page": page,
        "per_page": per_page,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    return [_parse_company(r) for r in results]


async def get_company_detail(siren: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/search", params={"q": siren})
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return {}
    return results[0]
