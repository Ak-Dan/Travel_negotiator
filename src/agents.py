import os
import json
import re
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AgentState
from src.tools import search_hotels, calculate_total, check_distance

# ---  SETUP LOGGING (Resilience Improvement) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Groq LLM
llm = ChatGroq(
    model= "llama-3.3-70b-versatile", 
    temperature=0,
    api_key=os.environ.get("GROQ_API_KEY")
)

# --- AGENT 1: THE SCOUT ---
def scout_agent(state: AgentState):
    #  PASSTHROUGH
    if state.get("human_decision") == "approve":
        logger.info("[SCOUT] Human override detected. Skipping search.")
        return {
            "plan_status": "APPROVED",
            "current_proposal": state["current_proposal"],
            "messages": ["Scout: Honoring human override."]
        }

    logger.info(f"[SCOUT] Starting search for destination: {state['destination']}")
    
    rejection_reason = state.get("rejection_reason")
    retry_count = state.get("retry_count", 0)
    
    # DECIDE STRATEGY
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
    logger.info(f"[SCOUT] Strategy applied: Searching for {tier} options.")

    # EXECUTE SEARCH
    query = f"{tier} hotels in {state['destination']} price per night"
    try:
        search_results = search_hotels.invoke(query)
    except Exception as e:
        logger.error(f"[SCOUT] Tavily Search Failed: {e}")
        search_results = "" # Fail gracefully
    
    # EXTRACT DATA
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
        # ROBUST FIX: Use Regex to find the JSON object
        match = re.search(r"\{.*?\}", content, re.DOTALL)
        if match:
            json_str = match.group(0)
            proposal = json.loads(json_str)
            logger.info(f"[SCOUT] Successfully extracted: {proposal['name']} (${proposal['price']})")
        else:
            raise ValueError("No JSON found in response")
            
    except Exception as e:
        logger.warning(f"[SCOUT] Extraction Error: {e}. Using Fallback.")
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
    if state.get("plan_status") == "APPROVED" or state.get("human_decision") == "approve":
        logger.info("[BUDGET] Skipping check (Human Approved).")
        return {
            "plan_status": "APPROVED",
            "messages": ["Budget: Skipped due to override."]
        }

    logger.info("[BUDGET] Reviewing costs...")
    proposal = state["current_proposal"]
    days = state["days"]
    total_budget = state["total_budget"]
    
    # Using deterministic tool
    total_cost = calculate_total.invoke({"hotel_price": proposal["price"], "days": days})
    
    if total_cost > total_budget:
        reason = f"Total cost ${total_cost} exceeds budget of ${total_budget}."
        logger.warning(f"[BUDGET] REJECTED: {reason}")
        return {
            "plan_status": "REJECTED", 
            "rejection_reason": reason,
            "messages": [f"Budget: Rejected. {reason}"]
        }
        
    logger.info(f"[BUDGET] APPROVED: ${total_cost} is within budget.")
    return {
        "plan_status": "BUDGET_APPROVED",
        "messages": [f"Budget: Approved. Cost ${total_cost}."]
    }


# --- AGENT 3: PLANNER ---
def planner_agent(state: AgentState):
    if state.get("plan_status") == "APPROVED" or state.get("human_decision") == "approve":
        logger.info("[PLANNER] Skipping check (Human Approved).")
        return {
            "plan_status": "APPROVED",
            "messages": ["Planner: Skipped due to override."]
        }

    logger.info("[PLANNER] Checking logistics...")
    proposal = state["current_proposal"]
    
    # Using deterministic tool
    dist = check_distance.invoke({"hotel_location": proposal["location"]})
    
    if dist > 30:
        reason = f"Hotel is too far ({dist} mins) from City Center."
        logger.warning(f"[PLANNER] REJECTED: {reason}")
        return {
            "plan_status": "REJECTED",
            "rejection_reason": reason,
            "messages": [f"Planner: Rejected. {reason}"]
        }
        
    logger.info(f"[PLANNER] APPROVED: {dist} mins is acceptable.")
    return {
        "plan_status": "APPROVED",
        "messages": [f"Planner: Final Approval!"]
    }

# --- HUMAN NODE ---
def human_review_node(state: AgentState):
    if state.get("human_decision") == "approve":
        logger.info("[HUMAN] User manually approved the plan.")
        return {"plan_status": "APPROVED", "messages": ["Human overruled the agents."]}
    elif state.get("human_decision") == "quit":
        logger.info("[HUMAN] User manually stopped the process.")
        return {"plan_status": "REJECTED", "messages": ["Human stopped the process."]}
    
    logger.warning("[HUMAN] Deadlock detected. Waiting for user input.")
    return {
        "plan_status": "WAITING_FOR_HUMAN", 
        "messages": ["Waiting for human decision..."]
    }