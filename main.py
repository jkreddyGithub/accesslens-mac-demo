import asyncio
import json
import os
import sys
from pathlib import Path
from typing import TypedDict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt


class AccessLensState(TypedDict):
    review_item_id: str
    user_id: str
    retrieved_context: dict
    explanation: str
    human_approval_status: str


workflow = StateGraph(AccessLensState)


def _mcp_server_python() -> str:
    """Prefer the project environment so the MCP server uses pinned dependencies."""
    project_dir = Path(__file__).resolve().parent
    if os.name == "nt":
        venv_python = project_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = project_dir / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return str(venv_python)
    return sys.executable


def _decode_tool_result(result: object) -> dict[str, object]:
    if getattr(result, "isError", False):
        raise RuntimeError(f"MCP tool returned an error: {result}")

    structured_content = getattr(result, "structuredContent", None)
    if isinstance(structured_content, dict):
        return structured_content

    for content in getattr(result, "content", []):
        text = getattr(content, "text", None)
        if text:
            decoded = json.loads(text)
            if isinstance(decoded, dict):
                return decoded
    raise RuntimeError("MCP tool returned no structured object.")


async def _fetch_mcp_context(user_id: str) -> dict[str, object]:
    server = StdioServerParameters(
        command=_mcp_server_python(),
        args=[str(Path(__file__).with_name("mcp_server.py"))],
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("[MCP] Connected to the local synthetic-data MCP server.")
            print("[MCP] Calling get_identity_context...")
            identity = _decode_tool_result(
                await session.call_tool("get_identity_context", {"user_id": user_id})
            )
            print("[MCP] Calling score_access_risk...")
            risk = _decode_tool_result(
                await session.call_tool("score_access_risk", {"user_id": user_id})
            )
    return {**identity, **risk}


def fetch_mcp_context(state: AccessLensState) -> dict[str, object]:
    """Fetch identity metadata and risk factors using the MCP protocol."""
    context = asyncio.run(_fetch_mcp_context(state["user_id"]))
    return {"retrieved_context": context}


def _generate_explanation(context: dict[str, object]) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    risk_score = context["risk_score"]
    flags = context["flags"]
    request = Request(
        f"{base_url}/api/chat",
        data=json.dumps(
            {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Write one concise compliance explanation about the "
                            "existing entitlement. State its exact risk score and "
                            "every risk flag. End by stating that a human reviewer "
                            "must choose APPROVE or REVOKE. Do not claim that any "
                            "decision has already been made. Use only supplied facts."
                        ),
                    },
                    {"role": "user", "content": json.dumps(context, indent=2)},
                ],
                "stream": False,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            payload = json.loads(response.read())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Ollama returned HTTP {exc.code} for model {model!r}: {detail}"
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {base_url}. Start Ollama and ensure "
            f"model {model!r} is available. Original error: {exc}"
        ) from exc

    explanation = payload.get("message", {}).get("content", "").strip()
    if not explanation:
        raise RuntimeError(f"Ollama returned an empty response for {model!r}.")
    normalized = explanation.casefold()
    required = [str(risk_score), *(str(flag).casefold() for flag in flags)]
    if any(value.casefold() not in normalized for value in required):
        raise RuntimeError(
            f"Ollama response from {model!r} omitted a required risk fact: "
            f"{explanation}"
        )
    if any(
        term in normalized
        for term in (
            "access request",
            "policy",
            "recommend",
            "automatically revoke",
            "will revoke",
            "has been revoked",
            "has been approved",
        )
    ):
        raise RuntimeError(
            f"Ollama response from {model!r} added unsupported claims: "
            f"{explanation}"
        )
    if (
        "human reviewer" not in normalized
        or "approv" not in normalized
        or "revok" not in normalized
    ):
        raise RuntimeError(
            f"Ollama response from {model!r} did not preserve the human-review "
            f"requirement: {explanation}"
        )
    return explanation


def generate_explanation_node(state: AccessLensState) -> dict[str, str]:
    """Generate a reviewer explanation with the configured Ollama model."""
    context = state["retrieved_context"]
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    print(f"[AI] Generating explanation with Ollama model {model!r}...")
    explanation = _generate_explanation(context)
    print(f"[AI] Explanation generated by {model}.")
    return {
        "explanation": explanation,
        "human_approval_status": "PENDING_HUMAN_REVIEW",
    }


def wait_for_human_review(state: AccessLensState):
    """Pause the workflow until a reviewer explicitly chooses an outcome."""
    decision = interrupt(
        {
            "review_item_id": state["review_item_id"],
            "status": state["human_approval_status"],
            "allowed_decisions": ["APPROVE", "REVOKE"],
        }
    )
    decision = decision.strip().upper()
    if decision not in {"APPROVE", "REVOKE"}:
        raise ValueError("Reviewer decision must be APPROVE or REVOKE.")
    return {"human_approval_status": f"{decision}D_BY_REVIEWER"}


workflow.add_node("fetch_context", fetch_mcp_context)
workflow.add_node("generate_explanation", generate_explanation_node)
workflow.add_node("human_review", wait_for_human_review)

workflow.set_entry_point("fetch_context")
workflow.add_edge("fetch_context", "generate_explanation")
workflow.add_edge("generate_explanation", "human_review")
workflow.add_edge("human_review", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)


if __name__ == "__main__":
    print("--- AccessLens Compliance Review Demo with HITL Initialized ---")
    print(
        "Using synthetic local MCP data. This workflow does not change real access."
    )
    config = {"configurable": {"thread_id": "review-session-101"}}
    initial_state = {
        "review_item_id": "ITEM-8842",
        "user_id": "contractor_jane",
        "retrieved_context": {},
        "explanation": "",
        "human_approval_status": "",
    }

    app.invoke(initial_state, config=config)
    pending_state = app.get_state(config)
    print("\n--- Paused at Checkpoint for Human Review ---")
    for key, value in pending_state.values.items():
        print(f"  - {key}: {value}")

    while True:
        decision = input("Reviewer decision (APPROVE/REVOKE): ").strip().upper()
        if decision in {"APPROVE", "REVOKE"}:
            break
        print("Please enter APPROVE or REVOKE.")

    print(f"\n--- Human Reviewer Action: {decision} Access ---")
    app.invoke(Command(resume=decision), config=config)
    final_state = app.get_state(config)
    print("\n--- Final Post-Review State ---")
    for key, value in final_state.values.items():
        print(f"  - {key}: {value}")