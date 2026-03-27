# analyst_agent.py — 分析 Agent
# 职责：从检索到的 ESG 报告段落中，结构化抽取 E/S/G 12个指标并打分
# 这是整个项目的核心差异化功能：把非结构化的报告文本 → 结构化评分数据

import json
from gateway.utils.llm_client import chat
from gateway.utils.logger import get_logger
from gateway.agents.prompts import ANALYST_SYSTEM, ANALYST_USER

logger = get_logger(__name__)

MAX_RETRIES = 2   # JSON 解析失败时的最大重试次数（LLM 有时会输出格式不对的内容）


def _parse_esg_json(raw: str) -> dict | None:
    """
    从 LLM 输出中提取并解析 JSON。
    容错处理：LLM 有时会在 JSON 外面套 ```json ... ``` 代码块，需要去掉。
    解析失败返回 None，由调用方决定是否重试。
    """
    text = raw.strip()

    # 去掉 markdown 代码块包裹：```json\n...\n```
    if text.startswith("```"):
        lines = text.split("\n")
        # 如果最后一行是 ``` 则去掉首尾各一行，否则只去掉第一行
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        return json.loads(text)    # 标准 JSON 解析
    except json.JSONDecodeError:
        return None                # 解析失败，返回 None 触发重试


def run_analyst(state: dict) -> dict:
    """
    分析 Agent：结构化抽取 E/S/G 指标并打分。

    输入 state 字段:
        question (str): 用户问题（用于告知分析对象）
        context  (str): 检索到的 ESG 报告段落

    输出 state 字段:
        esg_scores       (dict): 结构化 E/S/G 评分，包含3个维度×4个子指标
        analysis_summary (str):  2-3句话的执行摘要
    """
    question = state["question"]
    context  = state.get("context", "")

    # 没有 context 时跳过分析（缓存命中或检索失败的情况）
    if not context:
        logger.warning("[Analyst] No context available, skipping analysis.")
        return {**state, "esg_scores": {}, "analysis_summary": "No context available for analysis."}

    messages = [
        {"role": "system", "content": ANALYST_SYSTEM},
        {"role": "user",   "content": ANALYST_USER.format(question=question, context=context)},
    ]

    esg_scores = None

    # 重试循环：JSON 解析失败时最多重试 MAX_RETRIES 次
    # +2 原因：range(1, MAX_RETRIES + 2) = range(1, 4) = [1, 2, 3]，共3次机会
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            # temperature=0.1 接近确定性，但保留少量灵活性应对不同格式的报告
            raw = chat(messages, temperature=0.1, max_tokens=1500)
            esg_scores = _parse_esg_json(raw)
            if esg_scores:
                break    # 解析成功，退出循环
            logger.warning(f"[Analyst] JSON parse failed (attempt {attempt}), retrying...")
        except Exception as e:
            logger.error(f"[Analyst] LLM call failed (attempt {attempt}): {e}")

    if not esg_scores:
        logger.error("[Analyst] All attempts failed, returning empty scores.")
        esg_scores = {}    # 全部失败时返回空 dict，verifier 会处理这种情况

    # 从结果中提取摘要和关键指标用于日志
    summary = esg_scores.get("summary", "Analysis unavailable.")
    overall = esg_scores.get("overall_score", "N/A")
    risk    = esg_scores.get("risk_level", "unknown")

    logger.info(f"[Analyst] overall_score={overall}, risk_level={risk}")
    return {**state, "esg_scores": esg_scores, "analysis_summary": summary}
