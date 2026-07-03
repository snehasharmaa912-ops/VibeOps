<div align="center">

# ✨ VibeOps

**A multi-agent AI engineering system where specialized agents collaborate under one orchestrator with shared memory.**

[

![CI](https://img.shields.io/badge/CI-passing-brightgreen)

](.github/workflows/ci.yml)
[

![Python](https://img.shields.io/badge/python-3.11%2B-blue)

](https://www.python.org/)
[

![Tests](https://img.shields.io/badge/tests-8%20passing-success)

](tests/)
[

![License](https://img.shields.io/badge/license-MIT-lightgrey)

](#)

</div>

---

## 🚀 What is VibeOps?

VibeOps runs an entire software task pipeline automatically — no more copy-pasting between AI chat tabs for research, then coding, then testing, then docs.

**One request in → working code + tests + documentation out.**

A central **Orchestrator** delegates work to three specialist agents — 🔍 **Research**, 💻 **Coder**, and 🧪 **Tester/Docs** — who share memory and hand work back and forth until the task is complete.

```
 User
   │
   ▼
 🧠 Orchestrator
   │
   ├──▶ 🔍 Research Agent
   ├──▶ 💻 Code Agent
   ├──▶ 🧪 Test Agent
   └──▶ 📝 Doc Agent
   │
   ▼
 ✅ Final Output
   
   ↑___________ 🗂️ shared memory (SQLite + Chroma) ___________↑
```

---

## 🏗️ Architecture

### 1. Orchestrator — `src/orchestrator.py`
A **fixed state machine** built with LangGraph, not a free-roaming planner LLM. Each node is a specialist agent; edges define allowed transitions.

| Approach | ✅ Pro | ⚠️ Con |
|---|---|---|
| **Fixed state machine** (chosen) | Predictable, easy to debug, bounded cost | Less flexible to novel tasks |
| Dynamic LLM planner | Handles arbitrary workflows | Can loop, is expensive, hard to test |

An explicit `max_steps` guard means the pipeline can never loop forever, and every transition is logged.

### 2. Shared Memory — `src/memory.py`
Two layers, because they solve different problems:

| Layer | Storage | Purpose |
|---|---|---|
| 🗃️ **Working memory** | SQLite | Structured task state — which agent ran, what it returned, status, timestamps. Drives control flow. |
| 🧭 **Long-term memory** | Chroma (vector store) | Free-text semantic recall — "have we solved something like this before?" Additive context only, never control flow. |

Long-term memory uses a small, dependency-free hashing-based embedding function instead of Chroma's default (which downloads a ~90MB model from S3 and fails on network-restricted machines). This keeps the whole project runnable **fully offline** once installed.

### 3. Agents — `src/agents/`
Each agent is a thin wrapper: a system prompt + a single `run(task, context)` method that calls the Claude API and returns a structured result. Agents never call each other directly — they only read/write shared memory and return to the orchestrator, which keeps them independently testable and swappable.

### 4. Message Schema — `src/schema.py`
All inter-agent communication uses one Pydantic model (`task_id, role, input, context, output, status, timestamp`) so logging, memory writes, and testing stay uniform across every agent.

---

## 🛡️ Failure Handling

- ♻️ Every agent call retries twice with exponential backoff
- 🧯 If an agent fails all retries, the orchestrator marks the task `failed`, logs it to memory, and returns a **partial result** instead of crashing
- 🔒 `max_steps = 10` guards against infinite loops from routing bugs

---

## 🔮 What I'd Do With More Time

- ⚡ Run independent agents in parallel instead of strictly sequentially
- 🧠 Swap the fixed state machine for a constrained dynamic planner once the fixed pipeline is proven reliable
- 📊 Add per-agent cost/latency dashboards

---

## ⚙️ Setup (100% free to run)

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # add your ANTHROPIC_API_KEY
python -m src.main "Build a Python function that validates email addresses"
```

No paid infra required — SQLite and Chroma both run locally with zero setup. Anthropic's API offers free trial credits.

### 🎨 Run the Streamlit demo
```bash
streamlit run app.py
```

### ✅ Run tests
```bash
pytest tests/ -v
```
All 8 tests use a mocked LLM client, so they run **offline with zero API cost** and are fully deterministic — safe to run in CI.

---

## 🧰 Tech Stack

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
