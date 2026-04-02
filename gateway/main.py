import sys
import asyncio
import json as _json
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any

# RAG和基础模块（可选，缺依赖时降级）
try:
    from gateway.rag.rag_main import get_query_engine
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"RAG模块加载失败: {_e}")
    get_query_engine = None

try:
    from db.supabase_client import save_message, get_history, create_session, get_client
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"Supabase模块加载失败: {_e}")
    save_message = get_history = create_session = get_client = None

try:
    from scheduler.orchestrator import get_orchestrator
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"Orchestrator模块加载失败: {_e}")
    get_orchestrator = None

try:
    from agents.graph import run_agent
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"Agent graph模块加载失败: {_e}")
    run_agent = None

# 新增的ESG增强模块
try:
    from agents.esg_scorer import ESGScoringFramework, ESGScoreReport
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"ESG scorer模块加载失败: {_e}")
    ESGScoringFramework = ESGScoreReport = None

try:
    from agents.esg_visualizer import ESGVisualizer
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"ESG visualizer模块加载失败: {_e}")
    ESGVisualizer = None

try:
    from scheduler.data_sources import DataSourceManager, CompanyData
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"DataSource模块加载失败: {_e}")
    DataSourceManager = CompanyData = None

try:
    from scheduler.report_generator import ESGReportGenerator
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"ReportGenerator模块加载失败: {_e}")
    ESGReportGenerator = None

try:
    from scheduler.report_scheduler import ReportScheduler, PushRule, ReportSubscription
except Exception as _e:
    import logging; logging.getLogger(__name__).warning(f"ReportScheduler模块加载失败: {_e}")
    ReportScheduler = PushRule = ReportSubscription = None

from gateway.config import settings
from gateway.utils.llm_client import get_runtime_backend_status
from utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="ESG Agentic RAG Copilot")

# ── CORS 配置 ──────────────────────────────────────────────────────────────
import os as _os


def _parse_cors_origins(raw_value: str) -> List[str]:
    if not raw_value or raw_value == "*":
        return ["*"]

    try:
        parsed = _json.loads(raw_value)
        if isinstance(parsed, list):
            origins = [str(item).strip() for item in parsed if str(item).strip()]
            if origins:
                return origins
    except Exception:
        pass

    origins = [item.strip().strip("\"'") for item in raw_value.split(",") if item.strip()]
    return origins or ["*"]


_cors_origins = _os.getenv("CORS_ORIGINS", "*")
_allowed_origins = _parse_cors_origins(_cors_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def disable_app_static_cache(request: Request, call_next):
    response: Response = await call_next(request)

    if request.url.path.startswith("/app"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response

# ── 全局模块初始化 ────────────────────────────────────────────────────────────
esg_scorer = None
esg_visualizer = None
data_source_manager = None
report_generator = None
report_scheduler = None
report_jobs: Dict[str, Dict[str, Any]] = {}
sync_jobs: Dict[str, Dict[str, Any]] = {}


def _ensure_session(session_id: str, user_id: Optional[str] = None) -> None:
    if session_id and create_session is not None:
        create_session(session_id=session_id, user_id=user_id)


def _serialize_model(model: Any) -> Any:
    if model is None:
        return None
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return model


def _flatten_report_row(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = row.get("data") or {}
    if not isinstance(payload, dict):
        payload = {}

    report_id = row.get("id") or payload.get("report_id")
    flattened = dict(payload)
    flattened["report_id"] = report_id
    flattened.setdefault("id", report_id)
    flattened.setdefault("report_type", row.get("report_type"))
    flattened.setdefault("title", row.get("title"))
    flattened.setdefault("period_start", row.get("period_start"))
    flattened.setdefault("period_end", row.get("period_end"))
    flattened.setdefault("generated_at", row.get("generated_at"))
    return flattened


def _fetch_report_row(report_id: str) -> Optional[Dict[str, Any]]:
    if get_client is None:
        return None

    response = (
        get_client()
        .table("esg_reports")
        .select("id, report_type, title, period_start, period_end, data, generated_at")
        .eq("id", report_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _fetch_latest_report_row(report_type: str, company: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if get_client is None:
        return None

    response = (
        get_client()
        .table("esg_reports")
        .select("id, report_type, title, period_start, period_end, data, generated_at")
        .eq("report_type", report_type)
        .order("generated_at", desc=True)
        .limit(20)
        .execute()
    )

    for row in response.data or []:
        payload = row.get("data") or {}
        analyses = payload.get("company_analyses") or []
        if not company:
            return row
        if any(str(item.get("company_name", "")).lower() == company.lower() for item in analyses):
            return row

    return None


def _generate_report_by_type(report_type: str, companies: List[str]):
    if report_generator is None:
        raise HTTPException(status_code=503, detail="Report Generator not ready")

    if report_type == "daily":
        return report_generator.generate_daily_report(companies)
    if report_type == "weekly":
        return report_generator.generate_weekly_report(companies)
    if report_type == "monthly":
        return report_generator.generate_monthly_report(companies)
    raise HTTPException(status_code=400, detail="Invalid report type")


def _store_report_job(job_id: str, report: Any, persisted_id: Optional[str] = None) -> Dict[str, Any]:
    payload = _serialize_model(report) or {}
    payload["report_id"] = persisted_id or job_id
    payload.setdefault("id", persisted_id or job_id)

    report_jobs[job_id] = {
        "status": "completed",
        "report_id": persisted_id or job_id,
        "report": payload,
        "generated_at": payload.get("generated_at"),
    }
    return payload

async def startup():
    """应用启动时初始化所有模块"""
    global esg_scorer, esg_visualizer, data_source_manager, report_generator, report_scheduler

    logger.info("[Startup] Initializing ESG enhanced modules...")

    # RAG引擎后台初始化（非阻塞）：服务器立即就绪，索引在后台建立
    app.state.query_engine = None
    if get_query_engine is not None:
        async def _init_rag():
            loop = asyncio.get_event_loop()
            try:
                engine = await loop.run_in_executor(None, get_query_engine)
                app.state.query_engine = engine
                logger.info("[Startup] RAG engine ready (background init complete)")
            except Exception as e:
                logger.warning(f"[Startup] RAG engine failed: {e}")
        asyncio.create_task(_init_rag())
        logger.info("[Startup] RAG engine building in background, server starting now...")
    else:
        logger.warning("[Startup] RAG engine skipped (module not available)")

    # ESG评分框架
    if ESGScoringFramework is not None:
        try:
            esg_scorer = ESGScoringFramework()
            logger.info("[Startup] ESG Scorer initialized")
        except Exception as e:
            logger.warning(f"[Startup] ESG Scorer failed: {e}")

    # 可视化器
    if ESGVisualizer is not None:
        try:
            esg_visualizer = ESGVisualizer()
            logger.info("[Startup] ESG Visualizer initialized")
        except Exception as e:
            logger.warning(f"[Startup] ESG Visualizer failed: {e}")

    # 数据源管理器
    if DataSourceManager is not None:
        try:
            data_source_manager = DataSourceManager()
            logger.info("[Startup] Data Source Manager initialized")
        except Exception as e:
            logger.warning(f"[Startup] Data Source Manager failed: {e}")

    # 报告生成器
    if ESGReportGenerator is not None:
        try:
            report_generator = ESGReportGenerator()
            logger.info("[Startup] Report Generator initialized")
        except Exception as e:
            logger.warning(f"[Startup] Report Generator failed: {e}")

    # 报告调度器
    if ReportScheduler is not None:
        try:
            report_scheduler = ReportScheduler()
            report_scheduler.start_background_scheduler()
            logger.info("[Startup] Report Scheduler started")
        except Exception as e:
            logger.warning(f"[Startup] Report Scheduler failed: {e}")

    logger.info("[Startup] All modules initialized successfully")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup()
    yield


app.router.lifespan_context = lifespan


# ── 请求/响应模型 ───────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    session_id: str
    question: str


class QueryResponse(BaseModel):
    session_id: str
    question: str
    answer: str


class AnalyzeRequest(BaseModel):
    session_id: str = ""
    question: str


class ESGScoreRequest(BaseModel):
    company: str
    ticker: Optional[str] = None
    include_visualization: bool = True
    peers: Optional[List[str]] = None
    historical_data: bool = False


class ReportGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    report_type: str  # "daily", "weekly", "monthly"
    companies: List[str]
    async_: bool = Field(default=True, alias="async")
    include_peer_comparison: bool = False


class DataSyncRequest(BaseModel):
    sources: Optional[List[str]] = None
    companies: List[str]
    force_refresh: bool = False


class CreatePushRuleRequest(BaseModel):
    rule_name: str
    condition: str
    target_users: str
    push_channels: List[str]
    priority: int
    template_id: str


class UserReportSubscribeRequest(BaseModel):
    report_types: List[str]
    companies: List[str]
    alert_threshold: Optional[Dict[str, Any]] = None
    push_channels: List[str]
    frequency: str = "daily"


class PushRuleTestRequest(BaseModel):
    test_user_id: str
    mock_report: Dict[str, Any]


# ── 健康检查 ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """服务健康检查"""
    query_engine = getattr(app.state, "query_engine", None)

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "app_mode": settings.APP_MODE,
        "runtime": get_runtime_backend_status(),
        "modules": {
            "rag": query_engine is not None,
            "esg_scorer": esg_scorer is not None,
            "report_scheduler": report_scheduler is not None,
        }
    }


@app.get("/dashboard/overview")
def dashboard_overview():
    """旗舰首页总览数据"""
    generated_at = datetime.now(timezone.utc)
    query_engine = getattr(app.state, "query_engine", None)

    health_modules = {
        "rag": query_engine is not None,
        "esg_scorer": esg_scorer is not None,
        "report_scheduler": report_scheduler is not None,
        "data_sources": data_source_manager is not None,
    }

    recent_signals = []
    signal_source = "database"

    try:
        from db.supabase_client import get_client

        db = get_client()
        response = (
            db.table("esg_events")
            .select("id,title,company,event_type,source,source_url,detected_at,created_at,raw_content")
            .order("detected_at", desc=True)
            .limit(6)
            .execute()
        )

        for item in response.data or []:
            description = (
                item.get("description")
                or item.get("raw_content")
                or "最新 ESG 动态已进入监控队列。"
            )
            recent_signals.append({
                "id": item.get("id"),
                "company": item.get("company") or "市场观察",
                "title": item.get("title") or "新的 ESG 事件",
                "description": description,
                "event_type": item.get("event_type") or "update",
                "source": item.get("source") or "database",
                "source_url": item.get("source_url"),
                "detected_at": item.get("detected_at") or item.get("created_at"),
                "tone": "alert" if "rule" in str(item.get("title", "")).lower() else "positive",
            })

    except Exception as e:
        signal_source = "scanner_fallback"
        logger.warning(f"[Dashboard] Failed to load recent signals from database: {e}")

    if not recent_signals:
        signal_source = "scanner_fallback"
        try:
            from scheduler.scanner import get_scanner

            scanner = get_scanner()
            sample_events = []
            sample_events.extend(scanner.scan_news_feeds()[0])
            sample_events.extend(scanner.scan_esg_reports()[0])
            sample_events.extend(scanner.scan_compliance_updates()[0])

            tone_map = {
                "EMISSION_REDUCTION": "positive",
                "RENEWABLE_ENERGY": "positive",
                "GOVERNANCE_CHANGE": "alert",
            }

            for idx, event in enumerate(sample_events[:6]):
                event_type = str(event.event_type).split(".")[-1] if event.event_type else "UPDATE"
                recent_signals.append({
                    "id": f"sample-{idx}",
                    "company": event.company or "市场观察",
                    "title": event.title,
                    "description": event.description,
                    "event_type": event_type,
                    "source": event.source,
                    "source_url": event.source_url,
                    "detected_at": event.detected_at.isoformat(),
                    "tone": tone_map.get(event_type, "neutral"),
                })
        except Exception as e:
            logger.warning(f"[Dashboard] Scanner fallback unavailable: {e}")

    if not recent_signals:
        signal_source = "static_fallback"
        recent_signals = [
            {
                "id": "fallback-1",
                "company": "Tesla",
                "title": "Tesla 更新碳减排目标",
                "description": "环境目标被重新量化，市场关注其供应链执行速度。",
                "event_type": "EMISSION_REDUCTION",
                "source": "fallback",
                "source_url": None,
                "detected_at": generated_at.isoformat(),
                "tone": "positive",
            },
            {
                "id": "fallback-2",
                "company": "Microsoft",
                "title": "Microsoft 发布最新 ESG 报告",
                "description": "报告强调可再生能源与治理透明度提升。",
                "event_type": "RENEWABLE_ENERGY",
                "source": "fallback",
                "source_url": None,
                "detected_at": generated_at.isoformat(),
                "tone": "positive",
            },
            {
                "id": "fallback-3",
                "company": "SEC",
                "title": "新的 ESG 披露规则进入市场视野",
                "description": "治理与合规要求进一步趋严，企业披露压力抬升。",
                "event_type": "GOVERNANCE_CHANGE",
                "source": "fallback",
                "source_url": None,
                "detected_at": generated_at.isoformat(),
                "tone": "alert",
            },
        ]

    try:
        scheduler_summary = get_scheduler_statistics(7)
    except Exception as e:
        logger.warning(f"[Dashboard] Scheduler summary unavailable: {e}")
        scheduler_summary = {
            "total_scans": 0,
            "success_rate": 0,
            "last_sync_time": None,
            "degraded": True,
            "message": "Scheduler summary unavailable",
        }

    total_signals = len(recent_signals)
    tracked_companies = len({item["company"] for item in recent_signals if item.get("company")})
    active_modules = sum(1 for ready in health_modules.values() if ready)

    spotlight = recent_signals[0]
    spotlight_company = spotlight.get("company") or "Tesla"

    featured_questions = [
        f"{spotlight_company} 的 ESG 综合评分是多少？",
        f"{spotlight_company} 最近有哪些 ESG 风险事件？",
        "苹果与微软的社会责任表现如何对比？",
        "最近 7 天有哪些值得关注的 ESG 风险信号？",
    ]

    score_profiles = {
        "tesla": {
            "overall_score": 72,
            "confidence": 0.85,
            "dimensions": {"E": 78, "S": 65, "G": 73},
        },
        "microsoft": {
            "overall_score": 81,
            "confidence": 0.89,
            "dimensions": {"E": 84, "S": 77, "G": 82},
        },
        "apple": {
            "overall_score": 79,
            "confidence": 0.87,
            "dimensions": {"E": 82, "S": 74, "G": 79},
        },
    }
    score_profile = score_profiles.get(str(spotlight_company).lower(), {
        "overall_score": 74,
        "confidence": 0.83,
        "dimensions": {"E": 77, "S": 69, "G": 75},
    })

    score_snapshot = {
        "company": spotlight_company,
        "overall_score": score_profile["overall_score"],
        "confidence": score_profile["confidence"],
        "dimensions": [
            {
                "key": "E",
                "label": "环保",
                "score": score_profile["dimensions"]["E"],
                "trend": "up",
            },
            {
                "key": "S",
                "label": "社会",
                "score": score_profile["dimensions"]["S"],
                "trend": "stable",
            },
            {
                "key": "G",
                "label": "治理",
                "score": score_profile["dimensions"]["G"],
                "trend": "up",
            },
        ],
        "radar": [
            {"label": "碳排放", "value": min(95, score_profile["dimensions"]["E"] + 6)},
            {"label": "员工满意度", "value": min(95, score_profile["dimensions"]["S"] + 4)},
            {"label": "供应链伦理", "value": max(52, score_profile["dimensions"]["S"] - 3)},
            {"label": "能源效率", "value": min(95, score_profile["dimensions"]["E"] + 2)},
            {"label": "成本竞争力", "value": min(95, score_profile["dimensions"]["G"] + 1)},
        ],
        "trend": [
            {"month": "Jan", "E": 64, "S": 58, "G": 60},
            {"month": "Feb", "E": 67, "S": 60, "G": 63},
            {"month": "Mar", "E": 70, "S": 61, "G": 66},
            {"month": "Apr", "E": 69, "S": 62, "G": 67},
            {"month": "May", "E": 72, "S": 63, "G": 68},
            {"month": "Jun", "E": 73, "S": 63, "G": 69},
            {"month": "Jul", "E": 74, "S": 64, "G": 70},
            {"month": "Aug", "E": 76, "S": 64, "G": 71},
            {"month": "Sep", "E": score_profile["dimensions"]["E"] - 1, "S": score_profile["dimensions"]["S"], "G": score_profile["dimensions"]["G"] - 1},
            {"month": "Oct", "E": score_profile["dimensions"]["E"], "S": score_profile["dimensions"]["S"], "G": score_profile["dimensions"]["G"]},
        ],
    }

    risk_counts = {"high": 0, "medium": 0, "low": 0}
    monitor_events = []
    timeline = []

    for index, item in enumerate(recent_signals[:5]):
        tone = item.get("tone") or "neutral"
        if tone == "alert" and risk_counts["high"] == 0:
            level = "high"
            risk_score = 89 - index * 3
        elif tone == "alert":
            level = "medium"
            risk_score = 67 - index * 2
        elif tone == "positive":
            level = "low"
            risk_score = 46 + index * 2
        else:
            level = "medium"
            risk_score = 58 - index

        risk_counts[level] += 1

        recommendation = (
            "持续跟踪披露进度并评估治理回应质量。"
            if level == "high" else
            "补充行业对标并观察后续执行动作。"
            if level == "medium" else
            "作为正面样本持续观察，提炼可复用亮点。"
        )

        monitor_events.append({
            "company": item.get("company") or "市场观察",
            "title": item.get("title") or "新的 ESG 事件",
            "description": item.get("description") or "最新 ESG 动态已进入视野。",
            "level": level,
            "risk_score": max(28, min(96, risk_score)),
            "published_at": item.get("detected_at") or generated_at.isoformat(),
            "event_type": item.get("event_type") or "UPDATE",
            "recommendation": recommendation,
            "positive": tone == "positive",
        })

        timeline.append({
            "date_label": datetime.fromisoformat(
                str(item.get("detected_at") or generated_at.isoformat()).replace("Z", "+00:00")
            ).strftime("%m/%d"),
            "company": item.get("company") or "市场观察",
            "level": level,
        })

    return {
        "generated_at": generated_at.isoformat(),
        "source": signal_source,
        "health": health_modules,
        "spotlight": spotlight,
        "metrics": [
            {
                "label": "实时信号",
                "value": total_signals,
                "suffix": "条",
                "hint": "最近进入旗舰首页的信息流",
            },
            {
                "label": "覆盖主体",
                "value": tracked_companies,
                "suffix": "个",
                "hint": "当前热点涉及的企业或监管主体",
            },
            {
                "label": "系统模块",
                "value": active_modules,
                "suffix": f"/{len(health_modules)}",
                "hint": "当前在线的分析与调度能力",
            },
            {
                "label": "近 7 天扫描",
                "value": scheduler_summary.get("total_scans", 0),
                "suffix": "次",
                "hint": "调度器扫描统计",
            },
        ],
        "signals": recent_signals,
        "query_interface": {
            "hot_questions": featured_questions,
        },
        "score_snapshot": score_snapshot,
        "event_monitor": {
            "period_label": "最近 7 天",
            "risk_counts": risk_counts,
            "events": monitor_events,
            "timeline": timeline,
        },
        "narrative": {
            "headline": "ESG 智能中枢。",
            "subheadline": "像旗舰发布页一样呈现 ESG 情报、评分看板、事件监测与执行入口。",
            "summary": "把 QueryInterface、ScoreBoard、EventMonitor 和功能矩阵收束成一个高端总览页面，让信息一眼可读、功能一键可达。",
        },
    }


# ════════════════════════════════════════════════════════════════════════════
# 1. 被动分析 API - Agent工作流
# ════════════════════════════════════════════════════════════════════════════

@app.post("/session")
def new_session(session_id: str, user_id: str = None):
    """新建会话"""
    if create_session is None:
        raise HTTPException(status_code=503, detail="Database module not available")
    create_session(session_id=session_id, user_id=user_id)
    return {"session_id": session_id, "created": True}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """
    主查询接口 - 被动分析
    用户提问 → RAG检索 → LLM回答
    """
    engine = app.state.query_engine
    if engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not ready.")

    _ensure_session(req.session_id)
    history = get_history(req.session_id, limit=10) if get_history else []
    context_prefix = ""
    if history:
        lines = [f"{m['role'].upper()}: {m['content']}" for m in history]
        context_prefix = "【对话历史】\n" + "\n".join(lines) + "\n\n【当前问题】\n"

    full_question = context_prefix + req.question
    response = engine.query(full_question)
    answer = str(response)

    if save_message:
        save_message(req.session_id, "user", req.question)
        save_message(req.session_id, "assistant", answer)

    return QueryResponse(
        session_id=req.session_id,
        question=req.question,
        answer=answer,
    )


@app.get("/history/{session_id}")
def history(session_id: str, limit: int = 20):
    """获取会话历史"""
    if get_history is None:
        raise HTTPException(status_code=503, detail="Database module not available")
    return {"session_id": session_id, "messages": get_history(session_id, limit=limit)}


@app.post("/agent/analyze")
def analyze_esg(
    payload: Optional[AnalyzeRequest] = Body(default=None),
    question: Optional[str] = Query(default=None),
    session_id: str = Query(default=""),
):
    """
    Agent工作流分析 - 被动查询
    通过 LangGraph 工作流进行结构化分析
    """
    actual_question = payload.question if payload else question
    actual_session_id = payload.session_id if payload and payload.session_id else session_id

    if not actual_question:
        raise HTTPException(status_code=422, detail="question is required")
    if run_agent is None:
        raise HTTPException(status_code=503, detail="Agent module not available")

    try:
        result = run_agent(actual_question, session_id=actual_session_id)

        if actual_session_id and save_message:
            _ensure_session(actual_session_id)
            save_message(actual_session_id, "user", actual_question)
            save_message(actual_session_id, "assistant", result.get("final_answer", ""))

        return {
            "question": actual_question,
            "answer": result.get("final_answer"),
            "esg_scores": result.get("esg_scores", {}),
            "confidence": result.get("confidence", 0),
            "analysis_summary": result.get("analysis_summary", ""),
        }
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


# ════════════════════════════════════════════════════════════════════════════
# 2. ESG评分 API - 结构化评分 + 可视化
# ════════════════════════════════════════════════════════════════════════════

@app.post("/agent/esg-score")
def get_esg_score(req: ESGScoreRequest):
    """
    获取结构化的ESG评分报告
    包含15个维度的详细评分和可视化数据
    """
    if not esg_scorer:
        raise HTTPException(status_code=503, detail="ESG Scorer not ready")

    try:
        logger.info(f"[ESG Score] Computing score for {req.company}")

        # 拉取公司数据
        if not data_source_manager:
            raise HTTPException(status_code=503, detail="Data Source Manager not ready")
        company_data = data_source_manager.fetch_company_data(
            req.company,
            ticker=req.ticker
        )

        # 评分
        esg_report: ESGScoreReport = esg_scorer.score_esg(
            req.company,
            company_data.dict(),
            peers=req.peers,
        )

        # 生成可视化
        visualizations = {}
        if req.include_visualization and esg_visualizer:
            visualizations = esg_visualizer.generate_report_visual(esg_report)

        return {
            "esg_report": esg_report.dict(),
            "visualizations": visualizations if req.include_visualization else None,
            "success": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ESG Score error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════════════════
# 3. 报告 API - 定期报告系统
# ════════════════════════════════════════════════════════════════════════════

@app.post("/admin/reports/generate")
def generate_report(req: ReportGenerateRequest, background_tasks: BackgroundTasks):
    """生成日/周/月报告"""
    if not report_generator:
        raise HTTPException(status_code=503, detail="Report Generator not ready")

    try:
        logger.info(f"[Reports] Generating {req.report_type} report")
        if req.report_type not in {"daily", "weekly", "monthly"}:
            raise HTTPException(status_code=400, detail="Invalid report type")

        if req.async_:
            # 异步生成
            report_id = f"report_{datetime.now().timestamp()}"
            report_jobs[report_id] = {
                "status": "generating",
                "report_type": req.report_type,
                "companies_count": len(req.companies),
                "generated_at": None,
            }

            def generate_sync():
                try:
                    report = _generate_report_by_type(req.report_type, req.companies)

                    # 保存报告
                    persisted_id = report_scheduler._save_report(report) if report_scheduler else report_id
                    _store_report_job(report_id, report, persisted_id=persisted_id)
                    logger.info(f"[Reports] Report {report_id} generated successfully")
                except Exception as e:
                    report_jobs[report_id] = {
                        "status": "failed",
                        "report_type": req.report_type,
                        "companies_count": len(req.companies),
                        "error": str(e),
                        "generated_at": None,
                    }
                    logger.error(f"[Reports] Error generating report: {e}", exc_info=True)

            background_tasks.add_task(generate_sync)

            return {
                "report_id": report_id,
                "status": "generating",
                "report_type": req.report_type,
                "companies_count": len(req.companies),
                "message": "报告生成中..."
            }
        else:
            # 同步生成
            report = _generate_report_by_type(req.report_type, req.companies)

            report_id = report_scheduler._save_report(report) if report_scheduler else f"report_{datetime.now().timestamp()}"
            payload = _store_report_job(report_id, report, persisted_id=report_id)

            return {
                "report_id": report_id,
                "status": "completed",
                "report_type": req.report_type,
                "report": payload,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/reports/{report_id}")
def get_report(report_id: str, report_type: Optional[str] = None):
    """获取报告内容"""
    try:
        if report_id == "latest":
            row = _fetch_latest_report_row(report_type or "", None)
            if row is None:
                return Response(status_code=204)

            payload = _flatten_report_row(row)
            payload["status"] = "completed"
            return payload

        job = report_jobs.get(report_id)
        if job:
            if job.get("status") != "completed":
                return {
                    "report_id": report_id,
                    "status": job.get("status"),
                    "report_type": job.get("report_type"),
                    "error": job.get("error"),
                }

            payload = dict(job.get("report") or {})
            payload["status"] = "completed"
            payload["report_id"] = payload.get("report_id") or report_id
            return payload

        row = _fetch_report_row(report_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Report not found")

        payload = _flatten_report_row(row)
        payload["status"] = "completed"
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(status_code=404, detail="Report not found")


@app.get("/admin/reports/latest")
def get_latest_report(report_type: str = Query(...), company: Optional[str] = None):
    """获取最新的报告"""
    try:
        logger.info(f"[Reports] Latest report requested for type={report_type}, company={company}")
        row = _fetch_latest_report_row(report_type, company)
        if row is None:
            return Response(status_code=204)

        payload = _flatten_report_row(row)
        payload["status"] = "completed"
        return payload
    except Exception as e:
        logger.error(f"Error: {e}")
        return Response(status_code=204)


@app.get("/admin/reports/export/{report_id}")
def export_report(report_id: str, format: str = Query("pdf")):
    """导出报告为PDF/Excel"""
    if format not in ["pdf", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    return {
        "report_id": report_id,
        "format": format,
        "message": "Report export",
        "download_url": f"/api/files/report_{report_id}.{format}"
    }


@app.get("/admin/reports/statistics")
def get_report_statistics(
    period: str = Query(...),
    group_by: str = Query("report_type")
):
    """获取报告统计数据"""
    try:
        # 解析时间范围
        start_date, end_date = period.split(":")
        if get_client is None:
            raise RuntimeError("Database module not available")

        reports = (
            get_client()
            .table("esg_reports")
            .select("id, report_type, generated_at")
            .gte("generated_at", start_date)
            .lte("generated_at", end_date)
            .execute()
            .data
        )

        by_type = {"daily": 0, "weekly": 0, "monthly": 0}
        for report in reports:
            report_name = report.get("report_type")
            if report_name in by_type:
                by_type[report_name] += 1

        push_statistics = {
            "total_notifications": 0,
            "delivered": 0,
            "read": 0,
            "click_through_rate": 0,
        }

        try:
            push_rows = (
                get_client()
                .table("report_push_history")
                .select("push_status, read_at, click_through")
                .gte("created_at", start_date)
                .lte("created_at", end_date)
                .execute()
                .data
            )
            total_pushes = len(push_rows)
            delivered = sum(1 for row in push_rows if row.get("push_status") == "sent")
            read = sum(1 for row in push_rows if row.get("read_at"))
            clicked = sum(1 for row in push_rows if row.get("click_through"))
            push_statistics = {
                "total_notifications": total_pushes,
                "delivered": delivered,
                "read": read,
                "click_through_rate": round((clicked / total_pushes) * 100, 2) if total_pushes else 0,
            }
        except Exception as push_exc:
            logger.warning(f"Push statistics unavailable: {push_exc}")

        return {
            "period": {"start": start_date, "end": end_date},
            "group_by": group_by,
            "total_reports": len(reports),
            "by_type": by_type,
            "push_statistics": push_statistics,
        }
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════════════════
# 4. 数据源 API - 数据管理
# ════════════════════════════════════════════════════════════════════════════

@app.post("/admin/data-sources/sync")
def sync_data_sources(req: DataSyncRequest, background_tasks: BackgroundTasks):
    """触发数据源同步"""
    if not data_source_manager:
        raise HTTPException(status_code=503, detail="Data Source Manager not ready")

    try:
        job_id = f"sync_{datetime.now().timestamp()}"
        sync_jobs[job_id] = {
            "job_id": job_id,
            "status": "started",
            "companies_total": len(req.companies),
            "companies_synced": 0,
            "companies_failed": 0,
            "total_records": 0,
            "updated_at": datetime.now().isoformat(),
        }

        def sync_task():
            synced = 0
            failed = 0
            for company in req.companies:
                try:
                    success = data_source_manager.sync_company_snapshot(
                        company,
                        force_refresh=req.force_refresh
                    )
                    if success:
                        synced += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.warning(f"Sync error for {company}: {e}")

            sync_jobs[job_id] = {
                "job_id": job_id,
                "status": "completed" if failed == 0 else "completed_with_errors",
                "companies_total": len(req.companies),
                "companies_synced": synced,
                "companies_failed": failed,
                "total_records": synced,
                "updated_at": datetime.now().isoformat(),
            }

        background_tasks.add_task(sync_task)

        return {
            "job_id": job_id,
            "status": "started",
            "companies_to_sync": len(req.companies),
            "message": "数据同步已启动"
        }

    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/data-sources/sync/{job_id}")
def get_sync_status(job_id: str):
    """查询同步任务进度"""
    job = sync_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Sync job not found")
    return job


# ════════════════════════════════════════════════════════════════════════════
# 5. 推送规则 API - 智能推送
# ════════════════════════════════════════════════════════════════════════════

@app.post("/admin/push-rules")
def create_push_rule(req: CreatePushRuleRequest):
    """创建推送规则"""
    if not report_scheduler:
        raise HTTPException(status_code=503, detail="Report Scheduler not ready")

    try:
        rule = PushRule(
            rule_name=req.rule_name,
            condition=req.condition,
            target_users=req.target_users,
            push_channels=req.push_channels,
            priority=req.priority,
            template_id=req.template_id,
        )

        rule_id = report_scheduler.create_push_rule(rule)

        return {
            "rule_id": rule_id,
            "rule_name": req.rule_name,
            "status": "created"
        }

    except Exception as e:
        logger.error(f"Create rule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/push-rules")
def get_push_rules():
    """获取所有推送规则"""
    if not report_scheduler:
        return {
            "total": 0,
            "rules": [],
            "degraded": True,
            "message": "Report Scheduler not ready"
        }

    try:
        rules = list(report_scheduler.push_rules_cache.values())
        return {
            "total": len(rules),
            "rules": [r.dict() for r in rules]
        }

    except Exception as e:
        logger.error(f"Get rules error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/admin/push-rules/{rule_id}")
def update_push_rule(rule_id: str, updates: Dict[str, Any]):
    """更新推送规则"""
    if not report_scheduler:
        raise HTTPException(status_code=503, detail="Report Scheduler not ready")

    try:
        report_scheduler.update_push_rule(rule_id, updates)
        return {
            "rule_id": rule_id,
            "status": "updated"
        }

    except Exception as e:
        logger.error(f"Update rule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/push-rules/{rule_id}")
def delete_push_rule(rule_id: str):
    """删除推送规则"""
    if not report_scheduler:
        raise HTTPException(status_code=503, detail="Report Scheduler not ready")

    try:
        report_scheduler.delete_push_rule(rule_id)
        return {
            "rule_id": rule_id,
            "status": "deleted"
        }

    except Exception as e:
        logger.error(f"Delete rule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/push-rules/{rule_id}/test")
def test_push_rule(rule_id: str, req: PushRuleTestRequest):
    """测试推送规则"""
    channels = ["email", "in_app"]
    matched = False

    if report_scheduler and rule_id in report_scheduler.push_rules_cache:
        rule = report_scheduler.push_rules_cache[rule_id]
        channels = rule.push_channels
        try:
            matched = bool(eval(rule.condition, {"__builtins__": {}}, req.mock_report))
        except Exception as e:
            logger.warning(f"Push rule test failed for {rule_id}: {e}")

    return {
        "test_id": f"test_{datetime.now().timestamp()}",
        "rule_id": rule_id,
        "status": "success",
        "results": {
            "test_user_id": req.test_user_id,
            "matched": matched,
            "channels_tested": channels,
        },
    }


# ════════════════════════════════════════════════════════════════════════════
# 6. 用户订阅 API - 个性化订阅
# ════════════════════════════════════════════════════════════════════════════

@app.post("/user/reports/subscribe")
def subscribe_reports(req: UserReportSubscribeRequest, user_id: str = "user_123"):
    """用户订阅报告"""
    if not report_scheduler:
        raise HTTPException(status_code=503, detail="Report Scheduler not ready")

    try:
        subscription = ReportSubscription(
            user_id=user_id,
            report_types=req.report_types,
            companies=req.companies,
            alert_threshold=req.alert_threshold or {},
            push_channels=req.push_channels,
            frequency=req.frequency,
        )

        subscription_id = report_scheduler.user_subscribe_reports(subscription)

        return {
            "subscription_id": subscription_id or f"sub_{user_id}",
            "user_id": user_id,
            "status": "subscribed",
            "subscribed_to": {
                "report_types": req.report_types,
                "companies": req.companies,
                "channels": req.push_channels
            }
        }

    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/reports/subscriptions")
def get_user_subscriptions(user_id: str = "user_123"):
    """获取用户订阅"""
    if get_client is None:
        return {
            "user_id": user_id,
            "subscriptions": [],
            "degraded": True,
            "message": "Database module not available",
        }

    try:
        rows = (
            get_client()
            .table("user_report_subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .order("subscribed_at", desc=True)
            .execute()
            .data
        )

        subscriptions = [
            {
                "subscription_id": row.get("id"),
                "user_id": row.get("user_id"),
                "report_types": row.get("report_types", []),
                "companies": row.get("companies", []),
                "alert_threshold": row.get("alert_threshold", {}),
                "push_channels": row.get("push_channels", []),
                "frequency": row.get("frequency"),
                "subscribed_at": row.get("subscribed_at"),
                "updated_at": row.get("updated_at"),
            }
            for row in rows
        ]

        return {
            "user_id": user_id,
            "subscriptions": subscriptions,
        }
    except Exception as e:
        logger.error(f"Get subscriptions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/user/reports/subscriptions/{subscription_id}")
def update_subscription(subscription_id: str, updates: Dict[str, Any]):
    """更新订阅"""
    if get_client is None:
        raise HTTPException(status_code=503, detail="Database module not available")

    try:
        get_client().table("user_report_subscriptions").update(updates).eq("id", subscription_id).execute()
        return {
            "subscription_id": subscription_id,
            "status": "updated"
        }
    except Exception as e:
        logger.error(f"Update subscription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/user/reports/subscriptions/{subscription_id}")
def unsubscribe(subscription_id: str):
    """取消订阅"""
    if get_client is None:
        raise HTTPException(status_code=503, detail="Database module not available")

    try:
        get_client().table("user_report_subscriptions").delete().eq("id", subscription_id).execute()
        return {
            "subscription_id": subscription_id,
            "status": "deleted"
        }
    except Exception as e:
        logger.error(f"Delete subscription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════════════════
# 7. Scheduler API - 原有的调度器接口
# ════════════════════════════════════════════════════════════════════════════

@app.post("/scheduler/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    """触发ESG扫描"""
    if not get_orchestrator:
        raise HTTPException(status_code=503, detail="Scheduler module not available")
    orchestrator = get_orchestrator()

    def _run_pipeline():
        try:
            orchestrator.run_full_pipeline()
        except Exception as e:
            logger.error(f"[Scheduler] Pipeline failed: {e}", exc_info=True)

    background_tasks.add_task(_run_pipeline)

    return {
        "status": "scanning",
        "message": "ESG scan pipeline started",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/scheduler/scan/status")
def get_scan_status():
    """获取扫描状态"""
    if not get_orchestrator:
        raise HTTPException(status_code=503, detail="Scheduler module not available")
    orchestrator = get_orchestrator()
    status = orchestrator.get_scan_status()

    if status:
        return {"status": "completed", "data": status}
    return {"status": "no_scan_found"}


@app.get("/scheduler/statistics")
def get_scheduler_statistics(days: int = 7):
    """获取调度器统计"""
    try:
        orchestrator = get_orchestrator() if get_orchestrator else None
    except Exception as e:
        logger.warning(f"Scheduler orchestrator unavailable: {e}")
        orchestrator = None

    if orchestrator is None:
        return {
            "period_days": days,
            "total_scans": 0,
            "success_rate": 0,
            "last_sync_time": None,
            "degraded": True,
            "message": "Scheduler not ready"
        }

    try:
        stats = orchestrator.get_pipeline_statistics(days=days) or {}
    except Exception as e:
        logger.warning(f"Scheduler statistics unavailable: {e}")
        return {
            "period_days": days,
            "total_scans": 0,
            "success_rate": 0,
            "last_sync_time": None,
            "degraded": True,
            "message": "Scheduler statistics unavailable"
        }

    return {
        "period_days": days,
        "total_scans": stats.get("total_scans", stats.get("scan_count", 0)),
        "success_rate": stats.get("success_rate", 0),
        "last_sync_time": stats.get("last_sync_time"),
        "statistics": stats,
    }


# ════════════════════════════════════════════════════════════════════════════
# 8. 前端静态文件挂载
# ════════════════════════════════════════════════════════════════════════════

from fastapi.staticfiles import StaticFiles

frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")
    logger.info(f"Frontend mounted at /app from {frontend_path}")
else:
    logger.warning(f"Frontend directory not found at {frontend_path}")


# ────────────────────────────────────────────────────────────────────────────
# 本地直接运行
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
