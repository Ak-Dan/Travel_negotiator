import streamlit as st
from src.graph import app
import time

# ---  PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Travel Negotiator",
    page_icon="✈️",
    layout="wide"
)

# ---  CSS FOR SPACING ONLY (No Color Overrides) ---
st.markdown("""
<style>
    /* Hide the default Streamlit header */
    header {visibility: hidden;}
    
    /* Add padding to bottom so the 'Stop' buttons are never hidden */
    .block-container {
        padding-bottom: 5rem;
    }
</style>
""", unsafe_allow_html=True)

# ---  SIDEBAR ---
with st.sidebar:
    st.title("🧳 Trip Settings")
    
    destination = st.text_input("Destination", "Manchester")
    # Note: min_value=500 prevents the error you saw in Screenshot 2
    budget = st.number_input("Total Budget ($)", min_value=500, value=1500, step=100)
    days = st.slider("Duration (Days)", 1, 14, 5)
    
    st.divider()
    
    if st.button("🚀 Start Negotiation", type="primary", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["current_state"] = {
            "destination": destination,
            "total_budget": budget, 
            "days": days,
            "retry_count": 0,
            "messages": [],
            "rejection_reason": None,
            "plan_status": "IN_PROGRESS",
            "human_decision": None
        }
        st.session_state["running"] = True
        st.rerun()

# ---  STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "running" not in st.session_state:
    st.session_state["running"] = False
if "current_state" not in st.session_state:
    st.session_state["current_state"] = {}

# --- MAIN HEADER ---
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"Negotiating Trip to {destination}")
with col2:
    status_text = "🟢 Active" if st.session_state["running"] else "⚪ Idle"
    if st.session_state["current_state"].get("plan_status") == "WAITING_FOR_HUMAN":
        status_text = "🟠 Waiting for You"
    st.markdown(f"**Status:** {status_text}")

st.divider()

# ---  CHAT HISTORY ---
chat_container = st.container()

def render_message(msg):
    """Helper to render messages with correct avatars"""
    avatar = "🤖"
    if "Scout" in msg: avatar="🕵️"
    elif "Budget" in msg: avatar="💰"
    elif "Planner" in msg: avatar="🗺️"
    elif "Human" in msg: avatar="👤"
    
    with st.chat_message(name="assistant", avatar=avatar):
        if "Approved" in msg:
            st.success(msg) # Green Box
        elif "Rejected" in msg:
            st.error(msg)   # Red Box
        elif "Scout" in msg:
            st.info(msg)    # Blue Box (New! Makes the Scout pop)
        else:
            st.write(msg)   # Standard Text
# Render existing history
with chat_container:
    for msg in st.session_state["messages"]:
        render_message(msg)

# --- 7. STREAMING LOGIC ---
if st.session_state["running"]:
    try:
        current_state = st.session_state["current_state"]
        
        # Stream events from the graph
        for event in app.stream(current_state):
            for node_name, updates in event.items():
                
                # Update State
                st.session_state["current_state"].update(updates)
                
                # Process New Messages
                new_msgs = updates.get("messages", [])
                for msg in new_msgs:
                    st.session_state["messages"].append(msg)
                    with chat_container:
                        render_message(msg)
                        time.sleep(0.5) # Tiny delay for effect
        
        # Loop Finished - Check Status
        final_state = st.session_state["current_state"]
        status = final_state["plan_status"]

        if status == "WAITING_FOR_HUMAN":
            st.session_state["running"] = False 
            st.rerun() # Refresh to show buttons
            
        elif status in ["APPROVED", "REJECTED"]:
            st.session_state["running"] = False
            st.rerun()

    except Exception as e:
        st.error(f"Execution Error: {e}")
        st.session_state["running"] = False

# --- 8. HUMAN INTERVENTION AREA ---
# This renders AT THE BOTTOM when needed

final_status = st.session_state["current_state"].get("plan_status")

if final_status == "WAITING_FOR_HUMAN":
    
    # We use a container with a border to make it POP out
    st.markdown("### 🚨 Conflict Detected")
    st.info("The agents cannot agree. Please make a decision below.")
    
    with st.container(border=True):
        col_info, col_actions = st.columns([2, 1])
        
        with col_info:
            reason = st.session_state["current_state"].get("rejection_reason")
            prop = st.session_state["current_state"].get("current_proposal", {})
            
            st.markdown(f"**Issue:** {reason}")
            st.markdown(f"**Pending Proposal:** {prop.get('name')} (${prop.get('price')})")
        
        with col_actions:
            if st.button("✅ Force Approve", type="primary", use_container_width=True):
                st.session_state["current_state"]["human_decision"] = "approve"
                st.session_state["running"] = True
                st.rerun()
                
            if st.button("❌ Stop Negotiation", use_container_width=True):
                st.session_state["current_state"]["human_decision"] = "quit"
                st.session_state["running"] = True
                st.rerun()

# --- REPLACE THE APPROVED BLOCK AT THE BOTTOM OF frontend.py ---

elif final_status == "APPROVED":
    st.balloons()
    
    # Get the Data
    proposal = st.session_state["current_state"]["current_proposal"]
    days = st.session_state["current_state"]["days"]
    # Re-calculate total to show the user (Hotel + Food)
    total_trip_cost = (proposal["price"] * days) + (100 * days)

    #  Render the "Ticket"
    st.markdown("### ✈️ Trip Itinerary Confirmed")
    
    with st.container(border=True):
        # Header: Hotel Name
        st.markdown(f"## 🏨 {proposal['name']}")
        st.caption(f"📍 {proposal['location']}")
        
        st.divider()
        
        # Details in 3 Columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Price per Night", value=f"${proposal['price']}")
        
        with col2:
            st.metric(label="Duration", value=f"{days} Days")
            
        with col3:
            # Highlight the Savings
            st.metric(label="Total Trip Cost", value=f"${total_trip_cost}")
        
        st.divider()
        
        # Call to Action
        st.success("✅ The agents have successfully negotiated this deal within your budget!")

elif final_status == "REJECTED":
    st.error("❌ **Negotiation Failed**")