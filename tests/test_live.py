import pytest
from src.graph import app

# This marker is to exclude this test by default
# Run with: pytest -m live
@pytest.mark.live 
def test_live_paris_trip():
    """
    REAL WORLD TEST: Hits the actual Groq and Tavily APIs.
    Verifies that the prompt is good enough to find a real hotel
    and that the JSON parsing works on real, messy web data.
    """
    print("\n[LIVE TEST] contacting Llama 3 & Tavily... this may take 10s...")
    
    initial_state = {
        "destination": "Paris",
        "total_budget": 2000,
        "days": 5,
        "retry_count": 0,
        "messages": [],
        "rejection_reason": None,
        "plan_status": "IN_PROGRESS",
        "human_decision": None
    }

    # Run the real graph
    final_state = app.invoke(initial_state)

    #  Check Success Status
    assert final_state["plan_status"] == "APPROVED", \
        f"Expected APPROVED, got {final_state['plan_status']}"
    
    #  Check Data Integrity
    proposal = final_state["current_proposal"]
    assert proposal is not None
    assert isinstance(proposal["price"], int) or isinstance(proposal["price"], float)
    assert proposal["price"] > 0
    
    print(f"\n SUCCESS: Found hotel '{proposal['name']}' for ${proposal['price']}/night.")