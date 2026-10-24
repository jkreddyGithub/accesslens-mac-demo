"""Local, read-only MCP server providing synthetic AccessLens demo context."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AccessLens synthetic identity and risk data")


@mcp.tool()
def get_identity_context(user_id: str) -> dict[str, str]:
    """Return synthetic identity metadata for the demo reviewer."""
    if user_id != "contractor_jane":
        raise ValueError(f"No synthetic identity record for {user_id!r}.")

    return {
        "user_id": user_id,
        "account_status": "dormant",
        "last_active": "More than 90 days ago",
        "privilege": "administrator",
        "manager": "security-lead@example.test",
    }


@mcp.tool()
def score_access_risk(user_id: str) -> dict[str, object]:
    """Return a deterministic synthetic risk score and its factors."""
    if user_id != "contractor_jane":
        raise ValueError(f"No synthetic risk record for {user_id!r}.")

    return {
        "risk_score": 88,
        "flags": [
            "Dormant account (>90 days inactive)",
            "Excessive admin privilege",
        ],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
