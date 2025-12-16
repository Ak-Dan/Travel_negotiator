![Maintenance](https://img.shields.io/badge/Maintenance-Active-green.svg)

**Project Status:**  **Active**
This project is currently being maintained. Future updates will focus on integrating Flight Search APIs (Amadeus) and replacing the SQLite memory with a production-grade Postgres checkpointer.

#  AI Travel Negotiator (Neuro-Symbolic System)

A **Neuro-Symbolic** multi-agent system that autonomously negotiates travel itineraries under strict constraints. Built with **LangGraph**, **Streamlit**, **Groq (Llama 3)**, and **Tavily**.

Unlike standard chatbots, this project uses a "Hybrid" approach: it combines the creative reasoning of **LLMs** with the mathematical reliability of **Python Code** to create a system that is fast, cost-effective, and hallucination-resistant.

Try the app here: https://prince-travel-agent.streamlit.app/

---

##  Key Features

* ** Neuro-Symbolic Architecture**
    * **Scout (LLM):** Uses Llama 3 to "read" live search results and creatively adjust strategy (Luxury vs. Budget).
    * **Budget & Planner (Code):** Uses pure Python for objective tasks (Math & Logic), ensuring 0% error rate on costs.
* ** Live Web Search**
    * Integrated with **Tavily API** to fetch real-time hotel prices and availability from the web.
    * Includes **Robust Regex Parsing** to extract clean JSON data from messy web text.
* ** Human-in-the-Loop**
    * Detects "Deadlocks" (when agents cannot agree after N retries).
    * Pauses execution and requests a **Human Decision** via the UI.
    * Agents respect the "Force Approve" override and bypass subsequent checks.
* ** Professional UI**
    * Built with **Streamlit**.
    * Features **Real-time Streaming** of agent thoughts.
    * Universal Design (Compatible with both Light and Dark modes).
    * Generates a "Booking Confirmation" card upon success.

---

## Architecture

The system operates as a **State Graph**, in which agents pass a shared memory object (`AgentState`) to one another.

```mermaid
flowchart TD
    User[Streamlit UI Input] --> Start
    
    subgraph "Agent Loop"
        Start --> Scout[ Scout Agent]
        Scout -->|Tavily API| Web(Search Real Hotels)
        Web -->|Raw Text| Scout
        Scout -->|JSON Proposal| Budget[ Budget Officer]
        
        Budget -->|Approved| Planner[ Planner Agent]
        Budget -->|Rejected| Router{Decide Next}
        
        Planner -->|Approved| End([ Final Itinerary])
        Planner -->|Rejected| Router
    end
    
    Router -->|Retry Count < 3| Scout
    Router -->|Retry Count >= 3| Human[ Human Intervention]
    
    Human -->|Force Approve| End
    Human -->|Stop| Fail([ Negotiation Failed])
````
##  System Design & Scalability

### Modular Agent Design
The system follows a **Separation of Concerns** principle, ensuring modularity and ease of maintenance. Each agent is designed as a standalone functional unit:

* ** The Scout (Interface Layer):** Responsible strictly for **I/O operations** (Search & Parsing). It acts as the gateway between unstructured web data and the system's structured state.
* ** The Budget Officer (Logic Layer):** Responsible strictly for **Validation**. It is decoupled from the search logic, meaning the validation rules (e.g., adding tax, verifying limits) can be updated without touching the LLM prompts.
* ** The Planner (Constraint Layer):** Responsible for **Geospatial Logic**. This separation allows us to swap the underlying map provider (e.g., Google Maps vs. Mapbox) without affecting the budgeting or search modules.

### Scalability
The architecture is built on **LangGraph**, which utilizes a persistent state schema.
* **Stateless Execution:** Each node execution is independent, allowing the system to be deployed on serverless infrastructure (e.g., AWS Lambda) for horizontal scaling.
* **Graph Extensibility:** New agents (e.g., a "Flight Booker" or "Visa Checker") can be added as new nodes in the graph without rewriting the core orchestration logic.

-----

##  Tech Stack

  * **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) (Cyclic State Management)
  * **Frontend:** [Streamlit](https://streamlit.io/) (Interactive Web UI)
  * **Inference:** [Groq API](https://groq.com/) (Llama 3-70B for sub-second speeds)
  * **Tools:** [Tavily Search API](https://tavily.com/) (AI-optimized Web Search)
  * **Language:** Python 3.10+

-----

##  Installation

1.  **Clone the repository**

    ```bash
    git clone [https://github.com/YOUR_USERNAME/travel-negotiator.git](https://github.com/YOUR_USERNAME/travel-negotiator.git)
    cd travel-negotiator
    ```

2.  **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables**
    Create a `.env` file in the root directory:

    ```env
    GROQ_API_KEY=gsk_...
    TAVILY_API_KEY=tvly-...
    ```

-----

##  Usage

Run the Streamlit application:

```bash
streamlit run frontend.py
```

### How to use the UI:

1.  **Enter Trip Details:** Destination (e.g., "Paris"), Budget (e.g., "$2000"), and Duration.
2.  **Watch the Debate:** The agents will search live data and debate the cost/location.
3.  **Intervene:** If the constraints are too tight (e.g., "$100 budget for Paris"), the agents will get stuck. A "Conflict Detected" box will appear, allowing you to Force Approve the trip or Stop the negotiation.

-----

##  Project Structure

```text
├── frontend.py         # Main Streamlit UI Application
├── main.py             # CLI Entry Point (for testing without UI)
├── src/
│   ├── agents.py       # Agent Logic (Scout, Budget, Planner)
│   ├── graph.py        # LangGraph Workflow & Routing Logic
│   ├── state.py        # Shared State Schema (TypedDict)
│   └── tools.py        # Tool Definitions (Tavily Search wrapper)
├── requirements.txt    # Python Dependencies
├── .env                # API Keys (Excluded from Git)
└── README.md           # Documentation
```

-----

##  Engineering Decisions

  * **Why Hybrid?**
    Using an LLM for simple math (Budget Check) is slow and prone to hallucination. By moving the Budget and Planner logic to **Pure Python**, we reduced latency by **40%** and guaranteed mathematical accuracy.
  * **Passthrough Logic:**
    The agents are programmed with a "Human Override" check at the start of their execution. If `human_decision="approve"` is detected, they bypass their usual strict checks to honour the user's authority.
  * **Regex Extraction:**
    To handle messy web data, the Scout uses a robust regular expression (`r"\{.*?\}"`) to search for JSON objects in the LLM's response, preventing parsing errors.

-----

###  Testing Strategy
1.  **Unit & Integration (Mocked):** Fast, free tests that verify the graph logic and routing using `unittest.mock`.
    * Run: `pytest -m "not live"`
2.  **Live Evals (End-to-End):** Real-world tests that hit the Groq and Tavily APIs to verify prompt quality and live data fetching.
    * Run: `pytest -m live`


**2. Structured Logging:**
The system replaces standard print statements with Python's `logging` module. This provides:
- **Timestamps:** To track latency and execution order.
- **Log Levels:** `INFO` for normal flow, `WARNING` for rejections, and `ERROR` for API failures.
- **Traceability:** Easier debugging of the multi-agent decision loop.

##  License

This project is licensed under the **MIT License**.

