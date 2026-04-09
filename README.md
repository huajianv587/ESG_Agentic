# ESG Agentic RAG Copilot

Enterprise ESG analysis, scoring, monitoring, and reporting platform built with FastAPI, LangGraph, Qdrant, Supabase, and a local-first / cloud-fallback LLM runtime.

This README is bilingual:

- English version first
- 中文版本 second

---

# English Version

## 1. Project Overview

ESG Agentic RAG Copilot is a product-oriented ESG intelligence platform designed for:

- ESG question answering
- company-level ESG scoring
- RAG-enhanced report and evidence analysis
- proactive ESG event monitoring
- scheduled report generation
- dashboard-style customer demos and delivery

The system supports both:

- reactive workflows, where a user asks a question and gets an answer or score
- proactive workflows, where the platform scans signals, evaluates risk, and generates reports

## 2. Current Status

This repository is currently prepared for two practical usage modes:

### Fast demo mode

This is the recommended path for demo recording and live presentation.

- one-click start with `start.cmd`
- uses `APP_MODE=local`
- uses `LLM_BACKEND_MODE=cloud`
- uses `DEMO_FAST_MODE=1`
- bypasses the slow full RAG warm-up path for faster first response

### Local-first product mode

This is the fuller runtime path for local development and integration testing.

- uses `APP_MODE=local`
- uses `LLM_BACKEND_MODE=auto`
- fallback order is typically `Local -> DeepSeek -> OpenAI`
- may require Qdrant and longer warm-up time

## 3. What The Product Includes

- FastAPI backend with modular API routers
- LangGraph-based agent orchestration
- RAG retrieval and indexing pipeline
- Supabase-backed data and report storage
- ESG scoring workflows and visual outputs
- proactive scheduler and event-monitoring pipeline
- static frontend dashboard
- bilingual UI toggle: `ENG / 中文`
- Windows helper scripts for setup and startup

## 4. Architecture

```text
Frontend (static SPA)
        |
        v
FastAPI Gateway
  |- /health
  |- /health/ready
  |- /agent/*
  |- /dashboard/*
  |- /admin/*
        |
        +--> Agentic ESG analysis path
        |     |- Router Agent
        |     |- Retriever Agent
        |     |- Analyst Agent
        |     \- Verifier Agent
        |
        \--> Proactive scheduler path
              |- Scanner
              |- Event extractor
              |- Risk scorer
              |- Matcher
              |- Notifier
              \- Report generator

Shared runtime services
  |- Qdrant
  |- Supabase
  \- local / remote / cloud LLM clients
```

## 5. Repository Layout

```text
.
|- gateway/                 # backend app, routers, runtime, agents, RAG, scheduler
|- frontend/                # static frontend SPA
|- scripts/                 # bootstrap, run, smoke, doctor, build helpers
|- docs/                    # deployment and delivery documentation
|- tests/                   # automated tests
|- training/                # training / evaluation utilities
|- data/                    # local runtime data and indexes
|- dist/                    # generated static frontend and output artifacts
|- requirements.txt
|- package.json
|- docker-compose.yml
|- .env.example
\- start.cmd                # one-click demo launcher
```

## 6. Main Frontend Pages

The frontend is designed for demo and dashboard-style interaction.

- `Overview`: flagship summary page
- `Chat`: ESG Q&A interface
- `Scoring`: company ESG score generation and visualization
- `Report Center`: report viewing and export
- `Data Sync`: data-source and scheduler visibility
- `Push Rules`: push-rule configuration
- `Subscription Management`: tracked-company subscriptions

## 7. Prerequisites

Recommended minimum setup:

- Windows environment for the provided `.bat` scripts
- Python `3.11+`
- `.venv` available, or permission to create one
- `.env` configured
- at least one cloud API key:
  - `DEEPSEEK_API_KEY`, or
  - `OPENAI_API_KEY`

Optional for fuller local-first mode:

- Docker Desktop
- local Qdrant on port `6333`
- Supabase project and credentials

## 8. Minimal Environment Variables

Start from `.env.example` and make sure at least these values are available:

```env
APP_MODE=local

DEEPSEEK_API_KEY=...
OPENAI_API_KEY=...
```

For fuller local-first mode, the project also expects values such as:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=./data/vector_db
```

Do not commit your real `.env`.

## 9. Quick Start

### Option A. Fastest Demo Start

This is the best choice if you need the app running quickly for a demo.

1. Prepare the environment:

```bat
scripts\bootstrap_local_windows.bat
```

2. Create `.env` from `.env.example` and fill in at least:

- `DEEPSEEK_API_KEY`, or
- `OPENAI_API_KEY`

3. Start the demo server:

```bat
start.cmd
```

Optional custom port:

```bat
start.cmd 8012
```

What `start.cmd` does:

- checks `.venv`
- checks `.env`
- sets `APP_MODE=local`
- sets `LLM_BACKEND_MODE=cloud`
- sets `DEMO_FAST_MODE=1`
- waits for `/health`
- automatically opens `/app`

Default app URL pattern:

- `http://127.0.0.1:<port>/app`

Stop the server:

- return to the terminal window
- press `Ctrl + C`

### Option B. Local-First Development Start

Use this when you want the fuller local runtime path.

1. Bootstrap Python dependencies:

```bat
scripts\bootstrap_local_windows.bat
```

2. Start local Qdrant:

```bat
scripts\start_local_qdrant_windows.bat
```

3. Start the API:

```bat
scripts\run_local_first_windows.bat
```

4. Check health:

```bat
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/ready
```

5. Open:

- app: `http://127.0.0.1:8000/app`
- docs: `http://127.0.0.1:8000/docs`

### Option C. Demo Fast Script Without One-Click Browser Launch

```bat
scripts\run_demo_fast_windows.bat
```

This starts the API in fast demo mode on port `8000` with reload enabled.

## 10. Frontend Build

To build the static frontend bundle:

```bash
npm run build:static
```

Output directory:

- `dist/`

## 11. Main Runtime Modes

### `LLM_BACKEND_MODE=cloud`

- direct cloud response path
- fastest for demo use
- practical fallback order: `DeepSeek -> OpenAI`

### `LLM_BACKEND_MODE=auto`

- local-first behavior
- intended fallback order: `Local -> DeepSeek -> OpenAI`
- local model may be skipped automatically if CUDA is unavailable

### `DEMO_FAST_MODE=1`

- skips the heavy background RAG initialization path
- improves first-response speed for demos
- recommended for presentation and video recording

## 12. Health And Readiness

### `GET /health`

Use this for liveness and general runtime inspection.

It returns information such as:

- runtime mode
- active backend mode
- cloud fallback order
- module status

### `GET /health/ready`

Use this for readiness checks.

- returns `200` when required runtime modules are ready
- may return `503` while the system is still warming up

In fast demo mode, `/health` is the more useful check because full readiness may intentionally stay incomplete.

## 13. Main API Endpoints

Important product endpoints include:

- `POST /agent/analyze`
- `POST /agent/esg-score`
- `GET /dashboard/overview`
- `POST /admin/reports/generate`
- `POST /admin/data-sources/sync`
- `GET /health`
- `GET /health/ready`

See also:

- [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)

## 14. Key Scripts

### Setup and startup

- `start.cmd`
- `scripts/bootstrap_local_windows.bat`
- `scripts/run_demo_fast_windows.bat`
- `scripts/run_local_first_windows.bat`
- `scripts/run_local_hybrid_windows.bat`
- `scripts/start_local_qdrant_windows.bat`

### Diagnostics and validation

- `scripts/local_api_smoke.py`
- `scripts/runtime_doctor.py`
- `scripts/staging_check.py`
- `scripts/rag_quality_check.py`

### Maintenance and document generation

- `scripts/rebuild_rag_index.py`
- `scripts/generate_customer_delivery_doc.py`
- `scripts/build_static_frontend.mjs`

## 15. Common Commands

### Run tests

```bash
python -m pytest -q
```

### Runtime doctor

```bash
python scripts/runtime_doctor.py
```

### Local smoke test

```bash
python scripts/local_api_smoke.py --app-mode local --llm-backend-mode auto
```

### Build static frontend

```bash
npm run build:static
```

## 16. Troubleshooting

### `start.cmd` opens the browser but the page says connection refused

This usually means the browser opened before the backend was fully ready.

Current `start.cmd` now waits for `/health` before opening `/app`, but if you still see this:

1. wait a few more seconds
2. refresh the page
3. check `http://127.0.0.1:<port>/health`
4. restart the script if necessary

### The page opens but `/health/ready` is still `503`

That can be normal in full local mode while:

- Qdrant is warming up
- the RAG index is being restored
- the scheduler is starting

### The local model never runs

That is expected on CPU-only hosts.

In that case the system falls back to cloud providers.

### English mode still shows some Chinese

Refresh the page with `Ctrl + F5` to force the newest frontend assets.

The frontend uses versioned JS/CSS assets, but browser cache can still make old tabs look stale.

## 17. Demo Notes

For demo recording, use:

- `start.cmd`

Recommended flow:

1. open `Overview`
2. show `ENG / 中文` toggle
3. enter `Chat`
4. ask a fast ESG question
5. open `Scoring`
6. generate a company score
7. open `Report Center`

## 18. Related Documents

- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- [docs/STAGING_RELEASE_RUNBOOK.md](docs/STAGING_RELEASE_RUNBOOK.md)
- [docs/LOCAL_HYBRID_RUNBOOK.md](docs/LOCAL_HYBRID_RUNBOOK.md)
- [docs/LOCAL_HYBRID_RUNBOOK_ZH.md](docs/LOCAL_HYBRID_RUNBOOK_ZH.md)
- [docs/REMOTE_GPU_RUNBOOK.md](docs/REMOTE_GPU_RUNBOOK.md)
- [docs/PRODUCT_DELIVERY_CHECKLIST_ZH.md](docs/PRODUCT_DELIVERY_CHECKLIST_ZH.md)

## 19. License

MIT

---

# 中文版本

## 1. 项目简介

ESG Agentic RAG Copilot 是一个面向产品演示、分析交付和本地开发的 ESG 智能平台，主要能力包括：

- ESG 问答分析
- 公司级 ESG 评分
- 基于 RAG 的报告与证据检索分析
- 主动式 ESG 风险事件监测
- 定时报表生成
- 可用于演示和交付的仪表盘前端

系统同时支持两类工作流：

- 被动式工作流：用户提问，系统返回回答或评分
- 主动式工作流：系统持续扫描信号、评估风险、生成报告

## 2. 当前状态

这个仓库目前已经整理成两种最实用的运行方式：

### 快速 Demo 模式

这是当前最推荐的启动方式，适合：

- 录 demo 视频
- 现场演示
- 快速验证页面和问答流程

特点：

- 使用 `start.cmd` 一键启动
- 使用 `APP_MODE=local`
- 使用 `LLM_BACKEND_MODE=cloud`
- 使用 `DEMO_FAST_MODE=1`
- 跳过完整 RAG 冷启动链路，优先保证响应速度

### 本地优先产品模式

这是更完整的本地运行链路，适合：

- 本地开发
- 接口联调
- 更接近完整产品流程的测试

特点：

- 使用 `APP_MODE=local`
- 使用 `LLM_BACKEND_MODE=auto`
- 典型回退顺序为：`本地模型 -> DeepSeek -> OpenAI`
- 可能需要 Qdrant，并且冷启动时间更长

## 3. 产品能力范围

- 基于 FastAPI 的后端接口层
- 基于 LangGraph 的 Agent 编排
- RAG 检索与索引流程
- Supabase 数据和报告存储
- ESG 评分与可视化
- 主动式扫描与调度管线
- 静态前端 SPA
- 前端中英文切换：`ENG / 中文`
- Windows 本地启动和辅助脚本

## 4. 系统架构

```text
静态前端 SPA
     |
     v
FastAPI Gateway
  |- /health
  |- /health/ready
  |- /agent/*
  |- /dashboard/*
  |- /admin/*
     |
     +--> Agentic ESG 分析链路
     |     |- Router Agent
     |     |- Retriever Agent
     |     |- Analyst Agent
     |     \- Verifier Agent
     |
     \--> 主动调度链路
           |- Scanner
           |- Event extractor
           |- Risk scorer
           |- Matcher
           |- Notifier
           \- Report generator

共享运行时能力
  |- Qdrant
  |- Supabase
  \- 本地 / 远程 / 云端 LLM 客户端
```

## 5. 仓库结构

```text
.
|- gateway/                 # 后端应用、路由、运行时、Agent、RAG、调度
|- frontend/                # 静态前端 SPA
|- scripts/                 # 安装、启动、构建、体检、烟测脚本
|- docs/                    # 部署与交付文档
|- tests/                   # 自动化测试
|- training/                # 训练与评估工具
|- data/                    # 本地数据和索引
|- dist/                    # 构建产物和输出文件
|- requirements.txt
|- package.json
|- docker-compose.yml
|- .env.example
\- start.cmd                # 一键 demo 启动脚本
```

## 6. 主要前端页面

前端目前面向演示和可视化交付设计，主要页面包括：

- `Overview`：总览页
- `Chat`：ESG 对话页
- `Scoring`：企业 ESG 评分页
- `Report Center`：报告中心
- `Data Sync`：数据同步与调度状态
- `Push Rules`：推送规则
- `Subscription Management`：订阅管理

## 7. 环境要求

建议最小环境：

- Windows 环境，便于直接使用 `.bat` 脚本
- Python `3.11+`
- 已有 `.venv`，或者允许脚本创建 `.venv`
- 已配置 `.env`
- 至少一个云端 API Key：
  - `DEEPSEEK_API_KEY`
  - 或 `OPENAI_API_KEY`

如需更完整的本地优先运行：

- Docker Desktop
- 本地可访问的 Qdrant，端口 `6333`
- Supabase 项目及相关密钥

## 8. 最小环境变量

请从 `.env.example` 复制生成 `.env`，并至少保证下面这些值存在：

```env
APP_MODE=local

DEEPSEEK_API_KEY=...
OPENAI_API_KEY=...
```

如果你要运行更完整的本地优先链路，通常还需要：

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=./data/vector_db
```

不要把真实 `.env` 提交到仓库。

## 9. 快速开始

### 方式 A：最快 Demo 启动

如果你的目标是尽快打开网页开始演示，推荐这一种。

1. 先准备 Python 环境：

```bat
scripts\bootstrap_local_windows.bat
```

2. 复制 `.env.example` 为 `.env`，并至少填写：

- `DEEPSEEK_API_KEY`
- 或 `OPENAI_API_KEY`

3. 一键启动：

```bat
start.cmd
```

如果你想指定端口：

```bat
start.cmd 8012
```

`start.cmd` 会自动做这些事：

- 检查 `.venv`
- 检查 `.env`
- 设置 `APP_MODE=local`
- 设置 `LLM_BACKEND_MODE=cloud`
- 设置 `DEMO_FAST_MODE=1`
- 等待 `/health` 可访问
- 自动打开 `/app`

访问地址格式：

- `http://127.0.0.1:<端口>/app`

停止服务：

- 回到启动它的终端窗口
- 按 `Ctrl + C`

### 方式 B：本地优先完整模式

如果你想跑更完整的本地链路，使用下面这组命令。

1. 安装依赖：

```bat
scripts\bootstrap_local_windows.bat
```

2. 启动本地 Qdrant：

```bat
scripts\start_local_qdrant_windows.bat
```

3. 启动 API：

```bat
scripts\run_local_first_windows.bat
```

4. 检查健康状态：

```bat
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/ready
```

5. 打开：

- 页面：`http://127.0.0.1:8000/app`
- 接口文档：`http://127.0.0.1:8000/docs`

### 方式 C：仅启动快速 Demo API

```bat
scripts\run_demo_fast_windows.bat
```

这个脚本会在 `8000` 端口启动快速 demo 模式，并开启 `reload`。

## 10. 前端构建

构建静态前端：

```bash
npm run build:static
```

输出目录：

- `dist/`

## 11. 主要运行模式说明

### `LLM_BACKEND_MODE=cloud`

- 直接走云端回答链路
- 最适合 demo 和演示
- 实际回退顺序通常为：`DeepSeek -> OpenAI`

### `LLM_BACKEND_MODE=auto`

- 本地优先模式
- 目标顺序为：`本地模型 -> DeepSeek -> OpenAI`
- 如果没有 CUDA，本地模型可能会自动跳过

### `DEMO_FAST_MODE=1`

- 跳过沉重的后台 RAG 初始化过程
- 明显提升首问速度
- 适合录视频和现场演示

## 12. 健康检查与就绪检查

### `GET /health`

用于检查服务是否存活，以及查看运行时基本状态。

返回内容通常包括：

- 当前运行模式
- 当前后端模式
- 云端回退顺序
- 模块状态

### `GET /health/ready`

用于检查系统是否完全就绪。

- 当关键模块都准备好时返回 `200`
- 如果系统还在预热，可能返回 `503`

注意：

在快速 demo 模式下，`/health` 往往比 `/health/ready` 更有参考价值，因为这个模式本来就不会等完整 RAG 全量准备完。

## 13. 主要接口

项目里最关键的接口包括：

- `POST /agent/analyze`
- `POST /agent/esg-score`
- `GET /dashboard/overview`
- `POST /admin/reports/generate`
- `POST /admin/data-sources/sync`
- `GET /health`
- `GET /health/ready`

完整接口说明可参考：

- [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)

## 14. 关键脚本

### 安装与启动

- `start.cmd`
- `scripts/bootstrap_local_windows.bat`
- `scripts/run_demo_fast_windows.bat`
- `scripts/run_local_first_windows.bat`
- `scripts/run_local_hybrid_windows.bat`
- `scripts/start_local_qdrant_windows.bat`

### 诊断与校验

- `scripts/local_api_smoke.py`
- `scripts/runtime_doctor.py`
- `scripts/staging_check.py`
- `scripts/rag_quality_check.py`

### 维护与文档

- `scripts/rebuild_rag_index.py`
- `scripts/generate_customer_delivery_doc.py`
- `scripts/build_static_frontend.mjs`

## 15. 常用命令

### 运行测试

```bash
python -m pytest -q
```

### 运行时体检

```bash
python scripts/runtime_doctor.py
```

### 本地烟测

```bash
python scripts/local_api_smoke.py --app-mode local --llm-backend-mode auto
```

### 构建静态前端

```bash
npm run build:static
```

## 16. 常见问题

### `start.cmd` 打开浏览器后显示连接被拒绝

这通常说明浏览器打开得比后端真正完成启动更早。

现在的 `start.cmd` 已经会先轮询 `/health` 再打开 `/app`，但如果你仍然遇到：

1. 再等几秒
2. 手动刷新页面
3. 检查 `http://127.0.0.1:<端口>/health`
4. 必要时重新执行 `start.cmd`

### 页面能打开，但 `/health/ready` 一直是 `503`

这在完整本地模式下可能是正常现象，说明系统还在预热，例如：

- Qdrant 正在恢复
- RAG 索引正在加载
- 调度器正在启动

### 本地模型一直没有跑

如果机器没有 CUDA，这是正常行为。

系统会自动回退到云端模型。

### 英文模式下还残留中文

先按 `Ctrl + F5` 强制刷新页面，确保浏览器拿到最新的前端资源。

因为前端资源有版本号，如果浏览器标签页缓存了旧脚本，看起来就像“代码改了但页面没变”。

## 17. Demo 建议

如果你是为了录演示视频，推荐直接用：

- `start.cmd`

推荐演示顺序：

1. 打开 `Overview`
2. 展示 `ENG / 中文` 切换
3. 进入 `Chat`
4. 输入一个 ESG 问题
5. 进入 `Scoring`
6. 生成一个公司评分
7. 打开 `Report Center`

## 18. 相关文档

- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- [docs/STAGING_RELEASE_RUNBOOK.md](docs/STAGING_RELEASE_RUNBOOK.md)
- [docs/LOCAL_HYBRID_RUNBOOK.md](docs/LOCAL_HYBRID_RUNBOOK.md)
- [docs/LOCAL_HYBRID_RUNBOOK_ZH.md](docs/LOCAL_HYBRID_RUNBOOK_ZH.md)
- [docs/REMOTE_GPU_RUNBOOK.md](docs/REMOTE_GPU_RUNBOOK.md)
- [docs/PRODUCT_DELIVERY_CHECKLIST_ZH.md](docs/PRODUCT_DELIVERY_CHECKLIST_ZH.md)

## 19. License

MIT
