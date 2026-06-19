import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.analyst import run_analysis_stream
from backend.database import get_connection

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    query: str
    departements: list[str] = ["91", "92"]
    naf_codes: list[str] = ["43.39Z", "41.20A"]


@router.post("/run")
async def run_analysis(req: AnalysisRequest):
    """
    Stream a full strategic analysis via the Claude AI agent.
    Returns Server-Sent Events (SSE) with typed chunks:
      - {type: "start"}
      - {type: "thinking", text}
      - {type: "tool_call", tool, input}
      - {type: "tool_result", tool}
      - {type: "text", text}   ← final report
      - {type: "done"}
    """
    enriched_query = (
        f"{req.query}\n\n"
        f"Départements cibles : {', '.join(req.departements)}\n"
        f"Codes NAF : {', '.join(req.naf_codes)}"
    )

    return StreamingResponse(
        run_analysis_stream(enriched_query),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/reports")
async def list_reports():
    """Return saved analysis reports (most recent first)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, query, companies_count, created_at FROM analysis_reports ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Return a full report by ID."""
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
