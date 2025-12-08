from dotenv import load_dotenv
load_dotenv() # Load API keys from .env

from src.graph import app

def run_negotiation():
    print("--- STARTING TRAVEL NEGOTIATOR---")
    
    # TEST CASE:
    # We set a LOW budget to force the agents to negotiate.
    # A luxury hotel costs $450/night. 
    # 5 days = $2250 + food ($500) = $2750.
    # Our budget is $1500.
    # This MUST fail the first time and force a loop to the budget option.
    
    initial_state = {
        "destination": "Paris",
        "total_budget": 1500, 
        "days": 5,
        "retry_count": 0,
        "messages": [],
        "rejection_reason": None,
        "plan_status": "IN_PROGRESS"
    }
    
    # Run the graph
    final_state = app.invoke(initial_state)
    
    print("\n\n--- NEGOTIATION FINISHED ---")
    
    if final_state["plan_status"] == "APPROVED":
        print(" SUCCESS! Trip Booked.")
        proposal = final_state["current_proposal"]
        print(f"   Hotel: {proposal['name']}")
        print(f"   Location: {proposal['location']}")
        print(f"   Price: ${proposal['price']}/night")
    else:
        print(" FAILED. Could not find a suitable itinerary.")
        print(f"   Final Reason: {final_state.get('rejection_reason')}")

if __name__ == "__main__":
    run_negotiation()