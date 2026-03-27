# tools.py — LangChain Tool 定义
# Tool 是 Agent 可以「调用」的外部能力，用 @tool 装饰器注册
# LangChain 会读取函数名、docstring、参数类型来自动生成工具描述
# Agent 通过工具描述决定「什么时候用哪个工具」

from langchain_core.tools import tool            # LangChain 的 tool 装饰器
from gateway.rag.rag_main import get_query_engine # 复用已有 RAG 引擎，不重复实现
from gateway.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def rag_search(query: str) -> str:
    """
    Search the ESG report knowledge base using the RAG engine.
    Use this tool to retrieve relevant passages from ESG reports.

    Args:
        query: The search query string

    Returns:
        Retrieved context passages as a string
    """
    # get_query_engine() 是单例，第一次调用会加载索引，之后直接复用
    try:
        engine = get_query_engine()
        response = engine.query(query)           # 调用 LlamaIndex 的检索+生成流程
        result = str(response)
        logger.info(f"[Tools] rag_search completed for query: {query[:60]}...")
        return result
    except Exception as e:
        logger.error(f"[Tools] rag_search failed: {e}")
        return f"Search failed: {e}"             # 失败时返回错误描述而不是抛异常，避免 Agent 崩溃


@tool
def calculate_esg_score(e_score: float, s_score: float, g_score: float) -> dict:
    """
    Calculate the weighted overall ESG score and risk level.
    Weights: Environmental 35%, Social 35%, Governance 30%.

    Args:
        e_score: Environmental score (0-100)
        s_score: Social score (0-100)
        g_score: Governance score (0-100)

    Returns:
        Dict with overall_score and risk_level
    """
    # 加权平均：E和S各占35%，G占30%
    overall = round(e_score * 0.35 + s_score * 0.35 + g_score * 0.30, 1)

    # 风险等级阈值：70分以上低风险，45-70中风险，45以下高风险
    if overall >= 70:
        risk_level = "low"
    elif overall >= 45:
        risk_level = "medium"
    else:
        risk_level = "high"

    return {"overall_score": overall, "risk_level": risk_level}


# 暴露给 agent 使用的工具列表，graph.py 或 agent 可直接导入 ALL_TOOLS
ALL_TOOLS = [rag_search, calculate_esg_score]
