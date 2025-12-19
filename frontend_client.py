import streamlit as st
import requests
import json

# CONFIG
API_URL = "https://travel-graph-api.onrender.com"

st.set_page_config(page_title="TravelGraph Pro", page_icon="✈️", layout="centered")

st.title(" TravelGraph")
st.caption("Neuro-Symbolic AI Agent System • Powered by FastAPI")

# SIDEBAR INPUTS
with st.sidebar:
    st.header("Trip Parameters")
    destination = st.text_input("Destination", "Paris")
    budget = st.number_input("Total Budget ($)", min_value=500, value=2000)
    days = st.slider("Duration (Days)", 3, 14, 5)
    
    # Server Status Check
    try:
        status = requests.get(
            f"{API_URL}/health", 
            timeout=2,
            proxies={"http": None, "https": None}
            )
        if status.status_code == 200:
            st.success(" API System Online")
        else:
            st.warning(" API Error")
    except:
        st.error(" Backend Offline (Run uvicorn!)")

# MAIN ACTION BUTTON
if st.button(" Launch Negotiation"):
    payload = {
        "destination": destination,
        "total_budget": budget,
        "days": days
    }
    
    # VISUAL FEEDBACK
    with st.status("Agents are negotiating...", expanded=True) as status:
        st.write(" Sending data to FastAPI backend...")
        
        try:
           # The 'proxies' part tells Python to ignore any school/work firewalls
            response = requests.post(
                f"{API_URL}/plan-trip", 
                json=payload,
                proxies={"http": None, "https": None} 
                )
            
            if response.status_code == 200:
                data = response.json()
                st.write(" Response received!")
                status.update(label="Planning Complete!", state="complete", expanded=False)
                # DISPLAY RESULTS
                result_status = data["status"]
                
                if result_status == "APPROVED" or result_status == "BUDGET_APPROVED":
                    st.balloons()
                    col1, col2 = st.columns(2)
                    proposal = data["itinerary"]
                    
                    with col1:
                        st.metric("Hotel", proposal.get("name", "Unknown"))
                        st.metric("Price/Night", f"${proposal.get('price', 0)}")
                    
                    with col2:
                        st.metric("Total Cost", f"${proposal.get('price', 0) * days}")
                        st.success(f"Outcome: {result_status}")
                        
                elif result_status == "WAITING_FOR_HUMAN":
                    st.warning(" CONFLICT: Budget likes it, but Planner thinks it's too far.")
                    
                    # Show the disputed option
                    col1, col2 = st.columns(2)
                    proposal = data["itinerary"]
                    with col1:
                        st.metric("Hotel", proposal.get("name"))
                        st.metric("Price/Night", f"${proposal.get('price')}")
                    with col2:
                        st.metric("Distance", "45 mins (Too far)") # In a real app, you'd extract this from logs
                        st.metric("Total Cost", f"${proposal.get('total_cost')}")
                    
                    st.write("---")
                    st.write("###  Human Decision Required")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(" Force Approve"):
                            # Send 'approve' signal to backend (Future feature)
                            st.success("You overruled the Planner! Trip Approved.")
                    with c2:
                        if st.button(" Cancel Trip"):
                            st.error("Trip Cancelled.")
                else:
                    st.error(f"Plan Rejected: {result_status}")
                    
                # Show Logs
                with st.expander("View Agent Negotiation Logs"):
                    for msg in data["logs"]:
                        st.text(msg)
                        
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error(" Connection Refused. Is the backend running?")