from fastapi import APIRouter, Query
from backend.api_clients.insee import (
    get_departement_market_profile,
    get_departement_info,
    get_top_communes_by_population,
)

router = APIRouter(prefix="/api/insee", tags=["insee"])


@router.get("/profile/{departement}")
async def market_profile(departement: str):
    """
    Full INSEE market profile for a department:
    population, estimated households, renovation potential, top communes.
    """
    return await get_departement_market_profile(departement)


@router.get("/departement/{departement}")
async def departement_info(departement: str):
    """Basic department metadata from INSEE / geo.api.gouv.fr."""
    return await get_departement_info(departement)


@router.get("/communes")
async def top_communes(
    departement: str = Query(...),
    top_n: int = Query(default=10, le=50),
):
    """Top N communes by population in a department (prospecting zones)."""
    communes = await get_top_communes_by_population(departement, top_n)
    return {"departement": departement, "total": len(communes), "communes": communes}
