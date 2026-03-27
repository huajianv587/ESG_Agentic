# verifier_agent.py — 验证 Agent
# 职责：检查 analyst 的输出是否有幻觉，评估置信度，决定是否需要重试
# 幻觉(hallucination) = LLM 编造了上下文中根本不存在的数字或事实
# 这是 RAG 系统的质量保障层，直接影响用户对结果的信任度

import json
from gateway.utils.llm_client import chat
from gateway.utils.logger import get_logger
from gateway.agents.prompts import VERIFIER_SYSTEM, VERIFIER_USER

logger = get_logger(__name__)

CONFIDENCE_THRESHOLD = 0.6   # 低于此值在日志中标记为低可信度（供监控告警用）
MAX_RETRY_COUNT = 1           # graph 中最多允许打回 analyst 重试一次，防止死循环


def _parse_verifier_json(raw: str) -> dict | None:
    """解析 verifier 的 JSON 输出，容错处理 markdown 代码块。"""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def run_verifier(state: dict) -> dict:
    """
    验证 Agent：检查答案是否有幻觉，评估置信度。

    输入 state 字段:
        context      (str):  检索上下文（事实核查的依据）
        raw_answer   (str):  retriever 的原始答案
        esg_scores   (dict): analyst 的结构化评分（可为空）
        retry_count  (int):  已重试次数（防止无限循环）

    输出 state 字段:
        final_answer (str):   验证后的最终答案（可能被修正）
        confidence   (float): 置信度 0.0-1.0
        is_grounded  (bool):  答案是否有据可查
        needs_retry  (bool):  是否需要 analyst 重试（graph 根据此字段决定路由）
    """
    context     = state.get("context", "")
    esg_scores  = state.get("esg_scores", {})
    raw_answer  = state.get("raw_answer", "")
    retry_count = state.get("retry_count", 0)   # 记录已重试次数，达到上限则强制结束

    # 要验证的内容：优先验证 analyst 的结构化评分，没有则验证 raw_answer
    # json.dumps 把 dict 转成字符串，便于传给 LLM
    answer_to_verify = (
        json.dumps(esg_scores, ensure_ascii=False) if esg_scores else raw_answer
    )

    # 没有 context 时无法进行事实核查，直接放行
    if not context:
        logger.warning("[Verifier] No context to verify against, passing through.")
        return {
            **state,
            "final_answer": raw_answer,
            "confidence":   0.5,     # 无法核查时给中性置信度
            "is_grounded":  False,
            "needs_retry":  False,
        }

    messages = [
        {"role": "system", "content": VERIFIER_SYSTEM},
        {"role": "user",   "content": VERIFIER_USER.format(
            context=context, answer=answer_to_verify
        )},
    ]

    result = None
    try:
        raw = chat(messages, temperature=0.0, max_tokens=512)
        result = _parse_verifier_json(raw)
    except Exception as e:
        logger.error(f"[Verifier] LLM call failed: {e}")

    # JSON 解析失败时的 fallback：直接使用原始答案，不阻塞流程
    if not result:
        logger.warning("[Verifier] JSON parse failed, using raw_answer as fallback.")
        return {
            **state,
            "final_answer": raw_answer,
            "confidence":   0.5,
            "is_grounded":  False,
            "needs_retry":  False,
        }

    confidence  = float(result.get("confidence", 0.5))
    is_grounded = bool(result.get("is_grounded", False))
    issues      = result.get("issues", [])

    # needs_retry 需要同时满足两个条件：
    # 1. verifier 认为需要重试（答案有问题）
    # 2. 还没有超过最大重试次数（防止死循环）
    needs_retry = bool(result.get("needs_retry", False)) and retry_count < MAX_RETRY_COUNT

    # verified_answer 是 verifier 修正后的答案，如果没问题就和原答案一样
    final_answer = result.get("verified_answer", raw_answer)

    if issues:
        logger.warning(f"[Verifier] Issues found: {issues}")
    if confidence < CONFIDENCE_THRESHOLD:
        logger.warning(f"[Verifier] Low confidence: {confidence:.2f}")

    logger.info(f"[Verifier] confidence={confidence:.2f}, grounded={is_grounded}, retry={needs_retry}")

    return {
        **state,
        "final_answer": final_answer,
        "confidence":   confidence,
        "is_grounded":  is_grounded,
        "needs_retry":  needs_retry,
        "retry_count":  retry_count + 1,   # 每次经过 verifier 计数+1
    }
