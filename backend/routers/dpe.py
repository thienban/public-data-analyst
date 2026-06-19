from fastapi import APIRouter, Query
from backend.api_clients.dpe import fetch_dpe_passoires, get_dpe_stats

router = APIRouter(prefix="/api/dpe", tags=["dpe"])


@router.get("/stats/{departement}")
async def dpe_stats(departement: str):
    """DPE class distribution and thermal sieve count for a department."""
    return await get_dpe_stats(departement)


@router.get("/passoires")
async def dpe_passoires(
    code_postal: str = Query(..., description="Code postal ou préfixe (ex: 91300, 92)"),
    max_results: int = Query(default=100, le=500),
):
    """List thermal sieve buildings (DPE E/F/G) for a postal code."""
    records = await fetch_dpe_passoires(code_postal, max_results)
    return {
        "total": len(records),
        "code_postal": code_postal,
        "records": records,
    }
