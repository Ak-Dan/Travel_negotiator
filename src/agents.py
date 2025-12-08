from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AgentState
from src.tools import search_hotels, calculate_total, check_distance
import os
import re
import json

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0,
    api_key=os.environ.get("GROQ_API_KEY")
)

# --- AGENT 1: THE SCOUT ---
def scout_agent(state: AgentState):

    
    # PASSTHROUGH: If human approved, skip search
    if state.get("human_decision") == "approve":
        print("   [SCOUT] Human override detected. Skipping search.")
        return {
            "plan_status": "APPROVED",
            "messages": ["Scout: Honoring human override."]
        }

    print(f"\n--- SCOUT: Working on {state['destination']} ---")
    
    # 1. READ STATE
    rejection_reason = state.get("rejection_reason")
    retry_count = state.get("retry_count", 0)
    
    # 2. DECIDE STRATEGY
    system_prompt = """You are a Travel Scout.
    Decide whether to search for a 'luxury' or 'budget' hotel.
    - If rejection mentioned 'expensive', switch to 'budget'.
    - If rejection mentioned 'far', switch to 'luxury'.
    - Default to 'luxury'.
    Respond with ONLY: "luxury" or "budget".
    """
    decision = llm.invoke([
        SystemMessage(content=system_prompt), 
        HumanMessage(content=f"History: {rejection_reason}")
    ]).content.strip().lower()
    
    tier = "budget" if "budget" in decision else "luxury"
    print(f"   [SCOUT] Strategy: Searching for {tier} options.")

    # 3. EXECUTE SEARCH
    query = f"{tier} hotels in {state['destination']} price per night"
    search_results = search_hotels.invoke(query)
    
   # 4. EXTRACT DATA
    extraction_prompt = f"""
    You are a Data Extractor. 
    Here are the raw search results: {search_results}
    
    CRITICAL: Return a JSON object with these EXACT keys:
    - "name": (str) Name of hotel
    - "price": (int) Price per night (numbers only, remove '$')
    - "location": (str) EITHER "City Center" OR "Suburbs" (Infer this)
    """
    
    raw_response = llm.invoke([HumanMessage(content=extraction_prompt)])
    content = raw_response.content
    
    try:
        # Regex to find the JSON object
        match = re.search(r"\{.*?\}", content, re.DOTALL)
        if match:
            json_str = match.group(0)
            proposal = json.loads(json_str)
            print(f"   [SCOUT] Found: {proposal['name']} (${proposal['price']})")
        else:
            raise ValueError("No JSON found in response")
            
    except Exception as e:
        print(f"   [SCOUT] Extraction Error: {e}")
        # Let's see what the LLM actually said so we can debug
        print(f"   [SCOUT] Raw LLM Output: {content}")
        
        # IMPROVED FALLBACK: Randomize it slightly so it doesn't loop identically
        import random
        proposal = {
            "name": "Fallback Inn (Error)", 
            "price": random.randint(150, 300), 
            "location": "City Center"
        }

    return {
        "current_proposal": proposal,
        "plan_status": "PROPOSED",
        "retry_count": retry_count + 1,
        "rejection_reason": None,
        "messages": [f"Scout: Proposed {proposal['name']}"]
    }

# --- AGENT 2: BUDGET OFFICER ---
def budget_agent(state: AgentState):
    
    # PASSTHROUGH: If already approved, skip math
    if state.get("plan_status") == "APPROVED" or state.get("human_decision") == "approve":
        print("   [BUDGET] Skipping check (Human Approved).")
        return {
            "plan_status": "APPROVED",
            "messages": ["Budget: Skipped due to override."]
        }

    print("\n--- BUDGET OFFICER: Reviewing ---")
    proposal = state["current_proposal"]
    days = state["days"]
    total_budget = state["total_budget"]
    
    total_cost = calculate_total.invoke({"hotel_price": proposal["price"], "days": days})
    
    if total_cost > total_budget:
        reason = f"Total cost ${total_cost} exceeds budget of ${total_budget}."
        print(f"   [BUDGET] REJECTED: {reason}")
        return {
            "plan_status": "REJECTED", 
            "rejection_reason": reason,
            "messages": [f"Budget: Rejected. {reason}"]
        }
        
    print(f"   [BUDGET] APPROVED: ${total_cost} is within budget.")
    return {
        "plan_status": "BUDGET_APPROVED",
        "messages": [f"Budget: Approved. Cost ${total_cost}."]
    }


# --- AGENT 3: PLANNER ---
def planner_agent(state: AgentState):
    
    # PASSTHROUGH: If already approved, skip distance check
    if state.get("plan_status") == "APPROVED" or state.get("human_decision") == "approve":
        print("   [PLANNER] Skipping check (Human Approved).")
        return {
            "plan_status": "APPROVED",
            "messages": ["Planner: Skipped due to override."]
        }

    print("\n--- PLANNER: Checking Logistics ---")
    proposal = state["current_proposal"]
    
    dist = check_distance.invoke({"hotel_location": proposal["location"]})
    
    if dist > 30:
        reason = f"Hotel is too far ({dist} mins) from City Center."
        print(f"   [PLANNER] REJECTED: {reason}")
        return {
            "plan_status": "REJECTED",
            "rejection_reason": reason,
            "messages": [f"Planner: Rejected. {reason}"]
        }
        
    print(f"   [PLANNER] APPROVED: {dist} mins is acceptable.")
    return {
        "plan_status": "APPROVED",
        "messages": [f"Planner: Final Approval!"]
    }

# --- HUMAN NODE ---
def human_review_node(state: AgentState):
    # If the UI already injected the decision, process it
    if state.get("human_decision") == "approve":
        return {"plan_status": "APPROVED", "messages": ["Human overruled the agents."]}
    elif state.get("human_decision") == "quit":
        return {"plan_status": "REJECTED", "messages": ["Human stopped the process."]}
    
    # Otherwise, pause for UI
    return {
        "plan_status": "WAITING_FOR_HUMAN", 
        "messages": ["Waiting for human decision..."]
    }