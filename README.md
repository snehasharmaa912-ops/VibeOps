<div align="center">

# ✨ VibeOps

# LIVE DEMO 🔗: https://vibeops-snehasharmaa.streamlit.app/

### Multi-Agent AI Engineering Workspace

*Specialized AI agents collaborate under one orchestrator with shared memory — research, code, test, and document, all in one run.*

<br>

[

![CI](https://img.shields.io/badge/CI-passing-brightgreen?style=for-the-badge&logo=githubactions&logoColor=white)

](.github/workflows/ci.yml)
[

![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)

](https://www.python.org/)
[

![Tests](https://img.shields.io/badge/tests-8%20passing-success?style=for-the-badge&logo=pytest&logoColor=white)

](tests/)
[

![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange?style=for-the-badge)

](https://github.com/langchain-ai/langgraph)
[

![License](https://img.shields.io/badge/license-MIT-lightgrey?style=for-the-badge)

](#)

<br>

</div>

---

## 🚀 What is VibeOps?

> No more copy-pasting between AI chat tabs for research, then coding, then testing, then docs.
> **One request in → working code + tests + documentation out.**

A central **Orchestrator** delegates a task to three specialist agents — 🔍 **Research**, 💻 **Coder**, and 🧪 **Tester/Docs** — who share memory and hand work back and forth until the task is complete.

```mermaid
flowchart TD
    U([User Request]) --> O{Orchestrator}
    O --> R[Research Agent]
    R --> C[Code Agent]
    C --> T[Test Agent]
    T --> D[Doc Agent]
    D --> F([Final Output])

    R -. write/read .-> M[(Shared Memory: SQLite + Chroma)]
    C -. write/read .-> M
    T -. write/read .-> M
    D -. write/read .-> M

    style U fill:#6C63FF,color:#fff,stroke:#333
    style F fill:#22C55E,color:#fff,stroke:#333
    style O fill:#1E293B,color:#fff,stroke:#333
    style M fill:#FBBF24,color:#000,stroke:#333
    style R fill:#3B82F6,color:#fff
    style C fill:#8B5CF6,color:#fff
    style T fill:#EF4444,color:#fff
    style D fill:#14B8A6,color:#fff
```

---

## 🏗️ Architecture

### 1️⃣ Orchestrator — `src/orchestrator.py`
A **fixed state machine** built with LangGraph, not a free-roaming planner LLM. Each node is a specialist agent; edges define allowed transitions.

| Approach | ✅ Pro | ⚠️ Con |
|---|---|---|
| **Fixed state machine** *(chosen)* | Predictable, easy to debug, bounded cost | Less flexible to novel tasks |
| Dynamic LLM planner | Handles arbitrary workflows | Can loop, is expensive, hard to test |

An explicit `max_steps` guard means the pipeline can never loop forever, and every transition is logged.

### 2️⃣ Shared Memory — `src/memory.py`

```mermaid
flowchart LR
    A[Agent Output] --> B{Status?}
    B -- success --> C[(SQLite Working Memory)]
    B -- success --> D[(Chroma Long-Term Memory)]
    B -- failed --> C
    B -. failed, never indexed .-> D
```

| Layer | Storage | Purpose |
|---|---|---|
| 🗃️ **Working memory** | SQLite | Structured task state — which agent ran, what it returned, status, timestamps. Drives control flow. |
| 🧭 **Long-term memory** | Chroma (vector store) | Free-text semantic recall — *"have we solved something like this before?"* Additive context only, never control flow. |

Long-term memory uses a small, dependency-free hashing-based embedding function instead of Chroma's default (which downloads a ~90MB model from S3 and fails on network-restricted machines). This keeps the whole project runnable **fully offline** once installed.

### 3️⃣ Agents — `src/agents/`
Each agent is a thin wrapper: a system prompt + a single `run(task, context)` method that calls the Claude API and returns a structured result. Agents never call each other directly — they only read/write shared memory and return to the orchestrator, keeping them independently testable and swappable.

### 4️⃣ Message Schema — `src/schema.py`
All inter-agent communication uses one Pydantic model so logging, memory writes, and testing stay uniform across every agent:

```python
AgentMessage(task_id, role, input, context, output, status, timestamp)
```

---

## 🛡️ Failure Handling

| 🔧 Mechanism | Behavior |
|---|---|
| ♻️ **Retry** | Every agent call retries twice with exponential backoff |
| 🧯 **Graceful degrade** | If all retries fail, orchestrator marks task `failed`, logs it, returns a **partial result** instead of crashing |
| 🔒 **Loop guard** | `max_steps = 10` prevents infinite loops from routing bugs |

---

## ⚙️ Setup (100% free to run)

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # add your ANTHROPIC_API_KEY
python -m src.main "Build a Python function that validates email addresses"
```

> 💡 No paid infra required — SQLite and Chroma both run locally with zero setup. Anthropic's API offers free trial credits.

### 🎨 Run the Streamlit demo
```bash
streamlit run app.py
```

### ✅ Run tests
```bash
pytest tests/ -v
```

<div align="center">

**8/8 tests passing** — all use a mocked LLM client, so they run **offline with zero API cost** and are fully deterministic ✅

</div>

---

## 🧰 Tech Stack

<div align="center">



![LangGraph](https://img.shields.io/badge/-LangGraph-orange?style=flat-square)




![Anthropic](https://img.shields.io/badge/-Claude%20API-D97757?style=flat-square)




![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)




![Chroma](https://img.shields.io/badge/-ChromaDB-FBBF24?style=flat-square)




![Pydantic](https://img.shields.io/badge/-Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white)




![Streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)




![Pytest](https://img.shields.io/badge/-Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)




![GitHub Actions](https://img.shields.io/badge/-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)



</div>

| Layer | Tool |
|---|---|
| Orchestration | LangGraph (fixed state machine) |
| LLM | Claude API (Anthropic) |
| Structured memory | SQLite |
| Semantic memory | Chroma (offline embedding) |
| Schema / validation | Pydantic |
| Demo UI | Streamlit |
| Testing | pytest + mocked API client |
| CI | GitHub Actions |

---

<div align="center">

### 👩‍💻 Built by **Sneha Sharma**
✉️ sharmasnehaa08@gmail.com

</div>
