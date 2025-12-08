from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.agents import scout_agent, budget_agent, planner_agent, human_review_node

# --- ROUTER LOGIC ---
def decide_next_step(state: AgentState):
    status = state["plan_status"]
    retry_count = state.get("retry_count", 0)

    if status == "REJECTED":
        # CHANGE: If retries > 2, ask Human instead of quitting
        if retry_count > 2:
            return "human"
        
        print(f"   [GRAPH] Plan rejected. Retrying... (Attempt {retry_count+1})")
        return "retry"

    elif status == "BUDGET_APPROVED":
        return "planner"

    elif status == "APPROVED":
        return "done"

    return "failed"

# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("scout", scout_agent)
workflow.add_node("budget", budget_agent)
workflow.add_node("planner", planner_agent)
workflow.add_node("human", human_review_node)

# Set Entry Point
workflow.set_entry_point("scout")

# Edges
workflow.add_edge("scout", "budget")

# Budget -> Decision
workflow.add_conditional_edges(
    "budget",
    decide_next_step,
    {
        "retry": "scout",
        "planner": "planner",
        "human": "human", 
        "failed": END
    }
)

# Planner -> Decision
workflow.add_conditional_edges(
    "planner",
    decide_next_step,
    {
        "retry": "scout",
        "done": END,
        "human": "human", # <--- Route to Human
        "failed": END
    }
)

# Human -> End
# After the human decides, either finish (success) or fail (quit)
workflow.add_edge("human", END) 

app = workflow.compile()