import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Define the state schema for our AccessLens MCP agent
class AccessLensState(TypedDict):
    review_item_id: str
    user_id: str
    retrieved_context: dict
    explanation: str
    human_approval_status: str

# Initialize the state graph
workflow = StateGraph(AccessLensState)

def fetch_mcp_context(state: AccessLensState):
    """
    Simulates fetching secure identity and risk telemetry via MCP servers.
    """
    print(f"\n[MCP Client] Fetching identity and risk factors for user: {state['user_id']}...")
    
    # Mocking MCP tool output (representing Server A & Server B responses)
    mcp_mock_data = {
        "risk_score": 88,
        "flags": ["Dormant account (>90 days inactive)", "Excessive admin privilege"],
        "manager": "security-lead@enterprise.com"
    }
    return {"retrieved_context": mcp_mock_data}

def generate_explanation_node(state: AccessLensState):
    """
    Synthesizes why the access item was flagged using the MCP-retrieved context.
    """
    context = state["retrieved_context"]
    explanation = (
        f"AI Explanation: This entitlement was flagged due to a risk score of {context['risk_score']}/100. "
        f"Identified risk factors: {', '.join(context['flags'])}. "
        f"Recommended action: Review activity logs with manager ({context['manager']})."
    )
    print(f"[Agent] Generated compliance explanation successfully.")
    return {"explanation": explanation, "human_approval_status": "PENDING_HUMAN_REVIEW"}

# Add nodes to the graph workflow
workflow.add_node("fetch_context", fetch_mcp_context)
workflow.add_node("generate_explanation", generate_explanation_node)

# Define control flow edges
workflow.set_entry_point("fetch_context")
workflow.add_edge("fetch_context", "generate_explanation")
workflow.add_edge("generate_explanation", END)

# Compile the graph application with a MemorySaver checkpointer for state persistence & HITL
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    print("--- AccessLens MCP Compliance Agent with HITL Initialized ---")
    
    # Configuration required for checkpointer threads
    config = {"configurable": {"thread_id": "review-session-101"}}
    
    initial_state = {
        "review_item_id": "ITEM-8842",
        "user_id": "contractor_jane",
        "retrieved_context": {},
        "explanation": "",
        "human_approval_status": ""
    }
    
    # 1. Run the graph workflow until it pauses at the checkpoint
    result = app.invoke(initial_state, config=config)
    print("\n--- Paused at Checkpoint for Human Review ---")
    for key, value in result.items():
        print(f"  - {key}: {value}")
        
    # 2. Simulate Human Reviewer Decision (e.g., Compliance Manager clicks 'REVOKE')
    print("\n--- Human Reviewer Action: REVOKE Access ---")
    human_decision_update = {"human_approval_status": "REVOKED_BY_REVIEWER"}
    
    # Update the graph state with the human decision using the same thread config
    app.update_state(config, human_decision_update)
    
    # Resume / fetch the final state after human intervention
    final_state = app.get_state(config)
    print("\n--- Final Post-Review State ---")
    for key, value in final_state.values.items():
        print(f"  - {key}: {value}")