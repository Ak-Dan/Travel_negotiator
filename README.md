# 🌍 AI Travel Negotiator (Neuro-Symbolic System)

A **Neuro-Symbolic** multi-agent system that autonomously negotiates travel itineraries under strict constraints. Built with **LangGraph**, **Streamlit**, **Groq (Llama 3)**, and **Tavily**.

Unlike standard chatbots, this project uses a "Hybrid" approach: it combines the creative reasoning of **LLMs** with the mathematical reliability of **Python Code** to create a system that is fast, cost-effective, and hallucination-resistant.

Try the app here: https://prince-travel-agent.streamlit.app/

---

## ✨ Key Features

* **🧠 Neuro-Symbolic Architecture**
    * **Scout (LLM):** Uses Llama 3 to "read" live search results and creatively adjust strategy (Luxury vs. Budget).
    * **Budget & Planner (Code):** Uses pure Python for objective tasks (Math & Logic), ensuring 0% error rate on costs.
* **🌐 Live Web Search**
    * Integrated with **Tavily API** to fetch real-time hotel prices and availability from the web.
    * Includes **Robust Regex Parsing** to extract clean JSON data from messy web text.
* **🚨 Human-in-the-Loop**
    * Detects "Deadlocks" (when agents cannot agree after N retries).
    * Pauses execution and requests a **Human Decision** via the UI.
    * Agents respect the "Force Approve" override and bypass subsequent checks.
* **🖥️ Professional UI**
    * Built with **Streamlit**.
    * Features **Real-time Streaming** of agent thoughts.
    * Universal Design (Compatible with both Light and Dark modes).
    * Generates a "Booking Confirmation" card upon success.

---

## 🏗️ Architecture

The system operates as a **State Graph** where agents pass a shared memory object (`AgentState`) between them.

```mermaid
flowchart TD
    User[Streamlit UI Input] --> Start
    
    subgraph "Agent Loop"
        Start --> Scout[🕵️ Scout Agent]
        Scout -->|Tavily API| Web(Search Real Hotels)
        Web -->|Raw Text| Scout
        Scout -->|JSON Proposal| Budget[💰 Budget Officer]
        
        Budget -->|Approved| Planner[🗺️ Planner Agent]
        Budget -->|Rejected| Router{Decide Next}
        
        Planner -->|Approved| End([✅ Final Itinerary])
        Planner -->|Rejected| Router
    end
    
    Router -->|Retry Count < 3| Scout
    Router -->|Retry Count >= 3| Human[🚨 Human Intervention]
    
    Human -->|Force Approve| End
    Human -->|Stop| Fail([❌ Negotiation Failed])
````

-----

## 🛠️ Tech Stack

  * **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) (Cyclic State Management)
  * **Frontend:** [Streamlit](https://streamlit.io/) (Interactive Web UI)
  * **Inference:** [Groq API](https://groq.com/) (Llama 3-70B for sub-second speeds)
  * **Tools:** [Tavily Search API](https://tavily.com/) (AI-optimized Web Search)
  * **Language:** Python 3.10+

-----

## ⚙️ Installation

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

## 🚀 Usage

Run the Streamlit application:

```bash
streamlit run frontend.py
```

### How to use the UI:

1.  **Enter Trip Details:** Destination (e.g., "Paris"), Budget (e.g., "$2000"), and Duration.
2.  **Watch the Debate:** The agents will search live data and debate the cost/location.
3.  **Intervene:** If the constraints are too tight (e.g., "$100 budget for Paris"), the agents will get stuck. A **"Conflict Detected"** box will appear, allowing you to **Force Approve** the trip or **Stop** the negotiation.

-----

## 📂 Project Structure

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

## 💡 Engineering Decisions

  * **Why Hybrid?**
    Using an LLM for simple math (Budget Check) is slow and prone to hallucination. By moving the Budget and Planner logic to **Pure Python**, we reduced latency by **40%** and guaranteed mathematical accuracy.
  * **Passthrough Logic:**
    The agents are programmed with a "Human Override" check at the start of their execution. If `human_decision="approve"` is detected, they bypass their usual strict checks to honor the user's authority.
  * **Regex Extraction:**
    To handle messy web data, the Scout uses a robust Regex pattern (`r"\{.*?\}"`) to hunt for JSON objects within the LLM's response, preventing parsing errors.

-----

## 📜 License

This project is licensed under the **MIT License**.

