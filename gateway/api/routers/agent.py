from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query, Request

from gateway.api.schemas import AnalyzeRequest, ESGScoreRequest, QueryRequest, QueryResponse
from gateway.app_runtime import runtime
from gateway.config import settings
from gateway.utils.llm_client import chat
from gateway.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _strip_code_fences(raw: str) -> str:
    text = (raw or "").strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if lines and lines[-1].strip() == "```":
        lines = lines[1:-1]
    else:
        lines = lines[1:]
    return "\n".join(lines).strip()


def _coerce_score(value: object, default: int = 65) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = default
    return max(0, min(100, score))


def _normalize_fast_demo_payload(raw: str, question: str) -> dict:
    cleaned = _strip_code_fences(raw)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = {
            "answer": cleaned or "Fast demo answer unavailable.",
            "analysis_summary": "Generated from cloud LLM without RAG grounding.",
            "confidence": 0.68,
            "esg_scores": {},
        }

    answer = str(parsed.get("answer") or cleaned or "Fast demo answer unavailable.").strip()
    summary = str(parsed.get("analysis_summary") or "").strip()
    confidence = parsed.get("confidence", 0.68)

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.68
    confidence = max(0.0, min(1.0, confidence))

    score_payload = parsed.get("esg_scores") or {}
    esg_scores = {
        "e_score": _coerce_score(score_payload.get("e_score"), 68),
        "s_score": _coerce_score(score_payload.get("s_score"), 64),
        "g_score": _coerce_score(score_payload.get("g_score"), 70),
    }
    esg_scores["overall_score"] = _coerce_score(
        score_payload.get("overall_score"),
        round((esg_scores["e_score"] + esg_scores["s_score"] + esg_scores["g_score"]) / 3),
    )

    if not summary:
        summary = f"Fast demo response generated for: {question[:80]}"

    return {
        "answer": answer.replace("\n", "<br>"),
        "analysis_summary": summary,
        "confidence": confidence,
        "esg_scores": esg_scores,
    }


def _run_fast_demo_analysis(question: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an ESG demo copilot. Return valid JSON only. "
                "Use the same language as the user. "
                "Provide a concise presentation-friendly response for a live demo. "
                "When precise retrieved evidence is unavailable, frame the output as a fast estimate "
                "based on general ESG knowledge and common public information. "
                "Return this exact JSON schema: "
                "{\"answer\": string, \"analysis_summary\": string, "
                "\"confidence\": number, "
                "\"esg_scores\": {\"e_score\": number, \"s_score\": number, "
                "\"g_score\": number, \"overall_score\": number}}. "
                "Keep confidence between 0.55 and 0.85."
            ),
        },
        {
            "role": "user",
            "content": (
                "Question:\n"
                f"{question}\n\n"
                "Make the answer easy to present in a demo. "
                "Use short paragraphs or bullet-style lines."
            ),
        },
    ]
    raw = chat(messages, temperature=0.2, max_tokens=900)
    return _normalize_fast_demo_payload(raw, question)


@router.post("/session")
def new_session(session_id: str, user_id: str | None = None):
    if runtime.create_session is None:
        raise HTTPException(status_code=503, detail="Database module not available")
    runtime.create_session(session_id=session_id, user_id=user_id)
    return {"session_id": session_id, "created": True}


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, request: Request):
    engine = request.app.state.query_engine
    if engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not ready.")

    runtime.ensure_session(req.session_id)
    history = runtime.get_history(req.session_id, limit=10) if runtime.get_history else []
    context_prefix = ""
    if history:
        lines = [f"{message['role'].upper()}: {message['content']}" for message in history]
        context_prefix = "【对话历史】\n" + "\n".join(lines) + "\n\n【当前问题】\n"

    full_question = context_prefix + req.question
    response = engine.query(full_question)
    answer = str(response)

    if runtime.save_message:
        runtime.save_message(req.session_id, "user", req.question)
        runtime.save_message(req.session_id, "assistant", answer)

    return QueryResponse(
        session_id=req.session_id,
        question=req.question,
        answer=answer,
    )


@router.get("/history/{session_id}")
def history(session_id: str, limit: int = 20):
    if runtime.get_history is None:
        raise HTTPException(status_code=503, detail="Database module not available")
    return {"session_id": session_id, "messages": runtime.get_history(session_id, limit=limit)}


@router.post("/agent/analyze")
def analyze_esg(
    payload: Optional[AnalyzeRequest] = Body(default=None),
    question: Optional[str] = Query(default=None),
    session_id: str = Query(default=""),
):
    actual_question = payload.question if payload else question
    actual_session_id = payload.session_id if payload and payload.session_id else session_id

    if not actual_question:
        raise HTTPException(status_code=422, detail="question is required")
    if runtime.run_agent is None:
        raise HTTPException(status_code=503, detail="Agent module not available")

    try:
        if settings.DEMO_FAST_MODE:
            logger.info("[Analyze] DEMO_FAST_MODE enabled, using direct cloud analysis path.")
            result = _run_fast_demo_analysis(actual_question)
            final_answer = result.get("answer", "")
        else:
            result = runtime.run_agent(actual_question, session_id=actual_session_id)
            final_answer = result.get("final_answer", "")

        if actual_session_id and runtime.save_message:
            runtime.ensure_session(actual_session_id)
            runtime.save_message(actual_session_id, "user", actual_question)
            runtime.save_message(actual_session_id, "assistant", final_answer)

        return {
            "question": actual_question,
            "answer": final_answer,
            "esg_scores": result.get("esg_scores", {}),
            "confidence": result.get("confidence", 0),
            "analysis_summary": result.get("analysis_summary", ""),
        }
    except Exception as exc:
        logger.error(f"Analysis error: {exc}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")


@router.post("/agent/esg-score")
def get_esg_score(req: ESGScoreRequest):
    if not runtime.esg_scorer:
        raise HTTPException(status_code=503, detail="ESG Scorer not ready")

    try:
        logger.info(f"[ESG Score] Computing score for {req.company}")

        if not runtime.data_source_manager:
            raise HTTPException(status_code=503, detail="Data Source Manager not ready")

        company_data = runtime.data_source_manager.fetch_company_data(
            req.company,
            ticker=req.ticker,
        )

        company_payload = runtime.serialize_model(company_data) or {}
        esg_report = runtime.esg_scorer.score_esg(
            req.company,
            company_payload,
            peers=req.peers,
        )

        visualizations = {}
        if req.include_visualization and runtime.esg_visualizer:
            visualizations = runtime.esg_visualizer.generate_report_visual(esg_report)

        return {
            "esg_report": runtime.serialize_model(esg_report),
            "visualizations": visualizations if req.include_visualization else None,
            "success": True,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"ESG Score error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
