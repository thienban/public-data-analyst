import httpx
import uuid
from datetime import date, timedelta

# DVF via Etalab / api.cquest.org
DVF_URL = "https://api.cquest.org/dvf"


def _parse_mutation(row: dict) -> dict:
    code_postal = str(row.get("code_postal", "") or "")
    dept = code_postal[:2]
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, str(row.get("id_mutation", uuid.uuid4())))),
        "date_mutation": row.get("date_mutation"),
        "type_local": row.get("type_local"),
        "commune": row.get("nom_commune"),
        "code_postal": code_postal,
        "departement": dept,
        "valeur_fonciere": row.get("valeur_fonciere"),
        "surface_reelle_bati": row.get("surface_reelle_bati"),
        "nombre_pieces_principales": row.get("nombre_pieces_principales"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
    }


async def fetch_recent_transactions(
    code_postal: str,
    months_back: int = 6,
    type_local: str | None = None,
) -> list[dict]:
    """
    Fetch real estate transactions for a postal code over the last N months.
    A recent sale is a strong indicator of an upcoming renovation project.
    """
    date_from = (date.today() - timedelta(days=30 * months_back)).isoformat()

    params: dict = {
        "code_postal": code_postal,
        "date_mutation_min": date_from,
    }
    if type_local:
        params["type_local"] = type_local

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(DVF_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    mutations = data.get("resultats", data.get("features", []))
    parsed = []
    for m in mutations:
        props = m.get("properties", m)
        parsed.append(_parse_mutation(props))
    return parsed


async def get_dvf_stats(departement: str, months_back: int = 6) -> dict:
    """
    Aggregate DVF transaction volume for a departement.
    High transaction volume = high renovation demand.
    """
    date_from = (date.today() - timedelta(days=30 * months_back)).isoformat()
    params = {
        "code_departement": departement,
        "date_mutation_min": date_from,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(DVF_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    mutations = data.get("resultats", data.get("features", []))
    maisons = [m for m in mutations if m.get("properties", m).get("type_local") == "Maison"]
    appartements = [m for m in mutations if m.get("properties", m).get("type_local") == "Appartement"]

    return {
        "total_transactions": len(mutations),
        "maisons": len(maisons),
        "appartements": len(appartements),
        "periode": f"{months_back} derniers mois",
        "indicateur_renovation": "FORT" if len(maisons) > 50 else "MODERE" if len(maisons) > 20 else "FAIBLE",
    }
