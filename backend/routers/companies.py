from fastapi import APIRouter, HTTPException, Query
from backend.api_clients import sirene
from backend.models.company import NAF_LABELS

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/search")
async def search_companies(
    naf_codes: list[str] = Query(default=["43.39Z"]),
    departements: list[str] = Query(default=["91", "92"]),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, le=25),
):
    """Search active companies by NAF codes and departments."""
    all_companies = []
    for naf in naf_codes:
        for dept in departements:
            companies = await sirene.search_companies(
                naf_code=naf, departement=dept, page=page, per_page=per_page
            )
            all_companies.extend(companies)

    results = [c.model_dump() for c in all_companies]

    # Enrich with computed fields
    for r in results:
        from backend.models.company import Company
        c = Company(**r)
        r["is_fragile"] = c.is_fragile
        r["maturity_label"] = c.maturity_label
        r["naf_libelle"] = r.get("naf_libelle") or NAF_LABELS.get(r.get("naf_code", ""), "")

    fragile_count = sum(1 for r in results if r["is_fragile"])

    return {
        "total": len(results),
        "fragile_count": fragile_count,
        "companies": results,
    }


@router.get("/{siren}")
async def get_company(siren: str):
    """Get detail for a single company by SIREN."""
    detail = await sirene.get_company_detail(siren)
    if not detail:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    return detail


@router.get("/naf-codes/list")
async def list_naf_codes():
    """Return available NAF codes with labels."""
    return [{"code": k, "label": v} for k, v in NAF_LABELS.items()]
