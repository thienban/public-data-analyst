import json
import uuid
from typing import AsyncGenerator

import anthropic

from backend.config import settings
from backend.agents.prompts import SYSTEM_PROMPT
from backend.agents.tools import TOOLS
from backend.api_clients import sirene, dpe, dvf
from backend.database import get_connection

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
MODEL = "claude-sonnet-4-6"


async def _execute_tool(name: str, inputs: dict) -> str:
    if name == "search_companies":
        companies = await sirene.search_companies(
            naf_code=inputs["naf_code"],
            departement=inputs["departement"],
            per_page=inputs.get("per_page", 25),
        )
        rows = [c.model_dump() for c in companies]
        return json.dumps(rows, ensure_ascii=False, default=str)

    if name == "get_dpe_stats":
        stats = await dpe.get_dpe_stats(inputs["departement"])
        return json.dumps(stats, ensure_ascii=False)

    if name == "get_dvf_stats":
        stats = await dvf.get_dvf_stats(
            departement=inputs["departement"],
            months_back=inputs.get("months_back", 6),
        )
        return json.dumps(stats, ensure_ascii=False)

    if name == "generate_report":
        report_id = str(uuid.uuid4())
        conn = get_connection()
        conn.execute(
            "INSERT INTO analysis_reports (id, query, query_params, report_markdown) VALUES (?, ?, ?, ?)",
            (
                report_id,
                inputs["title"],
                json.dumps(inputs.get("query_params", {})),
                inputs["content"],
            ),
        )
        conn.commit()
        conn.close()
        return json.dumps({"report_id": report_id, "status": "saved"})

    return json.dumps({"error": f"Unknown tool: {name}"})


async def run_analysis_stream(user_query: str) -> AsyncGenerator[str, None]:
    """
    Agentic ReAct loop: Claude calls tools to gather data, then synthesizes analysis.
    Yields SSE-formatted chunks for streaming to the frontend.
    """
    messages: list[dict] = [{"role": "user", "content": user_query}]

    yield f"data: {json.dumps({'type': 'start', 'message': 'Démarrage de l\\'analyse...'})}\n\n"

    while True:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,  # type: ignore[arg-type]
            messages=messages,
        )

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Final text response — stream it
            for block in response.content:
                if hasattr(block, "text"):
                    yield f"data: {json.dumps({'type': 'text', 'text': block.text})}\n\n"
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    if hasattr(block, "text"):
                        yield f"data: {json.dumps({'type': 'thinking', 'text': block.text})}\n\n"
                    continue

                yield f"data: {json.dumps({'type': 'tool_call', 'tool': block.name, 'input': block.input})}\n\n"

                result = await _execute_tool(block.name, block.input)

                yield f"data: {json.dumps({'type': 'tool_result', 'tool': block.name})}\n\n"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason
        break

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
