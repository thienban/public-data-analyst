from fastapi import APIRouter, Query
from backend.api_clients.dvf import fetch_recent_transactions, get_dvf_stats

router = APIRouter(prefix="/api/dvf", tags=["dvf"])


@router.get("/stats/{departement}")
async def dvf_stats(
    departement: str,
    months_back: int = Query(default=6, ge=1, le=24),
):
    """Real estate transaction volume for a department (renovation demand indicator)."""
    return await get_dvf_stats(departement, months_back)


@router.get("/transactions")
async def dvf_transactions(
    code_postal: str = Query(...),
    months_back: int = Query(default=6, ge=1, le=24),
    type_local: str | None = Query(default=None),
):
    """Recent real estate transactions for a postal code. Recent sale = upcoming renovation."""
    transactions = await fetch_recent_transactions(code_postal, months_back, type_local)
    return {
        "total": len(transactions),
        "code_postal": code_postal,
        "periode_mois": months_back,
        "transactions": transactions,
    }
