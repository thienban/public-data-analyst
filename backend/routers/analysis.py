import json
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.config import settings
from backend.database import get_connection
from backend.api_clients import sirene, dpe, dvf
from backend.agents.rule_engine import generate_report

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

USE_CLAUDE = bool(settings.anthropic_api_key)


class AnalysisRequest(BaseModel):
    query: str
    departements: list[str] = ["91", "92"]
    naf_codes: list[str] = ["43.39Z", "41.20A"]


async def _rule_based_stream(req: AnalysisRequest):
    """
    Rule-based analysis — no LLM required.
    Collects data from French public APIs, then generates a Markdown report.
    Emits the same SSE event format as the Claude agent stream.
    """

    def evt(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    yield evt({"type": "start", "message": "Collecte des données en cours..."})

    # Collect companies across all NAF × dept combinations
    all_companies: list[dict] = []
    for naf in req.naf_codes:
        for dept in req.departements:
            yield evt({"type": "tool_call", "tool": "search_companies", "input": {"naf_code": naf, "departement": dept}})
            companies = await sirene.search_companies(naf_code=naf, departement=dept)
            all_companies.extend([c.model_dump() for c in companies])
            yield evt({"type": "tool_result", "tool": "search_companies"})

    # Aggregate DPE stats across departments
    dpe_agg: dict = {"total": 0, "passoires_count": 0, "passoires_pct": 0.0, "distribution": {}}
    for dept in req.departements:
        yield evt({"type": "tool_call", "tool": "get_dpe_stats", "input": {"departement": dept}})
        try:
            stats = await dpe.get_dpe_stats(dept)
            dpe_agg["total"] += stats.get("total", 0)
            dpe_agg["passoires_count"] += stats.get("passoires_count", 0)
            for cls, cnt in stats.get("distribution", {}).items():
                dpe_agg["distribution"][cls] = dpe_agg["distribution"].get(cls, 0) + cnt
        except Exception:
            pass
        yield evt({"type": "tool_result", "tool": "get_dpe_stats"})

    total = dpe_agg["total"]
    if total:
        dpe_agg["passoires_pct"] = round(dpe_agg["passoires_count"] / total * 100, 1)

    # Aggregate DVF stats
    dvf_agg: dict = {"total_transactions": 0, "maisons": 0, "appartements": 0, "indicateur_renovation": "FAIBLE"}
    for dept in req.departements:
        yield evt({"type": "tool_call", "tool": "get_dvf_stats", "input": {"departement": dept}})
        try:
            stats = await dvf.get_dvf_stats(departement=dept)
            dvf_agg["total_transactions"] += stats.get("total_transactions", 0)
            dvf_agg["maisons"] += stats.get("maisons", 0)
            dvf_agg["appartements"] += stats.get("appartements", 0)
        except Exception:
            pass
        yield evt({"type": "tool_result", "tool": "get_dvf_stats"})

    yield evt({"type": "thinking", "text": "Génération du rapport stratégique..."})

    report_md = generate_report(
        companies=all_companies,
        dpe_stats=dpe_agg,
        dvf_stats=dvf_agg,
        query=req.query,
        departements=req.departements,
        naf_codes=req.naf_codes,
    )

    # Save to DB
    report_id = str(uuid.uuid4())
    conn = get_connection()
    conn.execute(
        "INSERT INTO analysis_reports (id, query, query_params, report_markdown, companies_count) VALUES (?, ?, ?, ?, ?)",
        (
            report_id,
            req.query,
            json.dumps({"departements": req.departements, "naf_codes": req.naf_codes}),
            report_md,
            len(all_companies),
        ),
    )
    conn.commit()
    conn.close()

    yield evt({"type": "text", "text": report_md})
    yield evt({"type": "done"})


@router.post("/run")
async def run_analysis(req: AnalysisRequest):
    """
    Stream a strategic analysis report via SSE.
    Uses rule-based engine if no ANTHROPIC_API_KEY is set,
    otherwise uses the Claude AI agent.
    """
    if USE_CLAUDE:
        from backend.agents.analyst import run_analysis_stream
        enriched = f"{req.query}\n\nDépartements : {', '.join(req.departements)}\nNAF : {', '.join(req.naf_codes)}"
        generator = run_analysis_stream(enriched)
    else:
        generator = _rule_based_stream(req)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/mode")
async def analysis_mode():
    """Returns which analysis engine is active."""
    return {"mode": "claude" if USE_CLAUDE else "rule-based", "has_api_key": USE_CLAUDE}


@router.get("/reports")
async def list_reports():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, query, companies_count, created_at FROM analysis_reports ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM analysis_reports WHERE id = ?", (report_id,)
    ).fetchone()
    conn.close()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    result = dict(row)
    if result.get("query_params"):
        result["query_params"] = json.loads(result["query_params"])
    return result
