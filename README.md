# KAI ADK Chat Agent — DB + RAG Connectors (Local)

This repo demonstrates an ADK chat agent with:

1. **Authenticated connector to a primary DB (MySQL)** for structured admissions data
2. **Vector DB connector (Qdrant)** for RAG over admissions documents

---

## What’s implemented

### Primary DB (MySQL) connector (auth)

* Safe, parameterized DB tools (no raw SQL from user input)
* Example tools:

  * `get_program_overview(program_name)`
  * `list_intakes(program_name)`

### Vector DB (Qdrant) connector for RAG

* Document ingestion pipeline (chunk → embed → upsert into Qdrant)
* Retrieval tool:

  * `rag_search(query)` returns top chunks + sources

---

## Prerequisites

* Python 3.11+ (recommended)
* Docker + Docker Compose
* A Google GenAI API key (for embeddings)

---

## Repo layout

```
.
├── agents/
│   └── kai_agent/
│       ├── root_agent.yaml
│       ├── db_tools.py
│       ├── rag_tools.py
│       ├── rag_docs/
│       │   ├── refund_policy.md
│       │   ├── scholarships.md
│       │   └── application_checklist.md
│       └── .env                # gitignored
├── scripts/
│   └── ingest_rag.py
├── docker-compose.yml
├── .env                         # optional; gitignored
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

### 1) Environment variables

Copy the template and fill in values:

```bash
cp .env.example .env
```

Then edit `.env` and set:

* `GOOGLE_API_KEY` (or `GEMINI_API_KEY`)
* MySQL settings (match docker-compose defaults)
* Qdrant settings

For local ADK tool loading, copy env into the agent folder:

```bash
cp .env agents/kai_agent/.env
```

---

### 2) Start services (MySQL + Qdrant)

```bash
docker compose up -d
```

Optional health checks:

```bash
# Qdrant
curl -s http://localhost:6333/collections

# MySQL (inside container)
docker exec -it kai-mysql mysql -uadmissions_user -padmissions_pw -D admissions \
  -e "SELECT name, fee_usd FROM programs;"
```

---

### 3) Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 4) Ingest RAG documents into Qdrant

```bash
source .venv/bin/activate
python scripts/ingest_rag.py
```

You should see a message like:

```
✅ Ingested <N> chunks into Qdrant collection 'admissions_rag'
```

---

### 5) Run ADK

Run from the **project root** (so the loader can find `agents/`):

```bash
source .venv/bin/activate
adk web agents --port 8000
```

Open the UI:

* [http://127.0.0.1:8000/dev-ui/](http://127.0.0.1:8000/dev-ui/)

Select `kai_agent` in the left dropdown.

---

## Test prompts

### DB (structured)

* **What’s the fee and duration for Data Analytics Bootcamp?**
* **List upcoming intakes for Data Analytics Bootcamp.**

Expected behavior:

* Agent calls DB tools (`get_program_overview`, `list_intakes`)
* Answers are grounded; Trace shows tool calls

### RAG (unstructured)

* **What’s the refund policy if I withdraw after 10 days?**
* **What scholarship options are available and how long do decisions take?**
* **What documents are required to apply?**

Expected behavior:

* Agent calls `rag_search`
* Answers cite `Source(s): <filename>`

---

## Notes

* If RAG queries return empty results, re-run ingestion:

  ```bash
  python scripts/ingest_rag.py
  ```
* If ADK fails to load tools, check that `root_agent.yaml` only references modules that exist.

---
