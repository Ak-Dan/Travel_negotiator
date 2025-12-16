import os
from dotenv import load_dotenv
load_dotenv()  # Load API keys from .env file
# Updated import based on LangChain 0.3 standards
from langchain_tavily import TavilySearchResults
from langchain_core.tools import tool

# Initialize Tavily
tavily_tool = TavilySearchResults(max_results=3)

@tool
def search_hotels(query: str):
    """
    Searches for hotels using the Tavily API.
    Pass a natural language query like "budget hotels in Paris".
    Returns raw search results.
    """
    print(f"   [TOOL]  Searching the web for: '{query}'...")
    return tavily_tool.invoke({"query": query})

@tool
def calculate_total(hotel_price: int, days: int, daily_food_cost: int = 100):
    """Calculates the total cost."""
    return (hotel_price * days) + (daily_food_cost * days)

@tool
def check_distance(hotel_location: str, interest_point: str = "City Center"):
    """
    Checks distance. 
    NOTE: Since we are using live data, this is a simplified logic check.
    """
    # If the scout says it's in the "Suburbs", we assume it's far.
    if "Suburbs" in hotel_location:
        return 45
    elif "City Center" in hotel_location:
        return 5
    return 20 # Default average