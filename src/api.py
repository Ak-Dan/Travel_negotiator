import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.graph import app as travel_graph  # Importing your LangGraph app

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Initialize the API
app = FastAPI(
    title="TravelGraph API",
    description="Neuro-Symbolic Agent API for Travel Planning",
    version="1.0"
)

# 2. Define Input Schema (Standardizes what users send)
class TripRequest(BaseModel):
    destination: str
    total_budget: int
    days: int = 5

# 3. Define the Endpoint
@app.post("/plan-trip")
async def plan_trip(request: TripRequest):
    """
    Endpoints that triggers the multi-agent negotiation.
    """
    logger.info(f"API received request for: {request.destination}")
    
    # Prepare the initial state for your Graph
    initial_state = {
        "destination": request.destination,
        "total_budget": request.total_budget,
        "days": request.days,
        "retry_count": 0,
        "messages": [],
        "rejection_reason": None,
        "plan_status": "IN_PROGRESS",
        "human_decision": None
    }
    
    try:
        # EXECUTE THE GRAPH
        # .invoke() runs the agents until they finish or hit a breakpoint
        final_state = travel_graph.invoke(initial_state)
        
        # Return a clean JSON response
        return {
            "status": final_state.get("plan_status", "UNKNOWN"),
            "destination": final_state.get("destination"),
            "itinerary": final_state.get("current_proposal", {}),
            "logs": final_state.get("messages", [])[-5:]  # Send last 5 logs
        }
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 4. Health Check (Good for keeping the server alive)
@app.get("/health")
def health_check():
    return {"status": "active", "system": "TravelGraph Neuro-Symbolic Agents"}