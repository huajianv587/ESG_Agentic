# router_agent.py — 路由 Agent
# 职责：判断用户问题属于哪种任务类型，决定后续走哪条处理链路
# 这是整个 graph 的第一个节点，输出结果影响所有后续节点的执行路径

from gateway.utils.llm_client import chat        # 统一 LLM 调用（带 fallback）
from gateway.utils.logger import get_logger
from gateway.agents.prompts import ROUTER_SYSTEM, ROUTER_USER

logger = get_logger(__name__)

# 合法的任务类型集合，用于校验 LLM 输出是否在预期范围内
VALID_TASK_TYPES = {"esg_analysis", "factual", "general"}


def run_router(state: dict) -> dict:
    """
    路由 Agent：判断用户问题的任务类型。

    输入 state 字段:
        question (str): 用户问题

    输出 state 字段:
        task_type (str): esg_analysis | factual | general
    """
    question = state["question"]
    logger.info(f"[Router] Classifying question: {question[:80]}...")

    # temperature=0.0 确保分类结果完全确定，不允许随机性
    # max_tokens=20 限制输出极短，防止模型多输出内容
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM},  #system：告诉模型“你是 ESG query classifier”
        {"role": "user",   "content": ROUTER_USER.format(question=question)},  #user：把真实问题填进去
    ] 

    try:
        raw = chat(messages, temperature=0.0, max_tokens=20).strip().lower()

        # 只取第一个词：防止模型输出「esg_analysis (因为...)」这种情况
        task_type = raw.split()[0] if raw.split() else "factual"

        # 校验输出是否合法，不合法则 fallback 到 factual（最安全的默认值）
        if task_type not in VALID_TASK_TYPES:
            logger.warning(f"[Router] Unknown task type '{task_type}', defaulting to 'factual'")
            task_type = "factual"

    except Exception as e:
        logger.error(f"[Router] Failed: {e}, defaulting to 'factual'")
        task_type = "factual"    # LLM 完全失败时的兜底值

    logger.info(f"[Router] → task_type: {task_type}")

    # {**state} 是 Python 字典解包：把原 state 所有字段复制过来，
    # 再加上/覆盖 task_type 字段，返回新的 state
    return {**state, "task_type": task_type}
