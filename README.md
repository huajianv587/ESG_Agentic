# ESG Agentic RAG Copilot

An enterprise-grade ESG (Environmental, Social, Governance) analysis platform powered by multi-agent RAG architecture. It combines LangGraph-based agentic reasoning, hybrid vector retrieval, 15-dimensional ESG scoring, proactive event monitoring, and a full-stack web dashboard — delivering both reactive Q&A and autonomous ESG intelligence.

## Architecture

```
                        +---------------------------+
                        |     Frontend (SPA)        |
                        |  Chat / Dashboard / Reports|
                        +------------+--------------+
                                     |
                        +------------v--------------+
                        |    FastAPI Gateway         |
                        |    (gateway/main.py)       |
                        +-----+---------------+-----+
                              |               |
                 +------------v---+   +-------v-----------+
                 | Reactive Path  |   | Proactive Path    |
                 | (Agentic RAG)  |   | (Scheduler)       |
                 +------+---------+   +--------+----------+
                        |                      |
          +-------------v-----------+  +-------v----------+
          | LangGraph State Machine |  | Orchestrator     |
          |                         |  |                  |
          | Router Agent            |  | Scanner          |
          |   -> Retriever Agent    |  | Event Extractor  |
          |     -> Analyst Agent    |  | Risk Scorer      |
          |       -> Verifier Agent |  | Matcher          |
          +-----------+-------------+  | Notifier         |
                      |                | Report Generator |
          +-----------v-------------+  +-------+----------+
          |       Data Layer        |          |
          |                         <----------+
          | Qdrant (Vector DB)      |
          | Supabase (PostgreSQL)   |
          +-------------------------+
```

## Key Features

### Multi-Agent Reasoning (LangGraph)

Four specialized agents work as a pipeline with conditional routing and retry loops:

- **Router Agent** — classifies queries into `esg_analysis`, `factual`, or `general`
- **Retriever Agent** — hybrid BM25 + vector similarity search over ESG reports
- **Analyst Agent** — structured 15-dimensional ESG scoring with industry benchmarking
- **Verifier Agent** — validates answer grounding, assigns confidence scores, triggers retries if needed

### 15-Dimensional ESG Scoring

| Environmental (E) | Social (S) | Governance (G) |
|---|---|---|
| Carbon Emissions | Employee Satisfaction | Board Diversity |
| Energy Efficiency | Diversity & Inclusion | Executive Compensation |
| Water Management | Supply Chain Ethics | Anti-corruption |
| Waste Management | Community Impact | Risk Management |
| Renewable Energy | Customer Responsibility | Shareholder Rights |

### RAG Pipeline

- **Ingestion**: PDF parsing from 23+ ESG/sustainability reports
- **Chunking**: Hierarchical node parser (2048 / 512 / 128 tokens)
- **Indexing**: Qdrant vector store with OpenAI `text-embedding-3-small`
- **Retrieval**: Hybrid BM25 + dense vector search with reranking
- **Evaluation**: ROUGE metrics with automated quality reports

### Proactive Monitoring & Scheduling

- Autonomous ESG event scanning from multiple data sources
- Structured event extraction and risk quantification
- User-rule based matching and push notifications
- Automated PDF/HTML report generation (daily/weekly/monthly)

### Full-Stack Web UI

Single-page application with dark theme:

- **Chat Interface** — multi-turn conversation with the agent system
- **Overview Dashboard** — KPI gauges and ESG trend charts
- **Score Dashboard** — detailed 15-dimension scoring visualization
- **Reports** — on-demand and scheduled report generation
- **Data Management** — upload and manage ESG data sources
- **Push Rules** — configure notification triggers
- **Subscriptions** — manage report subscriptions

### Fine-Tuned ESG Model

- Base model: Qwen/Qwen2.5-7B-Instruct
- Method: LoRA (Low-Rank Adaptation) via PEFT
- Training data: 15M+ tokens of ESG-specific Q&A pairs
- Evaluation: ROUGE/BLEU metrics with visualization reports

## Project Structure

```
ESG Agentic RAG Copilot/
├── gateway/                  # Backend core (FastAPI)
│   ├── main.py               # API entry point (40+ endpoints)
│   ├── agents/               # LangGraph multi-agent system
│   │   ├── graph.py          # State machine orchestration
│   │   ├── router_agent.py   # Query classification
│   │   ├── retriever_agent.py# Document retrieval
│   │   ├── analyst_agent.py  # ESG analysis
│   │   ├── verifier_agent.py # Answer verification
│   │   ├── esg_scorer.py     # 15-dimension scoring framework
│   │   ├── esg_visualizer.py # Visualization generation
│   │   ├── prompts.py        # System prompts
│   │   └── tools.py          # LangChain tool definitions
│   ├── rag/                  # RAG pipeline
│   │   ├── rag_main.py       # RAG orchestration
│   │   ├── chunking.py       # Hierarchical chunking
│   │   ├── indexer.py        # Qdrant vector indexing
│   │   ├── ingestion.py      # PDF ingestion
│   │   ├── retriever.py      # Hybrid retrieval
│   │   ├── evaluator.py      # ROUGE evaluation
│   │   └── event_indexer.py  # Async event indexing
│   ├── scheduler/            # Proactive monitoring
│   │   ├── orchestrator.py   # Pipeline coordinator
│   │   ├── scanner.py        # Event scanning
│   │   ├── event_extractor.py# Structured extraction
│   │   ├── matcher.py        # User-event matching
│   │   ├── risk_scorer.py    # Risk assessment
│   │   ├── notifier.py       # Push notifications
│   │   ├── data_sources.py   # Data source management
│   │   ├── report_generator.py   # Report generation
│   │   └── report_scheduler.py   # Report scheduling
│   ├── db/                   # Database layer
│   │   ├── supabase_client.py# Supabase integration
│   │   └── migrations/       # SQL schema (4 migrations)
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   └── utils/                # Shared utilities
│       ├── llm_client.py     # Multi-LLM client (local/remote/DeepSeek/OpenAI)
│       ├── logger.py         # Structured logging
│       ├── cache.py          # In-memory cache
│       └── retry.py          # Retry logic
├── frontend/                 # Web UI (SPA)
│   ├── index.html            # App shell
│   ├── css/app.css           # Styling (dark theme)
│   └── js/                   # Vanilla JS modules
│       ├── api.js            # API client
│       ├── app.js            # Entry point
│       ├── router.js         # SPA routing
│       ├── store.js          # State management
│       ├── components/       # Reusable UI components
│       └── pages/            # Page modules (7 pages)
├── training/                 # Model fine-tuning pipeline
│   ├── prepare_data.py       # Data preparation
│   ├── finetune.py           # LoRA fine-tuning
│   ├── evaluate_model.py     # Model evaluation
│   ├── launch_job.py         # Job launcher
│   └── run_on_autodl.sh      # Cloud training scripts
├── model-serving/            # Fine-tuned model artifacts
│   └── checkpoint/           # Qwen 7B LoRA weights (155M)
├── data/
│   ├── raw/                  # ESG report PDFs (23 files)
│   ├── rag_training_data/    # Fine-tuning JSONL data
│   ├── rag_eval/             # Evaluation results & charts
│   └── data_ingestion_scripts/  # Data processing scripts
├── deploy/                   # Deployment configs
│   ├── nginx.conf            # Reverse proxy
│   └── aws/                  # AWS ECS/ECR configs
├── docs/                     # Documentation
├── configs/config.py         # Settings loader
├── scripts/                  # Utility scripts
├── tests/                    # Unit tests
├── docker-compose.yml        # Docker orchestration
└── requirements.txt          # Python dependencies
```

## Tech Stack

| Layer | Technologies |
|---|---|
| **LLM & AI** | LangChain, LangGraph, LlamaIndex, OpenAI, Anthropic Claude, DeepSeek |
| **Vector DB** | Qdrant (hybrid BM25 + dense retrieval) |
| **Database** | Supabase (PostgreSQL) |
| **Backend** | FastAPI, Pydantic, uvicorn |
| **Frontend** | Vanilla JS, Tailwind CSS, Chart.js |
| **Fine-tuning** | Transformers, PEFT (LoRA), Qwen 7B |
| **Infra** | Docker, Nginx, AWS ECS/ECR |

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- API keys: OpenAI, Anthropic (optional), DeepSeek (optional)
- Supabase project (for database)

### 1. Clone & Configure

```bash
git clone https://github.com/your-username/ESG-Agentic-RAG-Copilot.git
cd ESG-Agentic-RAG-Copilot

cp .env.example .env
# Edit .env with your API keys and database credentials
```

### 2. Run with Docker Compose

```bash
docker-compose up -d
```

This starts three services:
- **Qdrant** vector database on port `6333`
- **FastAPI app** on port `8000`
- **Nginx** reverse proxy on port `80`

### 3. Initialize the RAG Index

On first run, the system automatically ingests PDF documents from `data/raw/` and builds the Qdrant vector index. This happens once and is cached in `storage/docstore/`.

### 4. Access the Application

Open `http://localhost` in your browser to access the web dashboard.

API documentation is available at `http://localhost:8000/docs`.

### Run Locally (without Docker)

```bash
pip install -r requirements.txt

# Start Qdrant separately
docker run -p 6333:6333 qdrant/qdrant:latest

# Run the FastAPI server
cd gateway
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Windows Local-First Mode (Recommended)

Recommended for the current delivery baseline when you are not enabling a
remote GPU host yet:

```bat
scripts\bootstrap_local_windows.bat
scripts\start_local_qdrant_windows.bat
scripts\run_local_first_windows.bat
```

Default generation order:

- local model
- DeepSeek
- OpenAI

### Windows Hybrid Mode (Optional Remote GPU / Future 5090)

Use this only when you explicitly bring back a remote GPU host later:

```bat
scripts\bootstrap_local_windows.bat
scripts\start_local_qdrant_windows.bat
scripts\run_local_hybrid_windows.bat
```

See [docs/LOCAL_HYBRID_RUNBOOK.md](docs/LOCAL_HYBRID_RUNBOOK.md) for the full
workflow, including the SSH tunnel and runtime doctor checks.
Chinese guide: [docs/LOCAL_HYBRID_RUNBOOK_ZH.md](docs/LOCAL_HYBRID_RUNBOOK_ZH.md)
Remote-only details: [docs/REMOTE_GPU_RUNBOOK.md](docs/REMOTE_GPU_RUNBOOK.md)

## Database Setup

Run the SQL migrations in order against your Supabase PostgreSQL instance:

```bash
# In Supabase SQL Editor, execute in order:
gateway/db/migrations/001_init_sessions.sql
gateway/db/migrations/002_add_esg_report_tables.sql
gateway/db/migrations/003_add_scheduler_tables.sql
gateway/db/migrations/004_align_runtime_schema.sql
```

## Model Fine-Tuning

The training pipeline fine-tunes Qwen 7B on ESG-specific tasks using LoRA:

```bash
cd training
pip install -r requirements.txt

# Prepare data
python prepare_data.py

# Launch fine-tuning (AutoDL / EC2)
bash run_on_autodl.sh   # or run_on_ec2.sh

# Evaluate
python evaluate_model.py
```

Pre-trained LoRA checkpoints are available in `model-serving/checkpoint/`.

## API Highlights

| Endpoint | Method | Description |
|---|---|---|
| `/agent/analyze` | POST | Chat-style ESG query with multi-agent reasoning |
| `/agent/esg-score` | POST | Full 15-dimension ESG scoring report |
| `/agent/chat-history` | GET | Retrieve conversation history |
| `/scheduler/run` | POST | Trigger proactive event scanning pipeline |
| `/reports/generate` | POST | On-demand ESG report generation |
| `/push-rules/*` | GET/POST | Manage notification rules |
| `/subscriptions/*` | GET/POST | Manage report subscriptions |
| `/health` | GET | Service health check |

Full API reference: [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### AWS ECS (Production)

See [deploy/README.md](deploy/README.md) for full AWS deployment guide including:
- ECR image push automation
- ECS task definition with Secrets Manager
- ALB + CloudWatch monitoring

### Vercel + Cloudflare Pages + Railway

This repo now includes first-class configs for a split deployment setup:

- `railway.toml` deploys the FastAPI backend from [gateway/Dockerfile](gateway/Dockerfile)
- `vercel.json` builds a static frontend bundle into `dist/`
- `wrangler.toml` supports Cloudflare Pages using the same `dist/` output

Recommended setup:

1. Deploy the backend to Railway and set all server-side secrets there.
2. Set `CORS_ORIGINS` on Railway to your Vercel / Cloudflare frontend domains.
3. Set `ESG_API_BASE_URL` on Vercel or Cloudflare Pages to your Railway backend URL.
4. Use the build command `npm run build:static` for static frontend deployments.

The frontend build writes `dist/app/app-config.js`, so the same codebase can run:

- on Railway at `/app` with same-origin API calls
- on Vercel / Cloudflare Pages with an external API base URL

## Documentation

- [Product Delivery Checklist (ZH)](docs/PRODUCT_DELIVERY_CHECKLIST_ZH.md)
- [API Endpoints Reference](docs/API_ENDPOINTS.md)
- [Data Source Replacement Guide](docs/DATA_SOURCE_REPLACEMENT_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Multi-Agent Roadmap](docs/MULTIAGENT_ROADMAP.md)
- [AWS Deployment](deploy/README.md)

## License

MIT
