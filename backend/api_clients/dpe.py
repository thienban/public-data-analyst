import httpx
import uuid
from typing import Any

# ADEME DPE open data endpoint (via data.gouv.fr / ADEME API)
DPE_API_URL = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"

PASSOIRE_CLASSES = {"E", "F", "G"}


def _parse_dpe(row: dict[str, Any]) -> dict:
    code_postal = row.get("Code_postal_(BAN)", "") or ""
    dept = code_postal[:2] if code_postal else ""
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, row.get("N°DPE", str(uuid.uuid4())))),
        "adresse": row.get("Adresse_(BAN)"),
        "code_postal": code_postal,
        "ville": row.get("Commune_(BAN)"),
        "departement": dept,
        "classe_energie": row.get("Etiquette_DPE"),
        "etiquette_ges": row.get("Etiquette_GES"),
        "annee_construction": row.get("Année_construction"),
        "surface_habitable": row.get("Surface_habitable_logement"),
        "date_etablissement": row.get("Date_établissement_DPE"),
    }


async def fetch_dpe_passoires(code_postal_prefix: str, max_results: int = 200) -> list[dict]:
    """
    Fetch DPE thermal sieves (classes E, F, G) for a given postal code prefix.
    """
    params = {
        "size": max_results,
        "q": code_postal_prefix,
        "q_fields": "Code_postal_(BAN)",
        "qs": "Etiquette_DPE:(E OR F OR G)",
        "select": "N°DPE,Adresse_(BAN),Code_postal_(BAN),Commune_(BAN),Etiquette_DPE,Etiquette_GES,Année_construction,Surface_habitable_logement,Date_établissement_DPE",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(DPE_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    return [_parse_dpe(r) for r in data.get("results", [])]


async def get_dpe_stats(departement: str) -> dict:
    """
    Aggregate DPE class distribution for a departement.
    Returns counts per class and % of passoires thermiques.
    """
    params = {
        "size": 0,
        "q": departement,
        "q_fields": "Code_postal_(BAN)",
        "aggs": "Etiquette_DPE",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(DPE_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    agg = data.get("aggs", {}).get("Etiquette_DPE", {}).get("buckets", [])
    total = sum(b["count"] for b in agg)
    passoires = sum(b["count"] for b in agg if b["value"] in PASSOIRE_CLASSES)

    return {
        "total": total,
        "passoires_count": passoires,
        "passoires_pct": round(passoires / total * 100, 1) if total else 0,
        "distribution": {b["value"]: b["count"] for b in agg},
    }
