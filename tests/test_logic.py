import pytest
from src.agents import budget_agent, planner_agent

# --- HELPER: MOCK STATE ---
# This creates a fake "state" object so we can test the functions in isolation
def create_mock_state(price, budget, location, status="IN_PROGRESS"):
    return {
        "current_proposal": {"name": "Test Hotel", "price": price, "location": location},
        "total_budget": budget,
        "days": 5,
        "human_decision": None,
        "plan_status": status,
        "destination": "Test City",
        "retry_count": 0,
        "rejection_reason": None,
        "messages": []
    }

# --- TEST 1: BUDGET OFFICER ---

def test_budget_officer_rejection():
    """Test that the Budget Officer rejects expensive hotels."""
    # Scenario: Hotel ($500/night * 5 days) + $100 expenses = $2600. 
    # Budget is $1000. Should REJECT.
    state = create_mock_state(price=500, budget=1000, location="City Center")
    
    result = budget_agent(state)
    
    assert result["plan_status"] == "REJECTED"
    assert "exceeds budget" in result["rejection_reason"]

def test_budget_officer_approval():
    """Test that the Budget Officer approves affordable hotels."""
    # Scenario: Hotel ($100/night * 5 days) + $100 expenses = $600. 
    # Budget is $1000. Should APPROVE.
    state = create_mock_state(price=100, budget=1000, location="City Center")
    
    result = budget_agent(state)
    
    assert result["plan_status"] == "BUDGET_APPROVED"

def test_budget_passthrough():
    """Test that the Budget Officer respects the 'APPROVED' flag."""
    state = create_mock_state(price=9999, budget=100, location="City Center", status="APPROVED")
    
    result = budget_agent(state)
    
    # Even though price is high, it should skip math because status is already APPROVED
    assert result["plan_status"] == "APPROVED"
    assert "Skipped" in result["messages"][0]


# --- TEST 2: PLANNER AGENT ---

def test_planner_rejection():
    """Test that the Planner rejects bad locations."""
    # Scenario: Location is 'Suburbs' (which our logic deems too far).
    state = create_mock_state(price=100, budget=1000, location="Suburbs")
    
    result = planner_agent(state)
    
    assert result["plan_status"] == "REJECTED"
    assert "too far" in result["rejection_reason"]

def test_planner_approval():
    """Test that the Planner approves central locations."""
    state = create_mock_state(price=100, budget=1000, location="City Center")
    
    result = planner_agent(state)
    
    assert result["plan_status"] == "APPROVED"