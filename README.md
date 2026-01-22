# KAI ADK Chat Agent 

ADK agent with dynamic database querying, API integration, web scraping, and RAG capabilities.

## Key Features

### Dynamic MySQL Database Tools
- **Schema discovery** - automatically understands database structure
- **Real-time query generation** - converts natural language to SQL
- Tools: `get_database_schema()`, `execute_dynamic_query()`

### API Integration Tools  
- **Public API connector** for external data sources
- **Authentication support** for secured APIs
- Tools: `call_public_api()`, `call_rest_api_with_auth()`, `fetch_json_data()`

### Web Scraping Tools
- **Website content extraction** with BeautifulSoup
- **Targeted scraping** using CSS selectors  
- Tools: `scrape_webpage()`, `extract_specific_content()`, `get_page_metadata()`

### Vector DB (Qdrant) for RAG
- Document ingestion pipeline with embeddings
- Tool: `rag_search()` returns chunks + sources

---

## Quick Start

### Prerequisites
- Python 3.11+, Docker + Docker Compose
- Google GenAI API key

### Setup
```bash
# 1. Environment 
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY
cp .env agents/kai_agent/.env

# 2. Services
docker compose up -d

# 3. Dependencies
python -m venv .venv
source .venv/bin/activate
pip install google-adk mysql-connector-python python-dotenv qdrant-client
pip install requests beautifulsoup4 lxml

# 4. Ingest RAG documents
python scripts/ingest_rag.py

# 5. Run agent
adk web agents --port 8000
```

Open: [http://127.0.0.1:8000/dev-ui/](http://127.0.0.1:8000/dev-ui/) → Select `kai_agent`

---

## Test Questions

**Database Queries:**
- "What tables and columns are available in the database?"
- "Show me all programs with their fees"
- "Find the cheapest bootcamp program"

**API Integration:**
- "Get a random cat fact from an API"

**Web Scraping:**  
- "Scrape the main content from https://example.com"
- "Get metadata from https://github.com"

**Multi-Source:**
- "Show me our programs, then check competitor pricing from their website"

**RAG Documents:**
- "What's the refund policy if I withdraw after 10 days?"
- "What scholarship options are available?"

---

## Architecture

```
├── agents/kai_agent/
│   ├── root_agent.yaml          # Agent configuration
│   ├── db_tools.py             # Dynamic MySQL tools
│   ├── api_tools.py            # API integration tools  
│   ├── web_scraping_tools.py   # Web scraping tools
│   ├── rag_tools.py            # Vector search tools
│   └── rag_docs/               # Knowledge documents
├── docker-compose.yml          # MySQL + Qdrant services
└── scripts/ingest_rag.py      # Document ingestion
```

The agent routes queries to appropriate data sources: structured data → MySQL, external data → APIs, web content → scraping, policies → RAG.
