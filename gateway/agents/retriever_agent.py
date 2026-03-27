# retriever_agent.py — 检索 Agent
# 职责：query 改写 → 调用 RAG 引擎检索 → 返回上下文和初步答案
# 是 analyst 和 verifier 的数据来源，context 质量直接影响后续分析质量

from gateway.utils.llm_client import chat
from gateway.utils.logger import get_logger
from gateway.utils.cache import get_cache, set_cache   # 缓存：同一问题不重复调用 RAG
from gateway.rag.rag_main import get_query_engine       # 复用已有 RAG 引擎
from gateway.agents.prompts import (
    RETRIEVER_REWRITE_SYSTEM,
    RETRIEVER_REWRITE_USER,
)

logger = get_logger(__name__)


def _rewrite_query(question: str) -> str:
    """
    用 LLM 把用户口语化问题改写成更适合向量检索的专业表达。
    改写失败时直接返回原始问题（不影响主流程）。
    """
    messages = [
        {"role": "system", "content": RETRIEVER_REWRITE_SYSTEM},
        {"role": "user",   "content": RETRIEVER_REWRITE_USER.format(question=question)},
    ]
    try:
        rewritten = chat(messages, temperature=0.0, max_tokens=128).strip()
        logger.info(f"[Retriever] Rewritten query: {rewritten[:80]}...")
        return rewritten
    except Exception as e:
        logger.warning(f"[Retriever] Query rewrite failed: {e}, using original.")
        return question    # 失败降级：用原始问题继续，不中断流程


def run_retriever(state: dict) -> dict:
    """
    检索 Agent：query 改写 → RAG 检索 → 返回上下文和答案。

    输入 state 字段:
        question (str): 用户问题

    输出 state 字段:
        rewritten_query (str): 改写后的检索 query
        context (str):         检索到的原始段落（供 analyst/verifier 引用）
        raw_answer (str):      RAG 直接生成的初步答案
    """
    question = state["question"]

    # ── 缓存检查：命中则跳过整个检索流程 ─────────────────────────────────
    cached = get_cache(question)
    if cached:
        logger.info("[Retriever] Cache hit, skipping retrieval.")
        # 缓存命中时 context 为空，verifier 会直接放行
        return {**state, "rewritten_query": question, "context": "", "raw_answer": cached}

    # ── Query 改写 ────────────────────────────────────────────────────────
    rewritten_query = _rewrite_query(question)

    # ── RAG 检索 ──────────────────────────────────────────────────────────
    try:
        engine = get_query_engine()
        response = engine.query(rewritten_query)
        raw_answer = str(response)

        # source_nodes 是 LlamaIndex 返回的检索到的原始段落节点
        # 把它们拼接成 context 字符串，供 analyst 提取指标时引用
        source_nodes = getattr(response, "source_nodes", [])
        if source_nodes:
            context_parts = [node.get_content() for node in source_nodes]
            context = "\n\n---\n\n".join(context_parts)  # 用分隔符区分不同段落
        else:
            context = raw_answer    # 没有 source_nodes 时用答案本身作为 context

        # 写入缓存，下次同样问题直接命中
        set_cache(question, raw_answer)
        logger.info(f"[Retriever] Retrieved {len(source_nodes)} source nodes.")

    except Exception as e:
        logger.error(f"[Retriever] RAG query failed: {e}")
        raw_answer = f"Retrieval failed: {e}"
        context = ""

    return {**state, "rewritten_query": rewritten_query, "context": context, "raw_answer": raw_answer}
