import operator
from typing import TypedDict, Annotated, List, Optional

class AgentState(TypedDict):
    """
    The shared memory state for the travel negotiation system.
    """
    # -- INPUTS --
    destination: str
    total_budget: int
    days: int
    
    # -- INTERNAL STATE --
    messages: Annotated[List[str], operator.add] 
    current_proposal: Optional[dict] 
    rejection_reason: Optional[str] 
    plan_status: str  # "IN_PROGRESS", "REJECTED", "APPROVED", "WAITING_FOR_HUMAN"
    retry_count: int
    
    # -- NEW FIELD --
    human_decision: Optional[str] # "approve" or "quit"s